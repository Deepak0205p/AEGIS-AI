import { useAuthStore } from '@/store/useAuthStore';
import { getApiBase } from '@/lib/apiBase';

/**
 * Authenticated fetch for every backend call.
 *
 * The backend requires a signed bearer token on all /api routes, so no caller
 * may use the bare `fetch()` for API traffic. This helper:
 *   - resolves relative paths against the configured API base,
 *   - attaches the session token,
 *   - clears the expired session and returns to the login screen on 401.
 *
 * It returns the raw `Response` so existing `res.ok` call sites keep working.
 */
export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

function currentToken(): string | null {
  const fromStore = useAuthStore.getState().token;
  if (fromStore) return fromStore;
  if (typeof window !== 'undefined') {
    return window.localStorage.getItem('mrpl_auth_token');
  }
  return null;
}

export async function apiFetch(urlOrPath: string, options: RequestInit = {}): Promise<Response> {
  const url = urlOrPath.startsWith('http')
    ? urlOrPath
    : `${getApiBase()}${urlOrPath.startsWith('/') ? urlOrPath : `/${urlOrPath}`}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  const token = currentToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    // The token is missing, expired or signed with a rotated secret: drop the
    // local session instead of leaving a half-authenticated UI on screen.
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
  }

  return response;
}

/** Convenience wrapper that parses a JSON response and throws ApiError on failure. */
export async function apiJson<T = any>(urlOrPath: string, options: RequestInit = {}): Promise<T> {
  const response = await apiFetch(urlOrPath, options);
  const isJson = (response.headers.get('content-type') || '').includes('application/json');
  const data = isJson ? await response.json().catch(() => ({})) : await response.text();
  if (!response.ok) {
    const detail = (data as any)?.detail || (data as any)?.message || `Request failed (HTTP ${response.status})`;
    throw new ApiError(detail, response.status, data);
  }
  return data as T;
}

export default apiFetch;
