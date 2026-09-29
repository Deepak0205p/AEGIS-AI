import { create } from 'zustand';
import { DeliverableItem, useDeliverableStore } from './useDeliverableStore';
import { getApiBase } from '@/lib/apiBase';
import { useAuthStore } from './useAuthStore';
import { apiFetch } from '@/lib/apiFetch';

export type CanvasTab = 'editor' | 'metrics' | 'sop' | 'raw';

interface CanvasState {
  isOpen: boolean;
  isExpanded: boolean;
  activeDeliverable: DeliverableItem | null;
  activeTab: CanvasTab;
  editedContent: Record<string, any>;
  dirtyIds: Record<string, boolean>;
  hasUnsavedChanges: boolean;
  isSaving: boolean;
  saveError: string | null;
  lastSavedAt: string | null;

  // Actions
  openCanvas: (deliverableOrId: DeliverableItem | string) => void;
  closeCanvas: () => void;
  toggleExpand: () => void;
  setActiveTab: (tab: CanvasTab) => void;
  /** Seeds the editor buffer from the backend without marking the file dirty. */
  hydrateContent: (id: string, content: any) => void;
  /** Records a user edit and schedules a debounced real save. */
  updateEditedContent: (id: string, content: any) => void;
  clearSaveError: () => void;
  renameActiveDeliverable: (newName: string) => Promise<void>;
  /** Persists the editor buffer to the real deliverable on disk. */
  saveChanges: (id: string) => Promise<boolean>;
}

const AUTOSAVE_DEBOUNCE_MS = 1500;

let autoSaveTimer: ReturnType<typeof setTimeout> | null = null;
const inflightSaves = new Map<string, Promise<boolean>>();

function normalizeFileId(target: string): string {
  return (target || '').replace(/^\/api\/files\/(download\/)?/, '').trim();
}

