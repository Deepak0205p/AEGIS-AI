import { create } from 'zustand';

export interface TraceStep {
  id: string;
  step_number: number;
  type: 'thought' | 'action' | 'observation' | 'correction';
  content: string;
  tool_name?: string;
  tool_input?: string;
  tool_output?: string;
  duration_ms?: number;
  ram_mb?: number;
  timestamp: string;
}

export interface ChatAttachment {
  name: string;
  base64: string;
  type?: string;
  size?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: string;
  model_id?: string;
  routed_by?: 'stage1_regex' | 'stage2_semantic' | 'manual';
  confidence?: number;
  trace_steps?: TraceStep[];
  deliverable_ids?: string[];
  attachments?: ChatAttachment[];
}

export interface ConversationSession {
  id: string;
  title: string;
  timestamp: string;
  messages: ChatMessage[];
}

interface ChatState {
  sessions: ConversationSession[];
  activeSessionId: string;
  messages: ChatMessage[];
  isStreaming: boolean;
  activeScenario: 'furnace' | 'pump' | 'pid' | 'general';
  currentInput: string;
  activeTraceSteps: TraceStep[];
  regeneratingMsgId: string | null;
  currentRouting: {
    domain: string;
    model_id: string;
    routed_by: string;
    confidence: number;
  } | null;
  
  // Actions
  fetchUserSessions: (username?: string) => Promise<void>;
  fetchSessionById: (sessionId: string) => Promise<void>;
  createNewChat: (username?: string) => Promise<string>;
  selectSession: (id: string) => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  setCurrentInput: (input: string | ((prev: string) => string)) => void;
  setActiveScenario: (scenario: 'furnace' | 'pump' | 'pid' | 'general') => void;
  setStreaming: (isStreaming: boolean) => void;
  handleStreamEvent: (event: any) => void;
  clearTrace: () => void;
  regenerateMessage: (aiMsgIndex: number, role?: string) => void;
}

