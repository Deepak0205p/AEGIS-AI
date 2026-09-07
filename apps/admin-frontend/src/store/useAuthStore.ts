import { create } from 'zustand';

export interface AuthUser {
  username: string;
  role: string;
  permissions: string[];
  auth_method?: string;
  cert_serial?: string;
  organization?: string;
  ou?: string;
  full_name?: string;
  department?: string;
  expires_at?: number;
}

export interface CRLStatus {
  status: string;
  root_ca: string;
  total_revoked: number;
  last_updated: string;
  next_update: string;
  revoked_certificates: Array<{
    serial_number: string;
    revoked_at: string;
    reason: string;
  }>;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  authMethod: 'PKI_SMARTCARD' | 'INTRANET_LDAP' | 'LOCAL' | null;
  error: string | null;

  // Actions
  loginWithCert: (certPem: string, pin?: string) => Promise<boolean>;
  loginWithLdap: (username: string, password: string) => Promise<boolean>;
  loginWithStandard: (username: string, password: string) => Promise<boolean>;
  fetchCurrentUser: () => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  initializeAuth: () => Promise<void>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,
  authMethod: null,
  error: null,

  clearError: () => set({ error: null }),

  initializeAuth: async () => {
    if (typeof window === 'undefined') return;
    
    set({ isLoading: true });
    const savedToken = localStorage.getItem('reveal_auth_token');
    const savedMethod = localStorage.getItem('reveal_auth_method') as any;
    const savedUserStr = localStorage.getItem('reveal_user');

    if (!savedToken) {
      set({ token: null, user: null, isAuthenticated: false, isLoading: false, authMethod: null });
      return;
    }

    // Immediately restore cached user to eliminate loading delays / flicker
    if (savedUserStr) {
      try {
        const cachedUser = JSON.parse(savedUserStr);
        set({
          token: savedToken,
          user: cachedUser,
          isAuthenticated: true,
          authMethod: savedMethod || 'LOCAL',
        });
      } catch (e) {}
    }

    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: {
          Authorization: `Bearer ${savedToken}`,
        },
      });

      if (res.ok) {
        const userData: AuthUser = await res.json();
        if (typeof window !== 'undefined') {
          localStorage.setItem('reveal_user', JSON.stringify(userData));
        }
        set({
          token: savedToken,
          user: userData,
          isAuthenticated: true,
          isLoading: false,
          authMethod: savedMethod || (userData.auth_method === 'PKI_X509' ? 'PKI_SMARTCARD' : 'INTRANET_LDAP'),
          error: null,
        });
      } else {
        // Token invalid or expired
        localStorage.removeItem('reveal_auth_token');
        localStorage.removeItem('reveal_auth_method');
        localStorage.removeItem('reveal_user');
        set({ token: null, user: null, isAuthenticated: false, isLoading: false, authMethod: null });
      }
    } catch (err) {
      console.warn('Backend offline or auth check failed during initialization:', err);
      // If offline, preserve cached user and token in air-gapped sovereign mode
      set({ isLoading: false });
    }
  },

  loginWithCert: async (certPem: string, pin?: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/cert-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ certificate_pem: certPem, pin: pin || undefined }),
      });

      const data = await res.json();

      if (!res.ok) {
        const errMsg = data.detail || 'SmartCard / Certificate validation failed.';
        set({ error: errMsg, isLoading: false });
        return false;
      }

      const token = data.access_token;
      const user = data.user;

      if (typeof window !== 'undefined') {
        localStorage.setItem('reveal_auth_token', token);
        localStorage.setItem('reveal_auth_method', 'PKI_SMARTCARD');
      }

      set({
        token,
        user,
        isAuthenticated: true,
        isLoading: false,
        authMethod: 'PKI_SMARTCARD',
        error: null,
      });
      return true;
    } catch (err: any) {
      const msg = err.message || 'Network error connecting to Sovereign Auth Gateway.';
      set({ error: msg, isLoading: false });
      return false;
    }
  },

  loginWithLdap: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/ldap-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        const errMsg = data.detail || 'Active Directory / LDAP authentication failed.';
        set({ error: errMsg, isLoading: false });
        return false;
      }

      const token = data.access_token;
      const user = data.user;

      if (typeof window !== 'undefined') {
        localStorage.setItem('reveal_auth_token', token);
        localStorage.setItem('reveal_auth_method', 'INTRANET_LDAP');
      }

      set({
        token,
        user,
        isAuthenticated: true,
        isLoading: false,
        authMethod: 'INTRANET_LDAP',
        error: null,
      });
      return true;
    } catch (err: any) {
      const msg = err.message || 'Network error connecting to Intranet LDAP Gateway.';
      set({ error: msg, isLoading: false });
      return false;
    }
  },

  loginWithStandard: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        const errMsg = data.detail || 'Standard authentication failed.';
        set({ error: errMsg, isLoading: false });
        return false;
      }

      const token = data.token || data.access_token;
      const user = data.user;

      // Restrict access: Strictly verify the user's role from database
      const userRole = (user?.role || '').trim().toUpperCase();
      const allowedAdminRoles = ['SUPER_ADMIN', 'ADMIN', 'PLANT_SECURITY_OFFICER'];
      if (!allowedAdminRoles.includes(userRole)) {
        set({
          error: `Access Denied: Account with role '${user?.role || 'UNKNOWN'}' is not authorized. The Admin Observatory requires an Administrator role.`,
          isLoading: false
        });
        return false;
      }

      if (typeof window !== 'undefined') {
        localStorage.setItem('reveal_auth_token', token);
        localStorage.setItem('reveal_auth_method', 'LOCAL');
        if (user) {
          localStorage.setItem('reveal_user', JSON.stringify(user));
        }
        document.cookie = `reveal_auth_token=${encodeURIComponent(token)}; path=/; max-age=86400; SameSite=Lax`;
      }

      set({
        token,
        user,
        isAuthenticated: true,
        isLoading: false,
        authMethod: 'LOCAL',
        error: null,
      });
      return true;
    } catch (err: any) {
      const msg = err.message || 'Network error connecting to Auth Gateway.';
      set({ error: msg, isLoading: false });
      return false;
    }
  },

  fetchCurrentUser: async () => {
    const token = get().token || (typeof window !== 'undefined' ? localStorage.getItem('reveal_auth_token') : null);
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        const userData = data.user || data;
        const userRole = (userData?.role || '').trim().toUpperCase();
        const allowedAdminRoles = ['SUPER_ADMIN', 'ADMIN', 'PLANT_SECURITY_OFFICER'];
        if (!allowedAdminRoles.includes(userRole)) {
          get().logout();
          return;
        }
        set({ user: userData, isAuthenticated: true });
      } else if (res.status === 401) {
        get().logout();
      }
    } catch (err) {
      console.error('Failed to fetch user:', err);
    }
  },

  logout: async () => {
    const token = get().token || (typeof window !== 'undefined' ? localStorage.getItem('reveal_auth_token') : null);
    if (token) {
      try {
        await fetch(`${API_BASE}/api/v1/auth/logout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch (err) {
        console.warn('Logout notification error:', err);
      }
    }

    if (typeof window !== 'undefined') {
      localStorage.removeItem('reveal_auth_token');
      localStorage.removeItem('reveal_auth_method');
      localStorage.removeItem('reveal_user');
      document.cookie = 'reveal_auth_token=; path=/; max-age=0; SameSite=Lax';
    }

    set({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      authMethod: null,
      error: null,
    });

    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  },
}));
