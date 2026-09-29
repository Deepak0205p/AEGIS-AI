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

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: string;
  model_id?: string;
  routed_by?: 'stage1_regex' | 'stage2_semantic' | 'manual';
  /** Null when the pipeline does not compute a calibrated confidence. */
  confidence?: number | null;
  trace_steps?: TraceStep[];
  deliverable_ids?: string[];
  /** True when the operator stopped generation before a final answer arrived. */
  aborted?: boolean;
}

interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  activeScenario: 'furnace' | 'pump' | 'pid' | 'general';
  currentInput: string;
  activeTraceSteps: TraceStep[];
  /** Tokens received so far, so a stopped run can show its partial output. */
  streamingContent: string;
  currentRouting: {
    domain: string;
    model_id: string;
    routed_by: string;
    confidence: number | null;
  } | null;
  
  // Actions
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (message: ChatMessage) => void;
  setCurrentInput: (input: string) => void;
  setActiveScenario: (scenario: 'furnace' | 'pump' | 'pid' | 'general') => void;
  setStreaming: (isStreaming: boolean) => void;
  handleStreamEvent: (event: any) => void;
  clearTrace: () => void;
  /** Finalises a stopped run with whatever text was actually received. */
  abortGeneration: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // No fabricated system greeting: the transcript starts empty.
  messages: [],
  isStreaming: false,
  activeScenario: 'pump',
  currentInput: '',
  activeTraceSteps: [],
  streamingContent: '',
  currentRouting: null,

  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setCurrentInput: (currentInput) => set({ currentInput }),
  setActiveScenario: (activeScenario) => set({ activeScenario }),
  setStreaming: (isStreaming) => set({ isStreaming }),
  clearTrace: () => set({ activeTraceSteps: [], currentRouting: null }),

  abortGeneration: () => {
    const partial = get().streamingContent.trim();
    const routing = get().currentRouting;

    set((state) => {
      const reset = {
        isStreaming: false,
        streamingContent: '',
        activeTraceSteps: [],
        currentRouting: null,
      };
      if (!partial) return reset;

      const stoppedMsg: ChatMessage = {
        id: `agent-stopped-${Date.now()}`,
        role: 'agent',
        content: partial,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model_id: routing?.model_id,
        routed_by: (routing?.routed_by || 'stage1_regex') as any,
        confidence: routing?.confidence ?? null,
        trace_steps: state.activeTraceSteps,
        deliverable_ids: [],
        aborted: true,
      };
      return { ...reset, messages: [...state.messages, stoppedMsg] };
    });
  },

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
      if (event.step_type === 'token') {
        // Token frames accumulate into the live buffer instead of becoming
        // thousands of trace rows; they are also what a Stop preserves.
        const token = event.token ?? event.content ?? '';
        set((state) => ({ streamingContent: state.streamingContent + token }));
        return;
      }
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
      const agentMsg: ChatMessage = {
        id: `agent-${Date.now()}`,
        role: 'agent',
        content: event.content || '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model_id: event.display_model || event.model_id || routing?.model_id || 'Reasoning Engine',
        routed_by: (event.routed_by || routing?.routed_by || 'stage1_regex') as any,
        confidence: event.confidence ?? routing?.confidence ?? null,
        trace_steps: get().activeTraceSteps,
        deliverable_ids: deliverableIds,
      };

      // Automatically register new deliverables in useDeliverableStore for Screen 5
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

      set((state) => ({
        messages: [...state.messages, agentMsg],
        isStreaming: false,
        streamingContent: '',
        activeTraceSteps: [],
        currentRouting: null
      }));
    }
  }
}));
