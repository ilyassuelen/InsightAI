import { getAccessToken, clearAccessToken } from "@/lib/auth";

const API_BASE = "http://localhost:8000";

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getAccessToken();

  const headers = new Headers(options.headers || {});
  // Only set if not already set
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    // Token invalid/expired -> log out locally
    clearAccessToken();
  }

  return res;
}

export async function apiJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await apiFetch(path, options);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}