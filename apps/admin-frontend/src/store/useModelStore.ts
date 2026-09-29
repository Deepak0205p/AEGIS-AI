import { create } from 'zustand';
import { api } from '@/lib/api';

export interface ModelInfo {
  id: string;
  name: string;
  display_name?: string;
  ollama_tag?: string;
  vllm_model_name?: string;
  quantization: string;
  vram_mb: number;
  context_length: number;
  domain: string;
  is_primary: boolean;
  keep_alive: string;
  status: 'active' | 'standby' | 'swapping' | 'unloaded';
  description: string;
  backend?: string;
  tier?: string;
  endpoint_url?: string;
  node_ip?: string;
}

export interface SwapEvent {
  id: string;
  timestamp: string;
  from_model: string;
  to_model: string;
  duration_ms: number;
  status: 'SUCCESS' | 'FAILED' | 'OOM_FALLBACK';
  trigger: string;
  target_met: boolean;
  freed_vram_mb?: number;
  allocated_vram_mb?: number;
}

export interface VRAMTelemetry {
  gpu_available?: boolean;
  gpu_name?: string | null;
  total_mb: number;
  used_mb: number;
  free_mb: number;
  usage_percent: number;
  os_overhead_mb: number;
  primary_model_mb: number;
  secondary_model_mb: number;
  kv_cache_mb: number;
  active_profile?: string | null;
  max_concurrent_active_models?: number | null;
  loaded_models?: string[];
  temperature_celsius?: number;
  system_ram_total_mb?: number;
  system_ram_used_mb?: number;
  system_ram_free_mb?: number;
  system_ram_percent?: number;
}

export interface ComputeNode {
  id: string;
  name: string;
  host_ip: string;
  port: number;
  is_local: boolean;
  status: 'online' | 'offline' | 'testing';
  device_type: string;
  discovered_models: string[];
  latency_ms?: number;
  last_seen?: string;
  vram_total_mb?: number;
  vram_used_mb?: number;
}

interface ModelState {
  models: ModelInfo[];
  nodes: ComputeNode[];
  activeModel: string;
  activePrimaryId: string;
  activeSecondaryId: string | null;
  backendType: 'vLLM' | 'OLLaMA' | 'llama.cpp';
  vram: VRAMTelemetry;
  gpuUtilizationPct: number;
  gpuTemperatureC: number;
  loadedModels: string[];
  swapHistory: SwapEvent[];
  isSwapping: boolean;
  isPolling: boolean;
  isLoadingNodes: boolean;
  /** Real failure messages surfaced to the UI — never replaced by a fake success. */
  swapError: string | null;
  nodesError: string | null;
  endpointError: string | null;
  clearOperationError: () => void;

  // Actions
  fetchModels: () => Promise<void>;
  fetchNodes: () => Promise<void>;
  testNodeConnection: (hostIp: string, port?: number) => Promise<{ online: boolean; models: string[]; latency_ms?: number; message: string }>;
  addNode: (node: { name: string; host_ip: string; port?: number; device_type?: string; models?: string[] }) => Promise<boolean>;
  deleteNode: (nodeId: string) => Promise<boolean>;
  bindModelToNode: (modelId: string, nodeId: string) => Promise<boolean>;
  fetchVRAM: () => Promise<void>;
  fetchModelStatus: () => Promise<void>;
  updateVRAM: (vram: Partial<VRAMTelemetry>) => void;
  triggerModelSwap: (targetModelId: string) => Promise<boolean>;
  updateModelEndpoint: (modelId: string, endpointUrl: string) => Promise<boolean>;
  startPolling: () => void;
  stopPolling: () => void;
  addSwapEvent: (event: SwapEvent) => void;
}

let pollingTimer: NodeJS.Timeout | null = null;
let visibilityHandler: (() => void) | null = null;

