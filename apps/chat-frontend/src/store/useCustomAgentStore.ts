import { create } from 'zustand';
import { api } from '@/lib/api';

export interface CustomAgent {
  id: string;
  name: string;
  avatar: string;
  role: string;
  description: string;
  system_prompt: string;
  workflow_mode: 'sequential_agentic' | 'direct_fast' | 'autonomous_loop';
  tools: string[];
  created_at?: string;
  is_template?: boolean;
  author?: string;
}

interface CustomAgentState {
  agents: CustomAgent[];
  activeAgentId: string | null;
  isLoading: boolean;
  error: string | null;
  showBuilderModal: boolean;
  editingAgent: CustomAgent | null;

  // Actions
  fetchAgents: () => Promise<void>;
  setActiveAgent: (agentId: string | null) => void;
  openBuilder: (agent?: CustomAgent) => void;
  closeBuilder: () => void;
  saveAgent: (agent: Partial<CustomAgent>) => Promise<boolean>;
  deleteAgent: (agentId: string) => Promise<boolean>;
}

const DEFAULT_LOCAL_TEMPLATES: CustomAgent[] = [
  {
    id: 'template-cdu-yield-auditor',
    name: 'CDU Yield & Margin Auditor',
    avatar: '⚡',
    role: 'Process Optimization Specialist',
    description: 'Analyzes Crude Distillation Unit assay yields, furnace skin temps, and calculates gross refining margins (GRM).',
    system_prompt: 'You are the CDU Yield & Margin Auditor agent. Your objective is to audit distillation yields, calculate volumetric fractions, and flag any skin temperature deviations exceeding 420°C. When performing yield math, write and execute precise Python calculations. Ground all operational guidelines strictly in MRPL/OISD standards.',
    workflow_mode: 'sequential_agentic',
    tools: ['rag', 'sandbox', 'deliverables'],
    is_template: true,
    author: 'System Template'
  },
  {
    id: 'template-hse-shift-summarizer',
    name: 'HSE Shift & Incident Logger',
    avatar: '🛡️',
    role: 'HSE Safety Auditor & Compliance Lead',
    description: 'Audits Hot Work & Confined Space permits, validates OISD-STD-105 compliance, and generates shift handoff reports.',
    system_prompt: 'You are the HSE Shift & Incident Logger agent. Your objective is to verify safety permits, inspect gas testing thresholds (H2S < 10 ppm, LEL = 0%), and compile structured shift handover summaries with timestamped action items. Always cite referenced safety standards.',
    workflow_mode: 'sequential_agentic',
    tools: ['rag', 'chemicals', 'deliverables'],
    is_template: true,
    author: 'System Template'
  },
  {
    id: 'template-vibration-reliability-eng',
    name: 'Equipment Reliability & Vibration Eng',
    avatar: '⚙️',
    role: 'Mechanical Reliability Engineer',
    description: 'Assesses centrifugal pump vibration spectra (ISO 10816), bearing temperatures, and computes MTBF metrics.',
    system_prompt: 'You are the Equipment Reliability & Vibration Engineer. Your goal is to evaluate pump vibration velocity (mm/s RMS), check ISO 10816-3 Zone alarms, and run hydrodynamic or MTBF calculations using the Python Sandbox. Generate formal inspection summaries.',
    workflow_mode: 'sequential_agentic',
    tools: ['rag', 'sandbox', 'deliverables'],
    is_template: true,
    author: 'System Template'
  },
  {
    id: 'template-pid-isa-inspector',
    name: 'P&ID Instrument & ISA-5.1 Tag Inspector',
    avatar: '🔬',
    role: 'Instrumentation & Process Automation Lead',
    description: 'Extracts and verifies P&ID instrument loop tags (PT, TT, FT, ESDV), loop interlocks, and fail-safe actions.',
    system_prompt: 'You are the P&ID Instrument & ISA-5.1 Inspector. Your objective is to parse P&ID diagrams, verify tag nomenclatures, and check that emergency shutdown valves (ESDV) are properly specified with fail-closed (FC) safety positions.',
    workflow_mode: 'direct_fast',
    tools: ['rag', 'deliverables'],
    is_template: true,
    author: 'System Template'
  }
];

export const useCustomAgentStore = create<CustomAgentState>((set, get) => ({
  agents: DEFAULT_LOCAL_TEMPLATES,
  activeAgentId: null,
  isLoading: false,
  error: null,
  showBuilderModal: false,
  editingAgent: null,

  fetchAgents: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.get<any>('/api/v1/agents');
      if (res && Array.isArray(res.agents) && res.agents.length > 0) {
        set({ agents: res.agents, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    } catch {
      // Keep cached / default templates
      set({ isLoading: false });
    }
  },

  setActiveAgent: (agentId) => set({ activeAgentId: agentId }),

  openBuilder: (agent) =>
    set({
      showBuilderModal: true,
      editingAgent: agent || null,
    }),

  closeBuilder: () =>
    set({
      showBuilderModal: false,
      editingAgent: null,
    }),

  saveAgent: async (agentData) => {
    try {
      const id = agentData.id || `custom-agent-${Date.now()}`;
      const payload: CustomAgent = {
        id,
        name: agentData.name?.trim() || 'Custom Operations Agent',
        avatar: agentData.avatar || '🤖',
        role: agentData.role?.trim() || 'Industrial AI Specialist',
        description: agentData.description?.trim() || 'Custom agentic workflow for refinery tasks.',
        system_prompt: agentData.system_prompt?.trim() || 'You are an authoritative specialized Industrial AI Assistant.',
        workflow_mode: agentData.workflow_mode || 'sequential_agentic',
        tools: agentData.tools || ['rag', 'sandbox', 'deliverables'],
        created_at: new Date().toLocaleDateString(),
        is_template: false,
        author: agentData.author || 'Operator',
      };

      await api.post('/api/v1/agents', payload).catch(() => {});

      set((state) => ({
        agents: [payload, ...state.agents.filter((a) => a.id !== id)],
        activeAgentId: id,
        showBuilderModal: false,
        editingAgent: null,
      }));

      return true;
    } catch {
      return false;
    }
  },

  deleteAgent: async (agentId) => {
    try {
      await api.delete(`/api/v1/agents/${agentId}`).catch(() => {});
      set((state) => ({
        agents: state.agents.filter((a) => a.id !== agentId),
        activeAgentId: state.activeAgentId === agentId ? null : state.activeAgentId,
      }));
      return true;
    } catch {
      return false;
    }
  },
}));
