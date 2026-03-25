/**
 * Lightweight auth token manager.
 * Stores the JWT in sessionStorage and provides helpers
 * for login and for building Authorization headers.
 */

const TOKEN_KEY = "graphsentinel_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

/**
 * Returns headers object with Authorization if a token exists.
 * Spread this into your fetch headers.
 */
export function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Login with username/password and store the JWT.
 * Returns the token on success, null on failure.
 */
export async function login(
  username: string,
  password: string
): Promise<string | null> {
  try {
    const res = await fetch(`${API_BASE}/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    const token = data.access_token;
    if (token) {
      setToken(token);
      return token;
    }
    return null;
  } catch {
    return null;
  }
}
