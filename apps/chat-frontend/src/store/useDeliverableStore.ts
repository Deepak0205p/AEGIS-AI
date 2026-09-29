import { create } from 'zustand';
import { getApiHost } from '@/lib/apiBase';
import { apiFetch } from '@/lib/apiFetch';

export type DeliverableType = 'docx' | 'xlsx' | 'pptx' | 'py' | 'pdf' | 'sql' | 'json' | 'ts' | 'js' | 'sh' | 'txt' | 'csv';
export type VerificationStatus = 'PENDING_STAGE_1' | 'PENDING_STAGE_2' | 'VERIFIED' | 'REJECTED';

export interface DeliverableItem {
  id: string;
  filename: string;
  type: DeliverableType;
  size_bytes: number;
  size_formatted: string;
  source_scenario: string;
  source_requirement: string;
  generating_model: string;
  generated_timestamp: string;
  sha256_hash: string;
  summary: string;
  key_metrics: { label: string; value: string }[];
  sop_citations: string[];
  // 2-Step Human Verification Properties
  verification_status?: VerificationStatus;
  stage_1_verifier?: string | null;
  stage_1_at?: string | null;
  stage_1_notes?: string | null;
  stage_2_verifier?: string | null;
  stage_2_at?: string | null;
  stage_2_notes?: string | null;
  rejected_by?: string | null;
  rejected_at?: string | null;
  reject_reason?: string | null;
}

interface DeliverableState {
  deliverables: DeliverableItem[];
  selectedDeliverable: DeliverableItem | null;
  filterType: 'ALL' | DeliverableType;
  searchQuery: string;

  // Actions
  setFilterType: (type: 'ALL' | DeliverableType) => void;
  setSearchQuery: (query: string) => void;
  selectDeliverable: (id: string | null) => void;
  downloadDeliverable: (id: string) => Promise<void>;
  addDeliverableFromAgent: (filename: string, scenarioId: string, modelId: string) => void;
  fetchDiskDeliverables: () => Promise<void>;
  renameDeliverable: (id: string, newName: string) => Promise<boolean>;
  /** Applies genuine metadata reported by the backend (e.g. after a Canvas save). */
  applyServerMetadata: (id: string, patch: Partial<DeliverableItem>) => void;
}

function normalizeFileId(target: string): string {
  return (target || '').replace(/^\/api\/files\/(download\/)?/, '').trim();
}

