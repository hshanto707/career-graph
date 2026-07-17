// Central fetch wrapper for the CareerGraph API.
//
// Responsibilities:
//   - Resolve the base URL from VITE_API_BASE_URL.
//   - Serialize/deserialize JSON.
//   - Unwrap the backend's envelope: { success, data, message } -> data;
//     { success: false, error, message } -> throw an ApiError.
//   - Inject `Authorization: Bearer <token>` automatically when a token is
//     stored (never sends "Bearer null"/"Bearer undefined").
//   - On any 401 response, clear stored auth and redirect to "/" (session
//     expired UX) -- this fires regardless of *why* the 401 happened
//     (missing header, tampered token, or a token that looked valid on the
//     client but the server has since rejected/expired).

export const AUTH_STORAGE_KEY = "careergraph.auth";

export interface StoredAuth {
  token: string;
  user: unknown;
}

/** Reads the persisted token directly from localStorage. Kept independent
 * of React so the plain (non-hook) apiClient can use it without a Provider. */
export function getStoredToken(): string | null {
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StoredAuth;
    return parsed?.token ?? null;
  } catch {
    return null;
  }
}

export function clearStoredAuth(): void {
  try {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
  } catch {
    // Storage unavailable (e.g. blocked/private browsing) -- nothing to
    // clear, nothing to crash over.
  }
}

/** Indirection point so tests can observe/override the redirect without a
 * real jsdom navigation. Defaults to a real client-side redirect. */
export let redirectToLogin: () => void = () => {
  window.location.assign("/");
};

/** Test-only seam: allows swapping the redirect behavior. */
export function __setRedirectToLogin(fn: () => void): void {
  redirectToLogin = fn;
}

export class ApiError extends Error {
  readonly error: string;
  readonly status: number;

  constructor(error: string, message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.error = error;
    this.status = status;
  }
}

/** Raised for genuine network failures (server unreachable, DNS failure,
 * CORS rejection, offline) -- distinct from a well-formed 4xx/5xx response
 * so callers can show a "couldn't reach server" message specifically. */
export class NetworkError extends Error {
  constructor(message = "Network error: could not reach the server.") {
    super(message);
    this.name = "NetworkError";
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  headers?: Record<string, string>;
  /** Skip Authorization header injection (used by login/register). */
  skipAuth?: boolean;
}

function getBaseUrl(): string {
  const base = import.meta.env.VITE_API_BASE_URL as string | undefined;
  return (base ?? "http://localhost:8000").replace(/\/+$/, "");
}

interface Envelope<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string | null;
}

export async function apiRequest<T = unknown>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, headers = {}, skipAuth = false } = options;

  const finalHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...headers,
  };

  if (!skipAuth) {
    const token = getStoredToken();
    if (token) {
      finalHeaders["Authorization"] = `Bearer ${token}`;
    }
  }

  let response: Response;
  try {
    response = await fetch(`${getBaseUrl()}${path}`, {
      method,
      headers: finalHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new NetworkError();
  }

  if (response.status === 401) {
    clearStoredAuth();
    redirectToLogin();
    throw new ApiError("UNAUTHORIZED", "Your session has expired. Please log in again.", 401);
  }

  let payload: Envelope<T> | null = null;
  try {
    payload = (await response.json()) as Envelope<T>;
  } catch {
    // Non-JSON response body.
    if (!response.ok) {
      throw new ApiError("HTTP_ERROR", `Request failed with status ${response.status}.`, response.status);
    }
    throw new ApiError("PARSE_ERROR", "Could not parse server response.", response.status);
  }

  if (!payload.success) {
    throw new ApiError(payload.error ?? "UNKNOWN_ERROR", payload.message ?? "Request failed.", response.status);
  }

  return payload.data as T;
}

export const apiClient = {
  get: <T = unknown>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...options, method: "GET" }),
  post: <T = unknown>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...options, method: "POST", body }),
  put: <T = unknown>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...options, method: "PUT", body }),
  patch: <T = unknown>(path: string, body?: unknown, options?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...options, method: "PATCH", body }),
  delete: <T = unknown>(path: string, options?: Omit<RequestOptions, "method" | "body">) =>
    apiRequest<T>(path, { ...options, method: "DELETE" }),
};
