import { useChatStore, TraceStep } from '@/store/useChatStore';
import { useSovereigntyStore } from '@/store/useSovereigntyStore';
import { useModelStore } from '@/store/useModelStore';

/**
 * WebSocketClientManager handles real-time dual-channel streaming:
 * Channel 1: ws://<host>:8000/api/chat/stream (Agent Thought -> Action -> Token Stream)
 * Channel 2: ws://<host>:8000/api/audit-stream (1000ms 3-Tier Traffic & VRAM Telemetry)
 *
 * Implements resilient dynamic host resolution (window.location.hostname)
 * with graceful offline mock-fallback when backend is unavailable.
 */
class WebSocketClientManager {
  private chatWs: WebSocket | null = null;
  private auditWs: WebSocket | null = null;
  private auditReconnectTimer: NodeJS.Timeout | null = null;
  private isFallbackMode: boolean = false;
  private wsGeneration: number = 0;

  public getWsHost(): string {
    if (typeof window !== 'undefined') {
      const hostname = window.location.hostname;
      // Sanitize hostname to prevent injection - only allow localhost, valid IPs, or local names
      if (/^[a-zA-Z0-9.-]+$/.test(hostname)) {
        return hostname;
      }
    }
    return '127.0.0.1';
  }

  /**
   * Returns the backend WebSocket base URL.
   * WebSocket always connects directly to port 8000 (FastAPI backend),
   * regardless of whether the frontend is running on port 3000 (dev) or 8000 (prod).
   */
  public getWsBaseUrl(): string {
    const host = this.getWsHost();
    return `ws://${host}:8000`;
  }

  /**
   * Connects to the continuous 1000ms telemetry stream (/api/audit-stream)
   */
  public connectAuditStream() {
    if (typeof window === 'undefined') return;

    const wsUrl = `${this.getWsBaseUrl()}/api/audit-stream`;

    try {
      this.auditWs = new WebSocket(wsUrl);

      this.auditWs.onopen = () => {
        this.isFallbackMode = false;
      };

      this.auditWs.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.sovereignty) {
            useSovereigntyStore.getState().updateMetrics({
              external_packets: payload.sovereignty.external_packets || 0,
              localhost_packets: payload.sovereignty.localhost_packets || 0,
              lan_hotspot_packets: payload.sovereignty.lan_hotspot_packets || 0,
              daemon_heartbeat_hz: 1.0,
            });
            if (payload.sovereignty.sockets) {
              useSovereigntyStore.getState().setSockets(payload.sovereignty.sockets);
            }
          }
          if (payload.vram) {
            useModelStore.getState().updateVRAM(payload.vram);
          }
        } catch (err) {
          // Ignore malformed frames safely
        }
      };

      this.auditWs.onerror = () => {
        this.activateAuditFallback();
      };

      this.auditWs.onclose = () => {
        this.activateAuditFallback();
        // Retry connection in 3 seconds
        if (this.auditReconnectTimer) clearTimeout(this.auditReconnectTimer);
        this.auditReconnectTimer = setTimeout(() => this.connectAuditStream(), 3000);
      };
    } catch (err) {
      this.activateAuditFallback();
    }
  }

  private activateAuditFallback() {
    this.isFallbackMode = true;
    // Reset sovereignty metrics to zero when backend is unavailable
    useSovereigntyStore.getState().updateMetrics({ external_packets: 0 });
  }

  /**
   * Submits a prompt, optional attachments, and role over ws://<host>:8000/api/chat/stream
   */
  public sendChatTask(
    prompt: string,
    attachments: any[] = [],
    role?: string,
    force_refresh: boolean = false,
    session_id?: string,
    history?: { role: string; content: string }[]
  ) {
    const wsUrl = `${this.getWsBaseUrl()}/api/chat/stream`;

    const chatStore = useChatStore.getState();
    chatStore.setStreaming(true);
    chatStore.clearTrace();
    const activeSessionId = session_id || chatStore.activeSessionId;

    // Capture up to 3 prior messages for conversational memory context (excluding current prompt if already added)
    const allMsgs = chatStore.messages.filter(m => m.content && m.content.trim().length > 0);
    const priorMsgs = (allMsgs.length > 0 && allMsgs[allMsgs.length - 1].content === prompt && allMsgs[allMsgs.length - 1].role === 'user')
      ? allMsgs.slice(0, -1)
      : allMsgs;

    const chatHistory = history ?? (
      priorMsgs
        .slice(-3)
        .map(m => ({
          role: m.role,
          content: m.content
        }))
    );

    let wsConnected = false;
    const currentGen = ++this.wsGeneration;

    try {
      if (this.chatWs) {
        this.chatWs.close();
      }

      this.chatWs = new WebSocket(wsUrl);

      this.chatWs.onopen = () => {
        wsConnected = true;
        this.chatWs?.send(JSON.stringify({
          prompt,
          attachments,
          role,
          force_refresh,
          session_id: activeSessionId,
          history: chatHistory
        }));
      };

      this.chatWs.onmessage = (event) => {
        try {
          const frame = JSON.parse(event.data);
          chatStore.handleStreamEvent(frame);
        } catch (e) {
          // Safe JSON parsing
        }
      };

      this.chatWs.onerror = () => {
        if (!wsConnected) {
          chatStore.setStreaming(false);
          chatStore.addMessage({
            id: `err-${Date.now()}`,
            role: 'agent',
            content: `⚠️ [BACKEND UNREACHABLE]\n\nFailed to establish WebSocket connection to ws://${this.getWsHost()}:8000/api/chat/stream.\nPlease ensure the Sovereign Backend server is active.`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            model_id: 'System Error',
          });
        }
      };

      this.chatWs.onclose = () => {
        if (currentGen === this.wsGeneration) {
          chatStore.setStreaming(false);
        }
      };
    } catch (err) {
      chatStore.setStreaming(false);
      chatStore.addMessage({
        id: `err-${Date.now()}`,
        role: 'agent',
        content: `⚠️ [BACKEND UNREACHABLE]\n\nCould not initialize connection to ws://${this.getWsHost()}:8000.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model_id: 'System Error',
      });
    }
  }
}

export const socketManager = new WebSocketClientManager();
