/**
 * Single source of truth for resolving the backend (FastAPI :8000) base URL.
 *
 * Every frontend call — REST fetch, `lib/api.ts` wrapper, and WebSocket
 * connections — must resolve the backend through this module instead of
 * hard-coding `127.0.0.1`, `localhost`, or a relative path. This keeps the
 * app working identically when opened from localhost, a LAN IP, or the
 * air-gapped Wi-Fi hotspot: the host that served the page is the host that
 * runs the backend.
 *
 * Priority order:
 *   1. `NEXT_PUBLIC_API_URL` env override (baked in at build time), if present.
 *   2. `<page hostname>:8000` — hostname taken from `window.location` and
 *      sanitised before being placed into a URL.
 *   3. `127.0.0.1:8000` — SSR / sanitisation-failure fallback only.
 */

const FALLBACK_HOST = '127.0.0.1';
const BACKEND_PORT = 8000;

/** Sanitised hostname of the machine serving the frontend (and backend). */
export function getApiHost(): string {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    // Only allow localhost / IPv4 / dotted hostnames made of [a-zA-Z0-9.-].
    // Rejects anything that could break out of the URL (spaces, '/', '@', ...).
    if (/^[a-zA-Z0-9.-]+$/.test(hostname)) {
      return hostname;
    }
  }
  return FALLBACK_HOST;
}

/** Absolute HTTP base URL of the backend REST API, no trailing slash. */
export function getApiBase(): string {
  const override = process.env.NEXT_PUBLIC_API_URL;
  if (override) return override.replace(/\/+$/, '');
  return `http://${getApiHost()}:${BACKEND_PORT}`;
}

/** Absolute WebSocket base URL of the backend, no trailing slash. */
export function getWsBase(): string {
  const override = process.env.NEXT_PUBLIC_API_URL;
  if (override) return override.replace(/\/+$/, '').replace(/^http/, 'ws');
  return `ws://${getApiHost()}:${BACKEND_PORT}`;
}
