import { create } from 'zustand';
import { useDeliverableStore } from './useDeliverableStore';
import { useAuthStore } from './useAuthStore';
import { apiFetch } from '@/lib/apiFetch';

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
  /** Server-reported reason for the last failed action (empty when none). */
  lastError: string | null;

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

/**
 * Every verification endpoint is role-gated server-side, so requests go through
 * the shared authenticated helper. Failures are surfaced verbatim — a denied or
 * unauthenticated call is never reported as a silent no-op.
 */
async function authFetch(path: string, init?: RequestInit): Promise<Response> {
  return apiFetch(path, init);
}

async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return data?.detail || data?.message || `Request failed (HTTP ${res.status})`;
  } catch {
    return `Request failed (HTTP ${res.status})`;
  }
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
  lastError: null,

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
    set({ isLoading: true, lastError: null });

    try {
      // No role query parameter: the backend derives the role from the token.
      const res = await authFetch('/api/verification/pending');
      if (!res.ok) {
        set({ isLoading: false, lastError: await readError(res) });
        return;
      }
      const data = await res.json();
      set({
        pendingItems: data.items || [],
        totalPending: data.total_pending || 0,
        stage1Count: data.stage1_pending || 0,
        stage2Count: data.stage2_pending || 0,
        isLoading: false
      });
    } catch (err: any) {
      set({ isLoading: false, lastError: err?.message || 'Could not reach the verification service.' });
    }
  },

  approveStage1: async (fileId: string, notes: string = '') => {
    set({ isActing: true, lastError: null });
    const user = useAuthStore.getState().user;
    const verifierName = user?.full_name || user?.username || 'Process Lead';

    try {
      const res = await authFetch(`/api/verification/${fileId}/stage1/approve`, {
        method: 'POST',
        body: JSON.stringify({
          verifier: verifierName,
          notes: notes || 'Approved in Step 1 (Process & Quality Check)'
        })
      });

      if (res.ok) {
        // Refresh local lists and deliverables store
        await get().fetchPendingVerifications();
        await useDeliverableStore.getState().fetchDiskDeliverables();
        set({ isActing: false });
        return true;
      }
      set({ isActing: false, lastError: await readError(res) });
      return false;
    } catch (e: any) {
      set({ isActing: false, lastError: e?.message || 'Approval request failed.' });
      return false;
    }
  },

  approveStage2: async (fileId: string, notes: string = '') => {
    set({ isActing: true, lastError: null });
    const user = useAuthStore.getState().user;
    const verifierName = user?.full_name || user?.username || 'Refinery Admin';

    try {
      const res = await authFetch(`/api/verification/${fileId}/stage2/approve`, {
        method: 'POST',
        body: JSON.stringify({
          verifier: verifierName,
          notes: notes || 'Final Step 2 Approval & Compliance Sign-Off'
        })
      });

      if (res.ok) {
        await get().fetchPendingVerifications();
        await useDeliverableStore.getState().fetchDiskDeliverables();
        set({ isActing: false });
        return true;
      }
      set({ isActing: false, lastError: await readError(res) });
      return false;
    } catch (e: any) {
      set({ isActing: false, lastError: e?.message || 'Approval request failed.' });
      return false;
    }
  },

  rejectItem: async (fileId: string, reason: string) => {
    set({ isActing: true, lastError: null });
    const user = useAuthStore.getState().user;
    const rejectedBy = user?.full_name || user?.username || 'Reviewer';

    try {
      const res = await authFetch(`/api/verification/${fileId}/reject`, {
        method: 'POST',
        body: JSON.stringify({
          rejected_by: rejectedBy,
          reason: reason || 'Document requirements or quality parameters not satisfied'
        })
      });

      if (res.ok) {
        await get().fetchPendingVerifications();
        await useDeliverableStore.getState().fetchDiskDeliverables();
        set({ isActing: false });
        return true;
      }
      set({ isActing: false, lastError: await readError(res) });
      return false;
    } catch (e: any) {
      set({ isActing: false, lastError: e?.message || 'Rejection request failed.' });
      return false;
    }
  },

  editAndApprove: async (fileId: string, stage: 1 | 2, filename?: string, notes?: string) => {
    set({ isActing: true, lastError: null });
    const user = useAuthStore.getState().user;
    const verifierName = user?.full_name || user?.username || 'Reviewer';

    try {
      const res = await authFetch(`/api/verification/${fileId}/edit-and-approve`, {
        method: 'POST',
        body: JSON.stringify({
          verifier: verifierName,
          notes: notes || `Edited and approved in Step ${stage}`,
          stage,
          filename
        })
      });

      if (res.ok) {
        await get().fetchPendingVerifications();
        await useDeliverableStore.getState().fetchDiskDeliverables();
        set({ isActing: false });
        return true;
      }
      set({ isActing: false, lastError: await readError(res) });
      return false;
    } catch (e: any) {
      set({ isActing: false, lastError: e?.message || 'Edit-and-approve request failed.' });
      return false;
    }
  }
}));
