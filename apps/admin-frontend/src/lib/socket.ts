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
  private chatGeneration: number = 0;

  public getWsHost(): string {
    return getApiHost();
  }

  /**
   * Builds the `?token=` query string the backend requires on every WebSocket.
   * Unauthenticated sockets are closed with 4401 by the backend.
   */
  private authQuery(): string {
    const token = useAuthStore.getState().token;
    return token ? `?token=${encodeURIComponent(token)}` : '?token=';
  }

  /**
   * Aborts the in-flight generation for real: invalidates the current socket's
   * callbacks and closes it, which makes the backend's send raise and stops the
   * /api/chat/stream pipeline.
   */
  public abortChatTask(): boolean {
    const hadActiveTask = this.chatWs !== null && this.chatWs.readyState === WebSocket.OPEN;
    this.chatGeneration += 1;
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
   * Connects to the continuous 1000ms telemetry stream (/api/audit-stream)
   */
  public connectAuditStream() {
    if (typeof window === 'undefined') return;

    // Idempotent: this is called from a mount effect on every admin page, and
    // the previous socket was never closed. Each navigation added another live
    // socket, and because every one of them scheduled its own reconnect on
    // close, the count grew monotonically. Close any existing socket (and
    // cancel its pending reconnect) before opening a new one.
    this.disconnectAuditStream();

    const wsUrl = `${getWsBase()}/api/audit-stream${this.authQuery()}`;

    try {
      const socket = new WebSocket(wsUrl);
      this.auditWs = socket;

      socket.onopen = () => {
        this.isFallbackMode = false;
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.sovereignty) {
            useSovereigntyStore.getState().updateMetrics({
              // Preserve null: a null packet count means "not measured", and
              // coercing it to 0 would assert that zero traffic was observed.
              external_packets: payload.sovereignty.external_packets ?? null,
              localhost_packets: payload.sovereignty.localhost_packets ?? null,
              lan_hotspot_packets: payload.sovereignty.lan_hotspot_packets ?? null,
              localhost_sockets: payload.sovereignty.localhost_connections || 0,
              lan_hotspot_sockets: payload.sovereignty.lan_hotspot_connections || 0,
              external_sockets: payload.sovereignty.external_internet_connections || 0,
              verdict: payload.sovereignty.verdict || 'UNKNOWN - no verdict reported',
              daemon_heartbeat_hz: payload.sovereignty.daemon_heartbeat_hz || 1.0,
            });
            if (payload.sovereignty.sockets) {
              useSovereigntyStore.getState().setSockets(payload.sovereignty.sockets);
            }
            if (payload.sovereignty.audit_logs && payload.sovereignty.audit_logs.length > 0) {
              useSovereigntyStore.getState().setAuditLogs(payload.sovereignty.audit_logs);
            }
          }
          if (payload.vram) {
            useModelStore.getState().updateVRAM(payload.vram);
          }
        } catch (err) {
          // Ignore malformed frames safely
        }
      };

      socket.onerror = () => {
        this.activateAuditFallback();
      };

      socket.onclose = () => {
        this.activateAuditFallback();
        // Only auto-reconnect if this socket is still the current one; a socket
        // we deliberately closed in disconnectAuditStream() must not resurrect
        // itself.
        if (this.auditWs !== socket) return;
        if (this.auditReconnectTimer) clearTimeout(this.auditReconnectTimer);
        this.auditReconnectTimer = setTimeout(() => this.connectAuditStream(), 3000);
      };
    } catch (err) {
      this.activateAuditFallback();
    }
  }

  /**
   * Closes the audit telemetry socket and cancels any pending reconnect.
   * Previously no such method existed, so a page unmount left the socket (and
   * its reconnect timer) running.
   */
  public disconnectAuditStream() {
    if (this.auditReconnectTimer) {
      clearTimeout(this.auditReconnectTimer);
      this.auditReconnectTimer = null;
    }
    const socket = this.auditWs;
    this.auditWs = null;
    if (socket) {
      // Detach handlers first so closing does not trigger a reconnect.
      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      socket.onclose = null;
      try {
        if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
          socket.close();
        }
      } catch (err) {
        // Closing an already-dead socket is not an error worth surfacing.
      }
    }
  }

  private activateAuditFallback() {
    this.isFallbackMode = true;
    // The stream is unavailable, so telemetry is unknown - it is NOT zero.
    const currentSov = useSovereigntyStore.getState().metrics;
    if (currentSov.external_packets !== null) {
      useSovereigntyStore.getState().updateMetrics({ external_packets: null });
    }
  }

  /**
   * Submits a prompt and optional attachments over ws://<host>:8000/api/chat/stream
   */
  public sendChatTask(prompt: string, attachments: any[] = [], role?: string) {
    const wsUrl = `${getWsBase()}/api/chat/stream${this.authQuery()}`;

    const chatStore = useChatStore.getState();
    chatStore.setStreaming(true);

    let wsConnected = false;
    const currentGeneration = ++this.chatGeneration;

    try {
      if (this.chatWs) {
        this.chatWs.close();
      }

      const socket = new WebSocket(wsUrl);
      this.chatWs = socket;

      socket.onopen = () => {
        wsConnected = true;
        // A newer task superseded this one before the socket opened.
        if (currentGeneration !== this.chatGeneration) {
          try {
            socket.close();
          } catch {
            // already closing
          }
          return;
        }
        socket.send(JSON.stringify({ prompt, attachments, role }));
      };

      socket.onmessage = (event) => {
        // Drop frames from a task that was aborted or superseded.
        if (currentGeneration !== this.chatGeneration) return;
        try {
          const frame = JSON.parse(event.data);
          chatStore.handleStreamEvent(frame);
        } catch (e) {
          // Safe JSON parsing
        }
      };

      socket.onerror = () => {
        if (currentGeneration !== this.chatGeneration) return;
        if (!wsConnected) {
          chatStore.setStreaming(false);
          chatStore.addMessage({
            id: `err-${Date.now()}`,
            role: 'agent',
            content: 'Backend unavailable. Please ensure the Sovereign Backend server is active.',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            model_id: 'System Error',
          });
        }
      };

      socket.onclose = () => {
        if (currentGeneration !== this.chatGeneration) return;
        chatStore.setStreaming(false);
      };
    } catch (err) {
      chatStore.setStreaming(false);
      chatStore.addMessage({
        id: `err-${Date.now()}`,
        role: 'agent',
        content: 'Could not initialize WebSocket connection to backend.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model_id: 'System Error',
      });
    }
  }
}

export const socketManager = new WebSocketClientManager();