export const useModelStore = create<ModelState>((set, get) => ({
  // Nothing is known until the backend reports it: no demo node, no assumed model.
  models: [],
  nodes: [],
  activeModel: '',
  activePrimaryId: '',
  activeSecondaryId: null,
  backendType: 'OLLaMA',
  vram: {
    gpu_available: false,
    // No placeholder name: a GPU model is only ever shown once /api/v1/models/vram
    // reports a real one. "Detecting hardware..." was rendered as a GPU name.
    gpu_name: null,
    total_mb: 0,
    used_mb: 0,
    free_mb: 0,
    usage_percent: 0,
    os_overhead_mb: 0,
    primary_model_mb: 0,
    secondary_model_mb: 0,
    kv_cache_mb: 0,
    // GET /api/v1/models/vram returns neither of these, so they stay empty
    // rather than asserting a profile the backend never reported.
    active_profile: null,
    max_concurrent_active_models: null,
    loaded_models: [],
    temperature_celsius: 0,
    system_ram_total_mb: 0,
    system_ram_used_mb: 0,
    system_ram_free_mb: 0,
    system_ram_percent: 0,
  },
  gpuUtilizationPct: 0,
  gpuTemperatureC: 0,
  loadedModels: [],
  swapHistory: [],
  isSwapping: false,
  isPolling: false,
  isLoadingNodes: false,
  swapError: null,
  nodesError: null,
  endpointError: null,

  clearOperationError: () => set({ swapError: null, nodesError: null, endpointError: null }),

  fetchModels: async () => {
    try {
      const data = await api.get<ModelInfo[]>('/api/v1/models');
      if (Array.isArray(data) && data.length > 0) {
        const pri = data.find((m) => m.is_primary)?.id || data[0].id;
        const sec = data.find((m) => !m.is_primary && m.status === 'active')?.id || null;
        set({ models: data, activePrimaryId: pri, activeSecondaryId: sec });
      }
    } catch {
      // Keep existing models state
    }
  },

  fetchNodes: async () => {
    set({ isLoadingNodes: true });
    try {
      const nodes = await api.get<ComputeNode[]>('/api/v1/nodes');
      if (Array.isArray(nodes) && nodes.length > 0) {
        set({ nodes, isLoadingNodes: false });
      } else {
        set({ isLoadingNodes: false });
      }
    } catch {
      set({ isLoadingNodes: false });
    }
  },

  testNodeConnection: async (hostIp: string, port = 11434) => {
    try {
      const result = await api.post<any>('/api/v1/nodes/test', {
        host_ip: hostIp,
        port: port,
      });
      return {
        online: !!result.online,
        models: result.models || [],
        latency_ms: result.latency_ms ?? 0,
        message: result.message || 'Ping completed',
      };
    } catch (err: any) {
      return {
        online: false,
        models: [],
        latency_ms: 0,
        message: err?.message || 'Connection test failed',
      };
    }
  },

  addNode: async (nodeData) => {
    set({ nodesError: null });
    try {
      await api.post('/api/v1/nodes', {
        name: nodeData.name,
        host_ip: nodeData.host_ip,
        port: nodeData.port || 11434,
        device_type: nodeData.device_type || 'LAN Worker',
        models: nodeData.models || [],
      });
      await get().fetchNodes();
      await get().fetchModels();
      return true;
    } catch (err: any) {
      // The node was NOT registered — report the failure instead of inventing an online peer.
      set({ nodesError: err?.message || `Could not register node ${nodeData.host_ip}.` });
      return false;
    }
  },

  deleteNode: async (nodeId: string) => {
    set({ nodesError: null });
    try {
      await api.delete(`/api/v1/nodes/${nodeId}`);
      await get().fetchNodes();
      await get().fetchModels();
      return true;
    } catch (err: any) {
      set({ nodesError: err?.message || `Could not remove node ${nodeId}.` });
      return false;
    }
  },

  bindModelToNode: async (modelId: string, nodeId: string) => {
    try {
      await api.post('/api/v1/nodes/bind', { model_id: modelId, node_id: nodeId });
      await get().fetchModels();
      return true;
    } catch {
      return false;
    }
  },

  fetchVRAM: async () => {
    try {
      const data = await api.get<VRAMTelemetry>('/api/v1/models/vram');
      if (data) {
        set({
          vram: { ...get().vram, ...data },
          gpuTemperatureC: data.temperature_celsius ?? get().gpuTemperatureC,
          gpuUtilizationPct: data.usage_percent ?? get().gpuUtilizationPct,
        });
      }
    } catch {
      // Keep cached telemetry; never invent readings.
    }
  },

  updateVRAM: (newVram) =>
    set((state) => ({ vram: { ...state.vram, ...newVram } })),

  fetchModelStatus: async () => {
    try {
      const statusData = await api.get<any>('/api/v1/models/status');
      if (statusData) {
        // GET /api/v1/models/status returns `status`, `active_model`,
        // `active_domain`, `domain_info` and `models`. The previous reads
        // (active_primary_model / active_secondary_model / loaded_models /
        // vram_telemetry) matched no returned key, so all four were undefined
        // and the store silently kept stale values on every 2s poll.
        set({
          activePrimaryId: statusData.active_model || get().activePrimaryId,
          activeSecondaryId: get().activeSecondaryId,
          loadedModels: Array.isArray(statusData.models)
            ? statusData.models.filter((m: any) => m?.status === 'active').map((m: any) => m.id)
            : get().loadedModels,
          activeModel: statusData.active_model || get().activeModel,
        });
        // VRAM telemetry is a separate endpoint; poll it on the same cadence.
        get().fetchVRAM();
      }

      // Fetch live swap logs
      const swaps = await api.get<SwapEvent[]>('/api/v1/models/swaps');
      if (Array.isArray(swaps)) {
        set({ swapHistory: swaps });
      }
    } catch {
      // Graceful offline fallback
    }
  },

  triggerModelSwap: async (targetModelId: string) => {
    set({ isSwapping: true, swapError: null });
    try {
      const swapEvent = await api.post<SwapEvent>('/api/v1/models/swap', {
        model_id: targetModelId,
      });

      await get().fetchModels();
      await get().fetchVRAM();

      set((state) => ({
        activeSecondaryId: targetModelId,
        isSwapping: false,
        swapHistory: [swapEvent, ...state.swapHistory.filter((s) => s.id !== swapEvent.id)],
      }));
      return true;
    } catch (err: any) {
      // The swap did NOT happen. Record a genuine FAILED event and surface the reason
      // instead of fabricating a SUCCESS swap and flipping model states.
      const message = err?.message || 'Model swap request failed.';
      set((state) => ({
        isSwapping: false,
        swapError: message,
        swapHistory: [
          {
            id: `swap-failed-${Date.now()}`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            from_model: state.activeSecondaryId || 'unknown',
            to_model: targetModelId,
            duration_ms: 0,
            status: 'FAILED',
            trigger: 'MANUAL_HOTSWAP',
            target_met: false,
          },
          ...state.swapHistory,
        ],
      }));
      return false;
    }
  },

  updateModelEndpoint: async (modelId: string, endpointUrl: string) => {
    set({ endpointError: null });
    try {
      await api.post(`/api/v1/models/${modelId}/endpoint`, { endpoint_url: endpointUrl });
      await get().fetchModels();
      return true;
    } catch (err: any) {
      set({ endpointError: err?.message || `Could not update endpoint for ${modelId}.` });
      return false;
    }
  },

  startPolling: () => {
    if (pollingTimer) return;
    // A previous run may have installed a visibilitychange handler that is no
    // longer referenced (the handler nulls pollingTimer when the tab hides, so
    // the `if (pollingTimer) return` guard above no longer protects us). Remove
    // any stale listener first, otherwise duplicate 2s polling loops accumulate
    // on every remount of OverviewDeck.
    if (visibilityHandler && typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', visibilityHandler);
      visibilityHandler = null;
    }
    set({ isPolling: true });

    // Initial immediate fetch
    get().fetchModels();
    get().fetchVRAM();
    get().fetchModelStatus();

    // 2-second real-time polling interval
    pollingTimer = setInterval(() => {
      get().fetchVRAM();
      get().fetchModelStatus();
    }, 2000);

    // Lifecycle: pause polling when tab is inactive to preserve resources
    if (typeof document !== 'undefined') {
      visibilityHandler = () => {
        if (document.visibilityState === 'hidden') {
          if (pollingTimer) {
            clearInterval(pollingTimer);
            pollingTimer = null;
          }
        } else if (document.visibilityState === 'visible') {
          if (!pollingTimer) {
            get().fetchVRAM();
            get().fetchModelStatus();
            pollingTimer = setInterval(() => {
              get().fetchVRAM();
              get().fetchModelStatus();
            }, 2000);
          }
        }
      };
      document.addEventListener('visibilitychange', visibilityHandler);
    }
  },

  stopPolling: () => {
    if (pollingTimer) {
      clearInterval(pollingTimer);
      pollingTimer = null;
    }
    if (visibilityHandler && typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', visibilityHandler);
      visibilityHandler = null;
    }
    set({ isPolling: false });
  },

  addSwapEvent: (event) => set((state) => ({ swapHistory: [event, ...state.swapHistory] })),
}));
