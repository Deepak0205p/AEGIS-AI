import { useChatStore, TraceStep } from '@/store/useChatStore';
import { useSovereigntyStore } from '@/store/useSovereigntyStore';
import { useModelStore } from '@/store/useModelStore';
import { useAuthStore } from '@/store/useAuthStore';
import { getApiHost, getWsBase } from '@/lib/apiBase';

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
    return getApiHost();
  }

  /**
   * Returns the backend WebSocket base URL.
   * WebSocket always connects directly to port 8000 (FastAPI backend),
   * regardless of whether the frontend is running on port 3000 (dev) or 8000 (prod).
   */
  public getWsBaseUrl(): string {
    return getWsBase();
  }

  /**
   * Builds the `?token=` query string the backend requires on every WebSocket.
   * The backend closes unauthenticated sockets with 4401, so a missing token
   * is an honest rejection rather than a silent anonymous stream.
   */
  private authQuery(): string {
    const token = useAuthStore.getState().token;
    return token ? `?token=${encodeURIComponent(token)}` : '?token=';
  }

  /**
   * Connects to the continuous 1000ms telemetry stream (/api/audit-stream)
   */
  public connectAuditStream() {
    if (typeof window === 'undefined') return;

    const wsUrl = `${this.getWsBaseUrl()}/api/audit-stream${this.authQuery()}`;

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
              // Null is preserved: it means packet counting is unavailable,
              // not that zero packets were seen.
              external_packets: payload.sovereignty.external_packets ?? null,
              localhost_packets: payload.sovereignty.localhost_packets ?? null,
              lan_hotspot_packets: payload.sovereignty.lan_hotspot_packets ?? null,
              localhost_sockets: payload.sovereignty.localhost_connections || 0,
              lan_hotspot_sockets: payload.sovereignty.lan_hotspot_connections || 0,
              external_sockets: payload.sovereignty.external_internet_connections || 0,
              verdict: payload.sovereignty.verdict || 'UNKNOWN - no verdict reported',
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
    // Telemetry is unavailable, so it is unknown - not zero.
    useSovereigntyStore.getState().updateMetrics({
      external_packets: null,
      localhost_packets: null,
      lan_hotspot_packets: null,
      verdict: 'UNAVAILABLE - audit stream disconnected',
    });
  }

  /**
   * Aborts the in-flight generation for real.
   *
   * Bumping the generation invalidates every callback captured by the active
   * socket, and closing the socket makes the backend's `send_json` raise, which
   * unwinds the `async for` in the /api/chat/stream handler and stops the
   * pipeline instead of leaving it running in the background.
   */
  public abortChatTask(): boolean {
    const hadActiveTask = this.chatWs !== null && this.chatWs.readyState === WebSocket.OPEN;
    this.wsGeneration += 1; // ignore any late frames from the old socket
    if (this.chatWs) {
      try {
        this.chatWs.close();
      } catch {
        // already closing
      }
      this.chatWs = null;
    }
    return hadActiveTask;
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
    history?: { role: string; content: string }[],
    agent_id?: string
  ) {
    const wsUrl = `${this.getWsBaseUrl()}/api/chat/stream${this.authQuery()}`;

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
          history: chatHistory,
          agent_id: agent_id
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
