import { create } from 'zustand';
import { DeploymentMode } from '@/types/sovereignty';
import { getApiHost } from '@/lib/apiBase';
import { apiFetch } from '@/lib/api';

export type { DeploymentMode };

export interface SocketRecord {
  id: string;
  pid: number;
  process_name: string;
  local_address: string;
  remote_address: string;
  tier: 'LOCALHOST' | 'LAN_HOTSPOT' | 'EXTERNAL_WAN';
  status: string;
  security_verdict: 'PERMITTED' | 'BREACH_FLAGGED' | 'BLOCKED_BREACH';
}

export interface AuditLogEntry {
  sequence: number;
  timestamp: string;
  event: string;
  deployment_mode?: string;
  localhost_sockets?: number;
  lan_hotspot_sockets?: number;
  external_sockets?: number;
  external_packets?: number | null;
  username?: string;
  role?: string;
  details?: string;
  risk_level?: string;
  row_id?: number;
  block_hash: string;
  prev_hash: string;
  verified: boolean;
}

export interface SovereigntyMetrics {
  localhost_sockets: number;
  lan_hotspot_sockets: number;
  external_sockets: number;
  /**
   * Packet counters are null on deployments without packet counting. Null must
   * stay null: rendering it as 0 would claim traffic was measured.
   */
  localhost_packets: number | null;
  lan_hotspot_packets: number | null;
  external_packets: number | null;
  external_bytes: number | null;
  total_packets_sniffed: number | null;
  verdict: string;
  daemon_heartbeat_hz: number;
  last_updated: string;
}

interface SovereigntyState {
  deploymentMode: DeploymentMode;
  hostIp: string;
  port: number;
  metrics: SovereigntyMetrics;
  sockets: SocketRecord[];
  auditLogs: AuditLogEntry[];
  isVerifyingChain: boolean;
  chainVerificationStatus: 'unverified' | 'valid' | 'tampered';
  /** Real failure reasons — an unreachable backend is NOT a valid chain. */
  chainError: string | null;
  certificateError: string | null;
  networkError: string | null;
  /** How the backend described the certificate (e.g. static bootstrap vs live chain). */
  chainProvenance: string | null;
  clearSovereigntyErrors: () => void;

  // Actions
  setDeploymentMode: (mode: DeploymentMode) => Promise<void>;
  updateMetrics: (newMetrics: Partial<SovereigntyMetrics>) => void;
  setSockets: (sockets: SocketRecord[]) => void;
  setAuditLogs: (logs: AuditLogEntry[]) => void;
  verifyChainIntegrity: () => Promise<void>;
  exportAuditCertificate: () => Promise<boolean>;
  fetchNetworkStatus: () => Promise<void>;
}

export const useSovereigntyStore = create<SovereigntyState>((set, get) => ({
  deploymentMode: 'STANDALONE_LOCAL',
  hostIp: '127.0.0.1',
  port: 8000,
  metrics: {
    localhost_sockets: 0,
    lan_hotspot_sockets: 0,
    external_sockets: 0,
    // Unknown until measured - never pre-filled with a zero.
    localhost_packets: null,
    lan_hotspot_packets: null,
    external_packets: null,
    external_bytes: null,
    total_packets_sniffed: null,
    // Nothing is known until the live audit stream reports it.
    verdict: 'UNKNOWN - awaiting live telemetry',
    daemon_heartbeat_hz: 0,
    last_updated: ''
  },
  sockets: [],
  auditLogs: [],
  isVerifyingChain: false,
  chainVerificationStatus: 'unverified',
  chainError: null,
  certificateError: null,
  networkError: null,
  chainProvenance: null,

  clearSovereigntyErrors: () => set({ chainError: null, certificateError: null, networkError: null }),

  fetchNetworkStatus: async () => {
    try {
      const res = await apiFetch(`/api/network-status`);
      if (res.ok) {
        const data = await res.json();
        set({
          hostIp: data.host_ip || getApiHost(),
          port: data.port || 8000,
          deploymentMode: (data.deployment_mode as DeploymentMode) || 'STANDALONE_LOCAL'
        });
      }

      // Fetch live audit chain
      const logsRes = await apiFetch(`/api/sovereignty/logs`);
      if (logsRes.ok) {
        const logsData = await logsRes.json();
        if (logsData.success && logsData.logs) {
          set({ auditLogs: logsData.logs });
        }
      }
    } catch {
      // Graceful fallback
    }
  },

  setDeploymentMode: async (mode) => {
    set({ deploymentMode: mode });
    try {
      const res = await apiFetch(`/api/network-status/mode?mode=${mode}`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        set({ hostIp: data.host_ip });
      }
    } catch {
      // Fallback
    }
  },

  updateMetrics: (newMetrics) => set((state) => ({
    metrics: { 
      ...state.metrics, 
      ...newMetrics,
      last_updated: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    }
  })),

  setSockets: (sockets) => set({ sockets }),
  setAuditLogs: (auditLogs) => set({ auditLogs }),

  verifyChainIntegrity: async () => {
    set({ isVerifyingChain: true, chainVerificationStatus: 'unverified', chainError: null });
    try {
      const res = await apiFetch(`/api/sovereignty-audit/export`);
      if (!res.ok) {
        set({
          isVerifyingChain: false,
          chainVerificationStatus: 'unverified',
          chainError: `Audit endpoint returned HTTP ${res.status}. The chain was NOT verified.`,
        });
        return;
      }
      const cert = await res.json();
      const isValid = cert.integrity_verification?.valid === true;
      set({
        isVerifyingChain: false,
        // "valid" means the backend recomputed and re-linked the chain; it is
        // explicitly not an independent external verification.
        chainVerificationStatus: isValid ? 'valid' : 'tampered',
        chainError: isValid ? null : 'The backend reported an invalid chain.',
        chainProvenance: cert.provenance || cert.integrity_verification?.method || null,
      });
      return;
    } catch (err: any) {
      // An unreachable backend is NOT a verified chain — stay unverified.
      set({
        isVerifyingChain: false,
        chainVerificationStatus: 'unverified',
        chainError: err?.message || 'Could not reach the audit endpoint; the chain was not verified.',
      });
    }
  },

  exportAuditCertificate: async () => {
    set({ certificateError: null });
    try {
      const host = getApiHost();
      const res = await apiFetch(`/api/sovereignty-audit/export`);
      if (!res.ok) {
        // Never synthesise a certificate when the signed artefact is unavailable.
        set({ certificateError: `Certificate export failed (HTTP ${res.status}). Nothing was downloaded.` });
        return false;
      }
      const certificateData = await res.json();

      const blob = new Blob([JSON.stringify(certificateData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `MRPL_Sovereignty_Audit_Certificate_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      return true;
    } catch (err: any) {
      set({ certificateError: err?.message || 'Certificate export failed; nothing was downloaded.' });
      return false;
    }
  }
}));