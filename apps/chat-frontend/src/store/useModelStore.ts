import { create } from 'zustand';

export interface ModelInfo {
  id: string;
  name: string;
  display_name?: string;
  ollama_tag?: string;
  quantization: string;
  vram_mb: number;
  context_length: number;
  domain: string;
  is_primary: boolean;
  keep_alive: string;
  status: 'active' | 'standby' | 'swapping' | 'unloaded';
  description: string;
}

export interface SwapEvent {
  id: string;
  timestamp: string;
  from_model: string;
  to_model: string;
  duration_ms: number;
  status: 'success' | 'failed';
  trigger: 'router_auto' | 'manual_override';
  target_met: boolean;
}

export interface VRAMTelemetry {
  gpu_available?: boolean;
  gpu_name?: string;
  total_mb: number;
  used_mb: number;
  free_mb: number;
  usage_percent: number;
  os_overhead_mb: number;
  primary_model_mb: number;
  secondary_model_mb: number;
  kv_cache_mb: number;
  temperature_celsius?: number;
  system_ram_total_mb?: number;
  system_ram_used_mb?: number;
  system_ram_free_mb?: number;
  system_ram_percent?: number;
}

interface ModelState {
  models: ModelInfo[];
  activePrimaryId: string;
  activeSecondaryId: string | null;
  vram: VRAMTelemetry;
  swapHistory: SwapEvent[];
  isSwapping: boolean;
  
  // Actions
  fetchModels: () => Promise<void>;
  fetchVRAM: () => Promise<void>;
  setActivePrimary: (id: string) => void;
  setActiveSecondary: (id: string | null) => void;
  updateVRAM: (vram: Partial<VRAMTelemetry>) => void;
  triggerModelSwap: (targetModelId: string) => Promise<void>;
  addSwapEvent: (event: SwapEvent) => void;
}

function getApiHost(): string {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (/^[a-zA-Z0-9.-]+$/.test(hostname)) {
      return hostname;
    }
  }
  return '127.0.0.1';
}

export const useModelStore = create<ModelState>((set, get) => ({
  models: [],
  activePrimaryId: '',
  activeSecondaryId: null,
  vram: {
    total_mb: 6144,
    used_mb: 0,
    free_mb: 6144,
    usage_percent: 0,
    os_overhead_mb: 0,
    primary_model_mb: 0,
    secondary_model_mb: 0,
    kv_cache_mb: 0
  },
  swapHistory: [],
  isSwapping: false,

  fetchModels: async () => {
    try {
      const host = getApiHost();
      const res = await fetch(`http://${host}:8000/api/models`);
      if (res.ok) {
        const data: ModelInfo[] = await res.json();
        const pri = data.find(m => m.is_primary)?.id || (data.length > 0 ? data[0].id : '');
        const sec = data.find(m => !m.is_primary && m.status === 'active')?.id || null;
        set({ models: data, activePrimaryId: pri, activeSecondaryId: sec });
      }
    } catch {
      // Graceful fallback
    }
  },

  fetchVRAM: async () => {
    try {
      const host = getApiHost();
      const res = await fetch(`http://${host}:8000/api/models/vram`);
      if (res.ok) {
        const data: VRAMTelemetry = await res.json();
        set({ vram: data });
      }
    } catch {
      // Graceful fallback
    }
  },

  setActivePrimary: (id) => set({ activePrimaryId: id }),
  setActiveSecondary: (id) => set({ activeSecondaryId: id }),
  updateVRAM: (newVram) => set((state) => ({ vram: { ...state.vram, ...newVram } })),
  addSwapEvent: (event) => set((state) => ({ swapHistory: [event, ...state.swapHistory] })),

  triggerModelSwap: async (targetModelId: string) => {
    set({ isSwapping: true });
    const host = getApiHost();

    try {
      // 1. Call real backend POST /api/models/swap
      const res = await fetch(`http://${host}:8000/api/models/swap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: targetModelId
        })
      });

      if (res.ok) {
        const swapEvent: SwapEvent = await res.json();
        
        // 2. Refresh models and VRAM from live backend
        await get().fetchModels();
        await get().fetchVRAM();

        set((state) => ({
          activeSecondaryId: targetModelId,
          isSwapping: false,
          swapHistory: [swapEvent, ...state.swapHistory]
        }));
        return;
      }
    } catch {
      // Fallback local swap handler if backend unreachable
    }

    set({ isSwapping: false });
  }
}));
