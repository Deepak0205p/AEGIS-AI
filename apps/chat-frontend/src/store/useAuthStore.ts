'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UserProfile {
  id?: number;
  username: string;
  role: string;
  full_name?: string;
  department?: string;
  auth_method?: string;
  cert_serial?: string;
  can_verify?: boolean;
}

interface AuthState {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  lastActive: number | null;
  initialize: () => void;
  login: (user: UserProfile, token: string) => void;
  logout: () => void;
  setUser: (user: UserProfile | null) => void;
  touchSession: () => void;
}

// Enterprise Session Timeout Invariant (ISA/IEC 62443: 8 hours absolute max or 45 mins idle)
const IDLE_TIMEOUT_MS = 45 * 60 * 1000;

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,
      lastActive: null,
      initialize: () => {
        if (typeof window === 'undefined') return;
        try {
          const token = localStorage.getItem('mrpl_auth_token');
          const userStr = localStorage.getItem('mrpl_user');
          const lastActiveStr = localStorage.getItem('mrpl_auth_last_active');
          const lastActive = lastActiveStr ? parseInt(lastActiveStr, 10) : null;

          if (token && userStr) {
            if (lastActive && Date.now() - lastActive > IDLE_TIMEOUT_MS) {
              // Invalidate expired session
              get().logout();
              return;
            }
            const user = JSON.parse(userStr);
            set({
              user,
              token,
              isAuthenticated: true,
              isLoading: false,
              lastActive: Date.now()
            });
            localStorage.setItem('mrpl_auth_last_active', String(Date.now()));
            return;
          }
        } catch (e) {
          console.error('Failed to restore auth session from browser storage:', e);
        }
        set({ user: null, token: null, isAuthenticated: false, isLoading: false, lastActive: null });
      },
      login: (user, token) => {
        if (typeof window !== 'undefined') {
          try {
            localStorage.setItem('mrpl_auth_token', token);
            localStorage.setItem('mrpl_user', JSON.stringify(user));
            localStorage.setItem('mrpl_auth_last_active', String(Date.now()));
            // Set cookie for browser session persistence
            document.cookie = `mrpl_auth_token=${encodeURIComponent(token)}; path=/; max-age=86400; SameSite=Lax`;
          } catch (e) {
            console.error('Failed to save auth to browser storage:', e);
          }
        }
        set({
          user,
          token,
          isAuthenticated: true,
          isLoading: false,
          lastActive: Date.now()
        });
      },
      logout: () => {
        if (typeof window !== 'undefined') {
          try {
            localStorage.removeItem('mrpl_auth_token');
            localStorage.removeItem('mrpl_user');
            localStorage.removeItem('mrpl_auth_last_active');
            document.cookie = 'mrpl_auth_token=; path=/; max-age=0; SameSite=Lax';
          } catch (e) {
            console.error('Failed to clear browser storage:', e);
          }
        }
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          lastActive: null
        });
      },
      setUser: (user) => {
        if (typeof window !== 'undefined' && user) {
          try {
            localStorage.setItem('mrpl_user', JSON.stringify(user));
            localStorage.setItem('mrpl_auth_last_active', String(Date.now()));
          } catch (e) {}
        }
        set({ user, isAuthenticated: !!user, lastActive: Date.now() });
      },
      touchSession: () => {
        const state = get();
        if (state.isAuthenticated) {
          const now = Date.now();
          if (typeof window !== 'undefined') {
            try {
              localStorage.setItem('mrpl_auth_last_active', String(now));
            } catch (e) {}
          }
          set({ lastActive: now });
        }
      }
    }),
    {
      name: 'mrpl-auth-storage',
      onRehydrateStorage: () => {
        return (state) => {
          if (state) {
            state.initialize();
          } else {
            useAuthStore.setState({ isLoading: false });
          }
        };
      }
    }
  )
);

