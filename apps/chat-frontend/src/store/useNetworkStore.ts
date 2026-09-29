import { create } from 'zustand';
import { getApiBase } from '@/lib/apiBase';
import { useAuthStore } from './useAuthStore';
import { apiFetch } from '@/lib/apiFetch';

export type DeploymentMode = 'STANDALONE_LOCAL' | 'LAN_OPTION_A' | 'HOTSPOT_OPTION_B';

export interface NetworkInterface {
  interface: string;
  ip: string;
  loopback: boolean;
}

export interface ConnectedClient {
  ip: string;
  port?: number;
  /** The OS exposes no connect timestamp; null means "not tracked". */
  connected_at: string | null;
  last_seen: string;
}

/** Builds the URL a second device can actually open, from the live host address. */
function buildFrontendUrl(hostIp: string, loopbackOnly: boolean): string {
  if (typeof window === 'undefined') return '';
  if (!hostIp || loopbackOnly) return '';
  const port = window.location.port || '3000';
  return `http://${hostIp}:${port}`;
}

interface NetworkState {
  /** What the operator configured (echoed back by the backend). */
  deploymentMode: DeploymentMode;
  /** What the host actually looks like right now. */
  detectedMode: DeploymentMode | null;
  modeSatisfied: boolean;
  hostIp: string;
  loopbackOnly: boolean;
  port: number | null;
  /** Real, openable URL for the frontend on this LAN (empty when loopback-only). */
  frontendUrl: string;
  interfaces: NetworkInterface[];
  connectedClients: ConnectedClient[];
  externalEgressSockets: number;
  localhostSockets: number;
  lanSockets: number;
  isHotspotActive: boolean;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;

  // Actions
  fetchNetworkStatus: () => Promise<boolean>;
  setDeploymentMode: (mode: DeploymentMode) => Promise<boolean>;
  setHostIp: (ip: string) => void;
  setConnectedClients: (clients: ConnectedClient[]) => void;
}

export const useNetworkStore = create<NetworkState>((set, get) => ({
  // Nothing is assumed: the host address and topology come from the backend.
  deploymentMode: 'STANDALONE_LOCAL',
  detectedMode: null,
  modeSatisfied: false,
  hostIp: '',
  loopbackOnly: true,
  port: null,
  frontendUrl: '',
  interfaces: [],
  connectedClients: [],
  externalEgressSockets: 0,
  localhostSockets: 0,
  lanSockets: 0,
  isHotspotActive: false,
  isLoading: false,
  error: null,
  lastUpdated: null,

  fetchNetworkStatus: async () => {
    if (typeof window === 'undefined') return false;
    set({ isLoading: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      const res = await apiFetch(`${getApiBase()}/api/network-status`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      const data = await res.json().catch(() => null);
      if (!res.ok || !data) {
        throw new Error(data?.detail || `Network status request failed (HTTP ${res.status}).`);
      }

      const hostIp: string = data?.host_ip || '';
      const loopbackOnly = Boolean(data?.loopback_only);
      const detected = (data?.detected_mode as DeploymentMode) || null;

      set({
        deploymentMode: (data?.configured_mode as DeploymentMode) || 'STANDALONE_LOCAL',
        detectedMode: detected,
        modeSatisfied: Boolean(data?.mode_satisfied),
        hostIp,
        loopbackOnly,
        port: typeof data?.port === 'number' ? data.port : null,
        frontendUrl: buildFrontendUrl(hostIp, loopbackOnly),
        interfaces: Array.isArray(data?.interfaces) ? data.interfaces : [],
        connectedClients: Array.isArray(data?.connected_clients) ? data.connected_clients : [],
        externalEgressSockets: Number(data?.external_egress_sockets) || 0,
        localhostSockets: Number(data?.localhost_sockets) || 0,
        lanSockets: Number(data?.lan_sockets) || 0,
        isHotspotActive: detected === 'HOTSPOT_OPTION_B',
        isLoading: false,
        lastUpdated: new Date().toISOString(),
      });
      return true;
    } catch (err: any) {
      set({
        isLoading: false,
        error: err?.message || 'Network status unavailable from the backend.',
      });
      return false;
    }
  },

  setDeploymentMode: async (mode: DeploymentMode) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const res = await apiFetch(
        `${getApiBase()}/api/network-status/mode?mode=${encodeURIComponent(mode)}`,
        {
          method: 'POST',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        }
      );
      const data = await res.json().catch(() => null);
      if (!res.ok || !data) {
        throw new Error(data?.detail || `Could not set deployment mode (HTTP ${res.status}).`);
      }
      // Re-read the real status so a mismatch stays visible in the UI.
      return await get().fetchNetworkStatus();
    } catch (err: any) {
      set({ error: err?.message || `Could not set deployment mode to ${mode}.` });
      return false;
    }
  },

  setHostIp: (ip: string) =>
    set({ hostIp: ip, frontendUrl: buildFrontendUrl(ip, !ip) }),

  setConnectedClients: (connectedClients) => set({ connectedClients }),
}));
