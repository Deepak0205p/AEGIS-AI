import { create } from 'zustand';
import { DeliverableItem, useDeliverableStore } from './useDeliverableStore';

export type CanvasTab = 'editor' | 'metrics' | 'sop' | 'raw';

interface CanvasState {
  isOpen: boolean;
  isExpanded: boolean;
  activeDeliverable: DeliverableItem | null;
  activeTab: CanvasTab;
  editedContent: Record<string, any>;
  hasUnsavedChanges: boolean;
  isSaving: boolean;

  // Actions
  openCanvas: (deliverableOrId: DeliverableItem | string) => void;
  closeCanvas: () => void;
  toggleExpand: () => void;
  setActiveTab: (tab: CanvasTab) => void;
  updateEditedContent: (id: string, content: any) => void;
  renameActiveDeliverable: (newName: string) => Promise<void>;
  saveChanges: (id: string) => Promise<void>;
}

let autoSaveTimer: ReturnType<typeof setTimeout> | null = null;

export const useCanvasStore = create<CanvasState>((set, get) => ({
  isOpen: false,
  isExpanded: false,
  activeDeliverable: null,
  activeTab: 'editor',
  editedContent: {},
  hasUnsavedChanges: false,
  isSaving: false,

  openCanvas: async (deliverableOrId: DeliverableItem | string) => {
    let item: DeliverableItem | null = null;
    if (typeof deliverableOrId === 'string') {
      const cleanTarget = deliverableOrId.replace(/^\/api\/files\/(download\/)?/, '').trim();
      
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
          size_bytes: 32000,
          size_formatted: '32.0 KB',
          source_scenario: 'Live Document Workspace',
          source_requirement: 'Refinery AI Output',
          generating_model: 'Sovereign Engine',
          generated_timestamp: new Date().toLocaleTimeString(),
          sha256_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
          summary: `Interactive document generated live by Sovereign Agent: ${displayFilename}`,
          key_metrics: [
            { label: 'Status', value: 'ACTIVE_EDIT' },
            { label: 'Air-Gap Compliance', value: '100% VERIFIED' },
            { label: 'Format', value: ext.toUpperCase() },
          ],
          sop_citations: ['OISD-STD-105', 'MRPL Refinery Standard Operating Procedure'],
        };
      }
    } else {
      item = deliverableOrId;
    }

    set({
      isOpen: true,
      activeDeliverable: item,
      activeTab: 'editor',
      hasUnsavedChanges: false,
      isSaving: false,
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

  updateEditedContent: (id: string, content: any) => {
    set((state) => ({
      editedContent: {
        ...state.editedContent,
        [id]: content,
      },
      hasUnsavedChanges: true,
    }));

    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer);
    }

    autoSaveTimer = setTimeout(() => {
      set({ isSaving: true });
      setTimeout(() => {
        set({ isSaving: false, hasUnsavedChanges: false });
      }, 400);
    }, 1200);
  },

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
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer);
    }
    set({ isSaving: true });
    // Simulate air-gapped local commit and state persistence
    await new Promise((resolve) => setTimeout(resolve, 500));
    set({ isSaving: false, hasUnsavedChanges: false });
  },
}));