function formatBytes(bytes: number | null | undefined): string {
  if (!bytes || bytes <= 0) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const useDeliverableStore = create<DeliverableState>((set, get) => ({
  deliverables: [],
  selectedDeliverable: null,
  filterType: 'ALL',
  searchQuery: '',

  setFilterType: (filterType) => set({ filterType }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),

  selectDeliverable: (id) => {
    if (!id) {
      set({ selectedDeliverable: null });
      return;
    }
    const item = get().deliverables.find((d) => d.id === id) || null;
    set({ selectedDeliverable: item });
  },

  renameDeliverable: async (id: string, newName: string) => {
    const cleanName = newName.trim();
    if (!cleanName) return false;

    try {
      const res = await apiFetch(`/api/files/${id}/rename`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: cleanName }),
      });
      // apiFetch returns the Response and only throws on network errors, so a
      // 401/404/400 arrives here as a successful await. Checking res.ok is what
      // stops the UI from renaming locally and reporting success for a write the
      // server rejected.
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        console.warn(
          `[useDeliverableStore] rename rejected (HTTP ${res.status}):`,
          (detail as any)?.detail
        );
        return false;
      }
    } catch (e) {
      console.warn('[useDeliverableStore] rename request failed:', e);
      return false;
    }

    set((state) => {
      const updatedList = state.deliverables.map((d) => {
        if (d.id === id || d.filename.toLowerCase() === id.toLowerCase()) {
          const rawExt = cleanName.split('.').pop()?.toLowerCase();
          const type = (['docx', 'xlsx', 'pptx', 'py'].includes(rawExt || '') ? rawExt : d.type) as DeliverableType;
          return { ...d, filename: cleanName, type };
        }
        return d;
      });

      const updatedSelected =
        state.selectedDeliverable &&
        (state.selectedDeliverable.id === id || state.selectedDeliverable.filename.toLowerCase() === id.toLowerCase())
          ? { ...state.selectedDeliverable, filename: cleanName }
          : state.selectedDeliverable;

      return { deliverables: updatedList, selectedDeliverable: updatedSelected };
    });

    return true;
  },

  addDeliverableFromAgent: (identifierOrFilename: string, scenarioId: string, modelId: string) => {
    // 1. Clean the identifier if it came as a URL
    const cleanId = identifierOrFilename.replace(/^\/api\/files\/(download\/)?/, '').trim();
    if (!cleanId) return;

    // 2. Fetch disk deliverables asynchronously so the genuine item is registered from database
    get().fetchDiskDeliverables();

    const existing = get().deliverables.find(d => d.id === cleanId || d.filename.toLowerCase() === cleanId.toLowerCase());
    if (existing) return;

    let ext: DeliverableType = 'docx';
    let filename = cleanId;
    if (cleanId.includes('.')) {
      const parsedExt = cleanId.split('.').pop()?.toLowerCase();
      if (['docx', 'xlsx', 'pptx', 'py'].includes(parsedExt || '')) {
        ext = parsedExt as DeliverableType;
      }
    } else {
      filename = `${cleanId}.docx`;
    }

    const newItem: DeliverableItem = {
      id: cleanId,
      filename,
      type: ext,
      // Placeholder until the backend reports the real size/hash for this file.
      size_bytes: 0,
      size_formatted: '—',
      source_scenario: scenarioId,
      source_requirement: 'Production Deliverable',
      generating_model: modelId,
      generated_timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      sha256_hash: 'unavailable',
      summary: `Automated deliverable generated by ${modelId} for ${scenarioId}.`,
      key_metrics: [{ label: 'Status', value: 'AWAITING SERVER METADATA' }],
      // No invented source references: a citation is only shown when the server
      // supplied one for this deliverable.
      sop_citations: []
    };

    set(state => ({ deliverables: [newItem, ...state.deliverables] }));
  },

  fetchDiskDeliverables: async () => {
    try {
      const res = await apiFetch(`/api/files/list`);
      if (res.ok) {
        const data = await res.json();
        const rawList = data.files || data.deliverables || [];
        if (Array.isArray(rawList) && rawList.length > 0) {
          const diskItems: DeliverableItem[] = rawList.map((f: any) => {
            const rawExt = (f.filename || '').split('.').pop()?.toLowerCase();
            const type = (f.file_type || rawExt || 'docx').toLowerCase() as DeliverableType;
            const vStatus = (f.verification_status || 'PENDING_STAGE_1') as VerificationStatus;
            return {
              id: f.file_id || f.id || `deliv-${Date.now()}`,
              filename: f.filename || `deliverable_${f.file_id || 'unnamed'}.${type}`,
              type: (['docx', 'xlsx', 'pptx', 'py'].includes(type) ? type : 'docx') as DeliverableType,
              size_bytes: typeof f.size_bytes === 'number' ? f.size_bytes : 0,
              size_formatted: f.size_formatted || formatBytes(f.size_bytes),
              source_scenario: f.chat_id ? `Session: ${f.chat_id}` : (f.source_scenario || 'Refinery Output'),
              source_requirement: f.source_requirement || 'Generated Deliverable',
              generating_model: f.generating_model || 'Sovereign Gemma-4',
              generated_timestamp: f.created_at || f.generated_timestamp || new Date().toLocaleTimeString(),
              sha256_hash: f.sha256_hash || 'unavailable',
              summary: f.summary || `Air-gapped generated file: ${f.filename}`,
              key_metrics: f.key_metrics || [{ label: 'Format', value: type.toUpperCase() }, { label: 'Status', value: vStatus }],
              // Only real, server-supplied citations; never a placeholder source.
              sop_citations: Array.isArray(f.sop_citations) ? f.sop_citations : [],
              verification_status: vStatus,
              stage_1_verifier: f.stage_1_verifier || null,
              stage_1_at: f.stage_1_at || null,
              stage_1_notes: f.stage_1_notes || null,
              stage_2_verifier: f.stage_2_verifier || null,
              stage_2_at: f.stage_2_at || null,
              stage_2_notes: f.stage_2_notes || null,
              rejected_by: f.rejected_by || null,
              rejected_at: f.rejected_at || null,
              reject_reason: f.reject_reason || null,
            };
          });

          const currentList = get().deliverables;
          // Merge: Keep disk items first, then any custom local items not on disk
          const diskIds = new Set(diskItems.map(d => d.id));
          const diskFilenames = new Set(diskItems.map(d => d.filename));
          const nonDisk = currentList.filter(c => !diskIds.has(c.id) && !diskFilenames.has(c.filename));
          set({ deliverables: [...diskItems, ...nonDisk] });
        }
      }
    } catch (e) {
      console.warn('[useDeliverableStore] Auto-sync disk deliverables fallback:', e);
    }
  },

  downloadDeliverable: async (id: string) => {
    const item = get().deliverables.find((d) => d.id === id);
    if (!item) return;

    try {
      // 1. Fetch the genuine binary deliverable from the live backend.
      //    The path parameter is the file_id, not the filename: the backend
      //    resolves it with get_file_record(file_id), so sending the filename
      //    404'd for every real deliverable.
      const res = await apiFetch(`/api/files/download/${encodeURIComponent(item.id)}`);
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = item.filename;
        a.click();
        URL.revokeObjectURL(url);
        return;
      }
      console.warn(
        `[useDeliverableStore] Download of ${item.filename} failed (HTTP ${res.status}).`
      );
    } catch (e) {
      console.warn('[useDeliverableStore] Download request failed:', e);
    }

    // Backend unavailable: report the failure instead of pretending it downloaded.
    const sanitizedFilename = item.filename.replace(/[^a-zA-Z0-9._-]/g, '_');
    console.warn(`[useDeliverableStore] Backend unavailable. Cannot download ${sanitizedFilename}.`);
  },

  applyServerMetadata: (id: string, patch: Partial<DeliverableItem>) => {
    const cleanId = normalizeFileId(id);
    if (!cleanId) return;

    const defined = Object.fromEntries(
      Object.entries(patch).filter(([, value]) => value !== undefined)
    ) as Partial<DeliverableItem>;
    if (Object.keys(defined).length === 0) return;

    const matches = (itemId: string) => itemId === cleanId || itemId === id;

    set((state) => ({
      deliverables: state.deliverables.map((d) => (matches(d.id) ? { ...d, ...defined } : d)),
      selectedDeliverable:
        state.selectedDeliverable && matches(state.selectedDeliverable.id)
          ? { ...state.selectedDeliverable, ...defined }
          : state.selectedDeliverable,
    }));
  },
}));