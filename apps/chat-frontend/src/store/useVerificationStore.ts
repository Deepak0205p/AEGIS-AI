import { create } from 'zustand';
import { useDeliverableStore } from './useDeliverableStore';
import { useAuthStore } from './useAuthStore';

export interface PendingVerificationItem {
  file_id: string;
  chat_id: string;
  filename: string;
  file_type: string;
  verification_status: 'PENDING_STAGE_1' | 'PENDING_STAGE_2' | 'VERIFIED' | 'REJECTED';
  stage_1_verifier?: string | null;
  stage_1_at?: string | null;
  stage_1_notes?: string | null;
  stage_2_verifier?: string | null;
  stage_2_at?: string | null;
  stage_2_notes?: string | null;
  rejected_by?: string | null;
  rejected_at?: string | null;
  reject_reason?: string | null;
  created_at: string;
  download_url: string;
}

interface VerificationState {
  isModalOpen: boolean;
  activeItem: PendingVerificationItem | null;
  pendingItems: PendingVerificationItem[];
  stage1Count: number;
  stage2Count: number;
  totalPending: number;
  isLoading: boolean;
  selectedFilter: 'ALL' | 'PENDING_STAGE_1' | 'PENDING_STAGE_2' | 'REJECTED' | 'VERIFIED';
  isActing: boolean;

  // Actions
  openVerificationModal: (item?: PendingVerificationItem) => void;
  closeVerificationModal: () => void;
  setSelectedFilter: (filter: 'ALL' | 'PENDING_STAGE_1' | 'PENDING_STAGE_2' | 'REJECTED' | 'VERIFIED') => void;
  fetchPendingVerifications: () => Promise<void>;
  approveStage1: (fileId: string, notes?: string) => Promise<boolean>;
  approveStage2: (fileId: string, notes?: string) => Promise<boolean>;
  rejectItem: (fileId: string, reason: string) => Promise<boolean>;
  editAndApprove: (fileId: string, stage: 1 | 2, filename?: string, notes?: string) => Promise<boolean>;
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

export const useVerificationStore = create<VerificationState>((set, get) => ({
  isModalOpen: false,
  activeItem: null,
  pendingItems: [],
  stage1Count: 0,
  stage2Count: 0,
  totalPending: 0,
  isLoading: false,
  selectedFilter: 'ALL',
  isActing: false,

  openVerificationModal: (item) => {
    set({ isModalOpen: true, activeItem: item || null });
    get().fetchPendingVerifications();
  },

  closeVerificationModal: () => {
    set({ isModalOpen: false, activeItem: null });
  },

  setSelectedFilter: (filter) => {
    set({ selectedFilter: filter });
  },

  fetchPendingVerifications: async () => {
    set({ isLoading: true });
    const host = getApiHost();
    const user = useAuthStore.getState().user;
    const roleParam = user?.role ? `?role=${encodeURIComponent(user.role)}` : '';

    try {
      const res = await fetch(`http://${host}:8000/api/verification/pending${roleParam}`);
      if (res.ok) {
        const data = await res.json();
        set({
          pendingItems: data.items || [],
          totalPending: data.total_pending || 0,
          stage1Count: data.stage1_pending || 0,
          stage2Count: data.stage2_pending || 0,
          isLoading: false
        });
      }
    } catch (err) {
      console.warn('[useVerificationStore] fetch pending error:', err);
      set({ isLoading: false });
    }
  },

  approveStage1: async (fileId: string, notes: string = '') => {
    set({ isActing: true });
    const host = getApiHost();
    const user = useAuthStore.getState().user;
    const verifierName = user?.full_name || user?.username || 'Process Lead';

    try {
      const res = await fetch(`http://${host}:8000/api/verification/${fileId}/stage1/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          verifier: verifierName,
          notes: notes || 'Approved in Step 1 (Process & Quality Check)',
          role: user?.role || 'PROCESS_LEAD'
        })
      });

      if (res.ok) {
        // Refresh local lists and deliverables store
        await get().fetchPendingVerifications();
        await useDeliverableStore.getState().fetchDiskDeliverables();
        set({ isActing: false });
        return true;
      }
    } catch (e) {
      console.error('[useVerificationStore] approveStage1 failed:', e);
    }
    set({ isActing: false });
    return false;
  },

  approveStage2: async (fileId: string, notes: string = '') => {
    set({ isActing: true });
    const host = getApiHost();
    const user = useAuthStore.getState().user;
    const verifierName = user?.full_name || user?.username || 'Refinery Admin';

    try {
      const res = await fetch(`http://${host}:8000/api/verification/${fileId}/stage2/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          verifier: verifierName,
          notes: notes || 'Final Step 2 Approval & Compliance Sign-Off',
          role: user?.role || 'SUPER_ADMIN'
        })
      });

      if (res.ok) {
        await get().fetchPendingVerifications();
        await useDeliverableStore.getState().fetchDiskDeliverables();
        set({ isActing: false });
        return true;
      }
    } catch (e) {
      console.error('[useVerificationStore] approveStage2 failed:', e);
    }
    set({ isActing: false });
    return false;
  },

  rejectItem: async (fileId: string, reason: string) => {
    set({ isActing: true });
    const host = getApiHost();
    const user = useAuthStore.getState().user;
    const rejectedBy = user?.full_name || user?.username || 'Reviewer';

    try {
      const res = await fetch(`http://${host}:8000/api/verification/${fileId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rejected_by: rejectedBy,
          reason: reason || 'Document requirements or quality parameters not satisfied',
          role: user?.role
        })
      });

      if (res.ok) {
        await get().fetchPendingVerifications();
        await useDeliverableStore.getState().fetchDiskDeliverables();
        set({ isActing: false });
        return true;
      }
    } catch (e) {
      console.error('[useVerificationStore] rejectItem failed:', e);
    }
    set({ isActing: false });
    return false;
  },

  editAndApprove: async (fileId: string, stage: 1 | 2, filename?: string, notes?: string) => {
    set({ isActing: true });
    const host = getApiHost();
    const user = useAuthStore.getState().user;
    const verifierName = user?.full_name || user?.username || 'Reviewer';

    try {
      const res = await fetch(`http://${host}:8000/api/verification/${fileId}/edit-and-approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          verifier: verifierName,
          notes: notes || `Edited and approved in Step ${stage}`,
          stage,
          filename,
          role: user?.role
        })
      });

      if (res.ok) {
        await get().fetchPendingVerifications();
        await useDeliverableStore.getState().fetchDiskDeliverables();
        set({ isActing: false });
        return true;
      }
    } catch (e) {
      console.error('[useVerificationStore] editAndApprove failed:', e);
    }
    set({ isActing: false });
    return false;
  }
}));