function normalizeDbMessage(msg: any): ChatMessage {
  let traceSteps = msg.trace_steps;
  if (!traceSteps && msg.trace_steps_json) {
    try {
      traceSteps = typeof msg.trace_steps_json === 'string' ? JSON.parse(msg.trace_steps_json) : msg.trace_steps_json;
    } catch { traceSteps = []; }
  }
  let deliverableIds = msg.deliverable_ids;
  if (!deliverableIds && msg.deliverables_json) {
    try {
      deliverableIds = typeof msg.deliverables_json === 'string' ? JSON.parse(msg.deliverables_json) : msg.deliverables_json;
    } catch { deliverableIds = []; }
  }

  // Robust fallback: Extract file IDs and download links directly from message markdown content
  if ((!deliverableIds || deliverableIds.length === 0) && msg.content) {
    const extracted: string[] = [];
    // Match /api/files/download/<id> or /api/files/<id>
    const fileMatches = msg.content.match(/\/api\/files\/(download\/)?([a-zA-Z0-9_-]+(\.[a-zA-Z0-9]+)?)/g);
    if (fileMatches) {
      fileMatches.forEach((m: string) => {
        const clean = m.replace(/\/api\/files\/(download\/)?/, '').trim();
        if (clean && !extracted.includes(clean)) {
          extracted.push(clean);
        }
      });
    }
    if (extracted.length > 0) {
      deliverableIds = extracted;
    }
  }

  let attachments = msg.attachments;
  if (!attachments && msg.attachments_json) {
    try {
      attachments = typeof msg.attachments_json === 'string' ? JSON.parse(msg.attachments_json) : msg.attachments_json;
    } catch { attachments = []; }
  }
  return {
    id: msg.id,
    role: msg.role,
    content: msg.content,
    timestamp: msg.created_at ? new Date(msg.created_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : (msg.timestamp || ''),
    model_id: msg.model_id,
    routed_by: msg.routed_by,
    confidence: msg.confidence,
    trace_steps: traceSteps || [],
    deliverable_ids: deliverableIds || [],
    attachments: attachments || [],
  };
}

function getApiBase(): string {
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    const port = window.location.port;
    if (port === '8000' || port === '3000' || port === '') return 'http://127.0.0.1:8000';
    return `http://${host}:8000`;
  }
  return 'http://127.0.0.1:8000';
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  activeSessionId: '',
  messages: [],
  isStreaming: false,
  regeneratingMsgId: null,
  activeScenario: 'pump',
  currentInput: '',
  activeTraceSteps: [],
  currentRouting: null,

  fetchUserSessions: async (username = 'operator') => {
    try {
      const apiBase = getApiBase();
      const res = await fetch(`${apiBase}/api/chat/sessions?username=${encodeURIComponent(username)}`);
      const data = await res.json();
      if (data.status === 'SUCCESS' && Array.isArray(data.sessions)) {
        const mysqlSessions: ConversationSession[] = data.sessions.map((s: any) => ({
          id: s.id,
          title: s.title || 'New Chat',
          timestamp: s.updated_at || s.created_at || 'Today',
          messages: (s.messages || []).map(normalizeDbMessage)
        }));

        set({ sessions: mysqlSessions });

        // Only fetch messages if user explicitly has an active session or opened /chat/[id]
        const currentActive = get().activeSessionId;
        if (currentActive) {
          await get().fetchSessionById(currentActive);
        }
      }
    } catch (err) {
      console.warn('[useChatStore] Fetch user sessions MySQL error:', err);
    }
  },

  fetchSessionById: async (sessionId: string) => {
    if (!sessionId) return;
    try {
      const apiBase = getApiBase();
      const res = await fetch(`${apiBase}/api/chat/sessions/${sessionId}`);
      const data = await res.json();
      if (data.status === 'SUCCESS' && data.session) {
        const sess = data.session;
        const formattedSession: ConversationSession = {
          id: sess.id,
          title: sess.title || 'New Chat',
          timestamp: sess.updated_at || sess.created_at || 'Today',
          messages: (sess.messages || []).map(normalizeDbMessage)
        };

        set((state) => {
          const exists = state.sessions.some(s => s.id === sessionId);
          const newSessions = exists
            ? state.sessions.map(s => (s.id === sessionId ? formattedSession : s))
            : [formattedSession, ...state.sessions];

          return {
            sessions: newSessions,
            activeSessionId: sessionId,
            messages: formattedSession.messages,
            activeTraceSteps: [],
            isStreaming: false
          };
        });
      }
    } catch (err) {
      console.warn('[useChatStore] Fetch session by ID MySQL error:', err);
    }
  },

  createNewChat: async (username = 'operator') => {
    try {
      const apiBase = getApiBase();
      const res = await fetch(`${apiBase}/api/chat/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, title: 'New Chat' })
      });
      const data = await res.json();
      if (data.status === 'SUCCESS' && data.session) {
        const newSess: ConversationSession = {
          id: data.session.id, // 16-digit random hex code URL ID
          title: 'New Chat',
          timestamp: 'Today',
          messages: []
        };

        set((state) => ({
          sessions: [newSess, ...state.sessions.filter(s => s.messages.length > 0 || s.id === newSess.id)],
          activeSessionId: newSess.id,
          messages: [],
          activeTraceSteps: [],
          currentInput: '',
          isStreaming: false
        }));

        return newSess.id;
      }
    } catch (err) {
      console.warn('[useChatStore] Create session MySQL fallback:', err);
    }

    // Client-side fallback: 16-digit hex code
    const hex16 = Array.from(crypto.getRandomValues(new Uint8Array(8)))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');

    const fallbackSess: ConversationSession = {
      id: hex16,
      title: 'New Chat',
      timestamp: 'Today',
      messages: []
    };

    set((state) => ({
      sessions: [fallbackSess, ...state.sessions.filter(s => s.messages.length > 0)],
      activeSessionId: hex16,
      messages: [],
      activeTraceSteps: [],
      currentInput: '',
      isStreaming: false
    }));

    return hex16;
  },

  selectSession: async (id: string) => {
    set({
      activeSessionId: id,
      activeTraceSteps: [],
      isStreaming: false
    });
    await get().fetchSessionById(id);
  },

  deleteSession: async (id: string) => {
    try {
      const apiBase = getApiBase();
      await fetch(`${apiBase}/api/chat/sessions/${id}`, { method: 'DELETE' });
    } catch (err) {
      console.warn('[useChatStore] Delete session MySQL error:', err);
    }

    set((state) => {
      const newSessions = state.sessions.filter((s) => s.id !== id);
      const isActive = state.activeSessionId === id;
      const nextActive = isActive ? (newSessions[0]?.id || '') : state.activeSessionId;
      const nextMsgs = isActive ? (newSessions[0]?.messages || []) : state.messages;
      return {
        sessions: newSessions,
        activeSessionId: nextActive,
        messages: nextMsgs,
      };
    });
  },

  setMessages: (messages) => set({ messages }),
  addMessage: (message) => {
    set((state) => {
      const newMsgs = [...state.messages, message];
      const sessionExists = state.sessions.some(s => s.id === state.activeSessionId);
      
      let updatedSessions: ConversationSession[];
      let targetSessionId = state.activeSessionId;
      if (sessionExists) {
        updatedSessions = state.sessions.map((s) => {
          if (s.id === targetSessionId) {
            const autoTitle = s.messages.length === 0 && message.role === 'user'
              ? message.content.slice(0, 28) + (message.content.length > 28 ? '...' : '')
              : s.title;
            return { ...s, title: autoTitle, messages: newMsgs };
          }
          return s;
        });
      } else {
        const autoTitle = message.role === 'user'
          ? message.content.slice(0, 28) + (message.content.length > 28 ? '...' : '')
          : 'Conversation';
        const newSessId = targetSessionId || Array.from(crypto.getRandomValues(new Uint8Array(8))).map(b => b.toString(16).padStart(2, '0')).join('');
        targetSessionId = newSessId;
        const newSess: ConversationSession = {
          id: newSessId,
          title: autoTitle,
          timestamp: 'Today',
          messages: newMsgs
        };
        updatedSessions = [newSess, ...state.sessions];
      }
      return { messages: newMsgs, sessions: updatedSessions, activeSessionId: targetSessionId };
    });
  },
  setCurrentInput: (inputOrUpdater) =>
    set((state) => ({
      currentInput:
        typeof inputOrUpdater === 'function'
          ? (inputOrUpdater as (prev: string) => string)(state.currentInput || '')
          : typeof inputOrUpdater === 'string'
          ? inputOrUpdater
          : '',
    })),
  setActiveScenario: (activeScenario) => set({ activeScenario }),
  setStreaming: (isStreaming) => set({ isStreaming }),
  clearTrace: () => set({ activeTraceSteps: [], currentRouting: null }),

  handleStreamEvent: (event: any) => {
    if (event.event === 'routing') {
      set({
        currentRouting: {
          domain: event.domain,
          model_id: event.model_id,
          routed_by: event.routed_by,
          confidence: event.confidence
        }
      });
    } else if (event.event === 'step') {
      const step: TraceStep = {
        id: `step-${Date.now()}-${Math.random()}`,
        step_number: event.step_number || (get().activeTraceSteps.length + 1),
        type: event.step_type || 'thought',
        content: event.content || '',
        tool_name: event.tool_name,
        tool_input: event.tool_input,
        tool_output: event.tool_output,
        duration_ms: event.duration_ms,
        ram_mb: event.ram_mb,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      set((state) => ({ activeTraceSteps: [...state.activeTraceSteps, step] }));
    } else if (event.event === 'final_answer') {
      const routing = get().currentRouting;
      const deliverableIds = event.deliverable_ids || [];
      const regenId = get().regeneratingMsgId;
      const agentMsg: ChatMessage = {
        id: regenId || `agent-${Date.now()}`,
        role: 'agent',
        content: event.content || '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model_id: event.display_model || event.model_id || routing?.model_id || 'Reasoning Engine',
        routed_by: (event.routed_by || routing?.routed_by || 'stage1_regex') as any,
        confidence: event.confidence || routing?.confidence || 98,
        trace_steps: get().activeTraceSteps,
        deliverable_ids: deliverableIds,
      };

      // Automatically register new deliverables in useDeliverableStore and open Canvas Workspace
      try {
        const { useDeliverableStore } = require('./useDeliverableStore');
        const addDeliv = useDeliverableStore.getState().addDeliverableFromAgent;
        const currentScenario = get().activeScenario;
        const currentModel = agentMsg.model_id || 'Reasoning Engine';
        deliverableIds.forEach((fname: string) => {
          addDeliv(fname, `Scenario: ${currentScenario.toUpperCase()}`, currentModel);
        });
      } catch {
        // Safe require fallback
      }

      set((state) => {
        let newMsgs: ChatMessage[];
        if (regenId) {
          // Replace only the specific message in-place
          newMsgs = state.messages.map((m) => (m.id === regenId ? agentMsg : m));
        } else {
          newMsgs = [...state.messages, agentMsg];
        }

        let updatedSessions = state.sessions.map((s) => {
          if (s.id === state.activeSessionId) {
            return { ...s, messages: newMsgs };
          }
          return s;
        });

        // Fallback: If no session matched activeSessionId, update the first session or create one
        if (state.sessions.length > 0 && !state.sessions.some((s) => s.id === state.activeSessionId)) {
          updatedSessions = state.sessions.map((s, idx) => {
            if (idx === 0) return { ...s, messages: newMsgs };
            return s;
          });
        }

        return {
          messages: newMsgs,
          sessions: updatedSessions,
          activeSessionId: state.activeSessionId || (updatedSessions[0]?.id ?? ''),
          isStreaming: false,
          regeneratingMsgId: null,
          activeTraceSteps: [],
          currentRouting: null
        };
      });
    }
  },

  regenerateMessage: (aiMsgIndex: number, role?: string) => {
    const state = get();
    if (state.isStreaming || aiMsgIndex < 0 || aiMsgIndex >= state.messages.length) return;

    const targetMsg = state.messages[aiMsgIndex];
    if (!targetMsg) return;

    // Find the preceding user message prompt
    let userPrompt = '';
    for (let i = aiMsgIndex - 1; i >= 0; i--) {
      if (state.messages[i]?.role === 'user') {
        userPrompt = state.messages[i].content;
        break;
      }
    }
    if (!userPrompt) return;

    // Keep all messages intact! Mark targetMsg as regenerating
    set({
      isStreaming: true,
      regeneratingMsgId: targetMsg.id,
      activeTraceSteps: [],
      currentRouting: null
    });

    // Extract last 3 messages prior to this user interaction for context
    const historyBefore = state.messages
      .slice(0, Math.max(0, aiMsgIndex - 1))
      .filter(m => m.content && m.content.trim().length > 0)
      .slice(-3)
      .map(m => ({ role: m.role, content: m.content }));

    try {
      const { socketManager } = require('@/lib/socket');
      socketManager.sendChatTask(userPrompt, [], role, true, state.activeSessionId, historyBefore);
    } catch (err) {
      console.error('Failed to send regenerate task:', err);
      set({ isStreaming: false, regeneratingMsgId: null });
    }
  }
}));
