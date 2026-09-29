import { create } from 'zustand';
import { getApiHost } from '@/lib/apiBase';
import { apiFetch } from '@/lib/apiFetch';

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
  /** Real failure reason for the last swap attempt (no fabricated success). */
  swapError: string | null;

  // Actions
  fetchModels: () => Promise<void>;
  fetchVRAM: () => Promise<void>;
  setActivePrimary: (id: string) => void;
  setActiveSecondary: (id: string | null) => void;
  updateVRAM: (vram: Partial<VRAMTelemetry>) => void;
  triggerModelSwap: (targetModelId: string) => Promise<boolean>;
  addSwapEvent: (event: SwapEvent) => void;
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
  swapError: null,

  fetchModels: async () => {
    try {
      const res = await apiFetch(`/api/models`);
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
      const res = await apiFetch(`/api/models/vram`);
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
    set({ isSwapping: true, swapError: null });

    const recordFailure = (message: string) =>
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
            status: 'failed',
            trigger: 'manual_override',
            target_met: false,
          },
          ...state.swapHistory,
        ],
      }));

    try {
      // 1. Call real backend POST /api/models/swap
      const res = await apiFetch(`/api/models/swap`, {
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
        return true;
      }

      // Non-2xx: the swap did not happen — report the server's own reason.
      const errData = await res.json().catch(() => ({}));
      recordFailure(errData?.detail || `Swap rejected by the backend (HTTP ${res.status}).`);
      return false;
    } catch (err: any) {
      // Backend unreachable: the model did NOT change. Never fake a successful swap.
      recordFailure(err?.message || 'Backend unreachable — the model was not swapped.');
      return false;
    }
  }
}));