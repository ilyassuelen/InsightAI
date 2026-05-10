import { getAccessToken, clearAccessToken } from "@/lib/auth";

const API_BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getAccessToken();

  const headers = new Headers(options.headers || {});
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
        let message = `Request failed: ${res.status}`;

        try {
            const errorData = await res.json();

            if (typeof errorData === "string") {
                message = errorData;

            } else if (errorData?.detail) {
                message = errorData.detail;

            } else if (errorData?.message) {
                message = errorData.message;

            } else {
                message = JSON.stringify(errorData);
            }

        } catch {
            const text = await res.text().catch(() => "");

            if (text) {
                message = text;
            }
        }

        throw new Error(message);
    }

    return res.json() as Promise<T>;
}