function formatBytes(bytes: number): string {
  if (!bytes || bytes < 0) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const useCanvasStore = create<CanvasState>((set, get) => ({
  isOpen: false,
  isExpanded: false,
  activeDeliverable: null,
  activeTab: 'editor',
  editedContent: {},
  dirtyIds: {},
  hasUnsavedChanges: false,
  isSaving: false,
  saveError: null,
  lastSavedAt: null,

  openCanvas: async (deliverableOrId: DeliverableItem | string) => {
    let item: DeliverableItem | null = null;
    if (typeof deliverableOrId === 'string') {
      const cleanTarget = normalizeFileId(deliverableOrId);
      
      // Always ensure deliverables are synced
      await useDeliverableStore.getState().fetchDiskDeliverables();
      let { deliverables } = useDeliverableStore.getState();
      item = deliverables.find(
        (d) =>
          d.id === cleanTarget ||
          d.id === deliverableOrId ||
          d.filename.toLowerCase() === cleanTarget.toLowerCase() ||
          d.filename.toLowerCase() === deliverableOrId.toLowerCase()
      ) || null;

      if (!item) {
        // Create an on-the-fly deliverable item if it's a newly generated filename or raw ID
        let cleanName = deliverableOrId;
        if (cleanName.startsWith('/api/files/')) {
          cleanName = cleanName.replace('/api/files/', '');
        }
        
        let ext = 'docx';
        if (cleanName.includes('.')) {
          ext = cleanName.split('.').pop()?.toLowerCase() || 'docx';
        }
        
        const type = (['docx', 'xlsx', 'pptx', 'py', 'sql', 'html', 'json', 'ts', 'sh'].includes(ext) ? ext : 'docx') as any;
        const displayFilename = cleanName.includes('.') ? cleanName : `${cleanName}.${type}`;

        item = {
          id: cleanTarget || `deliv-dyn-${Date.now()}`,
          filename: displayFilename,
          type,
          // Unknown until the backend reports real metadata — never fabricate it.
          size_bytes: 0,
          size_formatted: '—',
          source_scenario: 'Live Document Workspace',
          source_requirement: 'Refinery AI Output',
          generating_model: 'Sovereign Engine',
          generated_timestamp: new Date().toLocaleTimeString(),
          sha256_hash: 'unavailable',
          summary: `Interactive document generated live by Sovereign Agent: ${displayFilename}`,
          key_metrics: [
            { label: 'Status', value: 'ACTIVE_EDIT' },
            { label: 'Air-Gap Compliance', value: 'NOT VERIFIED' },
            { label: 'Format', value: ext.toUpperCase() },
          ],
          // No invented source references: a citation is only present when the
          // server supplied one for this document.
          sop_citations: [],
        };
      }
    } else {
      item = deliverableOrId;
    }

    const activeId = item ? normalizeFileId(item.id) : '';
    set({
      isOpen: true,
      activeDeliverable: item,
      activeTab: 'editor',
      hasUnsavedChanges: activeId ? Boolean(get().dirtyIds[activeId]) : false,
      isSaving: false,
      saveError: null,
    });
  },

  closeCanvas: () => {
    set({ isOpen: false, isExpanded: false });
  },

  toggleExpand: () => {
    set((state) => ({ isExpanded: !state.isExpanded }));
  },

  setActiveTab: (tab: CanvasTab) => {
    set({ activeTab: tab });
  },

  hydrateContent: (id: string, content: any) => {
    const cleanId = normalizeFileId(id);
    if (!cleanId) return;
    set((state) => ({
      editedContent: {
        ...state.editedContent,
        [cleanId]: { ...(state.editedContent[cleanId] || {}), ...content },
      },
    }));
  },

  updateEditedContent: (id: string, content: any) => {
    const cleanId = normalizeFileId(id);
    if (!cleanId) return;

    set((state) => ({
      editedContent: {
        ...state.editedContent,
        [cleanId]: { ...(state.editedContent[cleanId] || {}), ...content },
      },
      dirtyIds: { ...state.dirtyIds, [cleanId]: true },
      hasUnsavedChanges: true,
    }));

    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer);
    }
    autoSaveTimer = setTimeout(() => {
      autoSaveTimer = null;
      void get().saveChanges(cleanId);
    }, AUTOSAVE_DEBOUNCE_MS);
  },

  clearSaveError: () => set({ saveError: null }),

  renameActiveDeliverable: async (newName: string) => {
    const active = get().activeDeliverable;
    if (!active || !newName.trim()) return;
    const cleanName = newName.trim();
    
    // Update local active deliverable
    set({
      activeDeliverable: {
        ...active,
        filename: cleanName
      }
    });

    // Sync in global deliverable store and backend
    await useDeliverableStore.getState().renameDeliverable(active.id, cleanName);
  },

  saveChanges: async (id: string) => {
    const cleanId = normalizeFileId(id);
    if (!cleanId) return false;

    // Never stack concurrent saves for the same deliverable
    const alreadyRunning = inflightSaves.get(cleanId);
    if (alreadyRunning) return alreadyRunning;

    const content = get().editedContent[cleanId];
    if (!content || Object.keys(content).length === 0) {
      set({ hasUnsavedChanges: false, saveError: null });
      return true;
    }

    const task = (async (): Promise<boolean> => {
      set({ isSaving: true, saveError: null });

      try {
        const token = useAuthStore.getState().token;
        const res = await apiFetch(`${getApiBase()}/api/files/${encodeURIComponent(cleanId)}/content`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ content, editor: 'canvas' }),
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok || data?.status !== 'SUCCESS') {
          throw new Error(data?.detail || `Backend rejected the canvas save (HTTP ${res.status}).`);
        }

        const sizeBytes = typeof data.size_bytes === 'number' ? data.size_bytes : undefined;
        const sizeFormatted = sizeBytes ? formatBytes(sizeBytes) : undefined;

        useDeliverableStore.getState().applyServerMetadata(cleanId, {
          sha256_hash: data.sha256_hash || undefined,
          size_bytes: sizeBytes,
          size_formatted: sizeFormatted,
          verification_status: data.verification_status || undefined,
        });

        const active = get().activeDeliverable;
        if (active && normalizeFileId(active.id) === cleanId) {
          set({
            activeDeliverable: {
              ...active,
              sha256_hash: data.sha256_hash || active.sha256_hash,
              size_bytes: sizeBytes ?? active.size_bytes,
              size_formatted: sizeFormatted || active.size_formatted,
              verification_status: data.verification_status || active.verification_status,
            },
          });
        }

        set((state) => {
          const dirtyIds = { ...state.dirtyIds, [cleanId]: false };
          return {
            isSaving: false,
            saveError: null,
            lastSavedAt: new Date().toISOString(),
            dirtyIds,
            hasUnsavedChanges: Object.values(dirtyIds).some(Boolean),
          };
        });

        if (data.reverification_required) {
          console.warn(
            `[CANVAS] ${cleanId} re-opened for verification after edit (was ${data.previous_verification_status}).`
          );
        }
        return true;
      } catch (err: any) {
        console.error('[CANVAS] Save failed:', err);
        // Never fake success: keep the file dirty and surface the real reason.
        set({
          isSaving: false,
          saveError: err?.message || 'Canvas save failed — backend unreachable.',
        });
        return false;
      }
    })();

    inflightSaves.set(cleanId, task);
    try {
      return await task;
    } finally {
      inflightSaves.delete(cleanId);
    }
  },
}));
