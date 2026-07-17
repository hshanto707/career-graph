import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  apiRequest,
  AUTH_STORAGE_KEY,
  ApiError,
  NetworkError,
  getStoredToken,
  clearStoredAuth,
  __setRedirectToLogin,
} from "@/lib/apiClient";

function mockFetchOnce(status: number, body: unknown) {
  global.fetch = vi.fn().mockResolvedValue({
    status,
    ok: status >= 200 && status < 300,
    json: async () => body,
  }) as unknown as typeof fetch;
}

describe("apiClient", () => {
  let redirectSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    window.localStorage.clear();
    redirectSpy = vi.fn();
    __setRedirectToLogin(redirectSpy);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("unwraps { success: true, data } and returns data directly", async () => {
    mockFetchOnce(200, { success: true, data: { id: "job-1" }, message: null });

    const result = await apiRequest<{ id: string }>("/jobs/job-1");

    expect(result).toEqual({ id: "job-1" });
  });

  it("throws ApiError on { success: false, error, message }", async () => {
    mockFetchOnce(404, { success: false, error: "NOT_FOUND", message: "Job xyz does not exist" });

    await expect(apiRequest("/jobs/xyz")).rejects.toMatchObject({
      error: "NOT_FOUND",
      message: "Job xyz does not exist",
    });
  });

  it("injects Authorization: Bearer <token> when a token is stored", async () => {
    window.localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({ token: "abc123", user: { id: "1" } })
    );
    const fetchSpy = vi.fn().mockResolvedValue({
      status: 200,
      ok: true,
      json: async () => ({ success: true, data: {} }),
    });
    global.fetch = fetchSpy as unknown as typeof fetch;

    await apiRequest("/profile");

    const [, options] = fetchSpy.mock.calls[0];
    expect(options.headers.Authorization).toBe("Bearer abc123");
  });

  it("omits Authorization header when no token exists (not 'Bearer null')", async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      status: 200,
      ok: true,
      json: async () => ({ success: true, data: {} }),
    });
    global.fetch = fetchSpy as unknown as typeof fetch;

    await apiRequest("/jobs");

    const [, options] = fetchSpy.mock.calls[0];
    expect(options.headers.Authorization).toBeUndefined();
  });

  it("on a 401 response, clears stored auth and redirects to login", async () => {
    window.localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({ token: "expired-token", user: { id: "1" } })
    );
    mockFetchOnce(401, { success: false, error: "UNAUTHORIZED", message: "Session expired" });

    await expect(apiRequest("/dashboard")).rejects.toBeInstanceOf(ApiError);

    expect(getStoredToken()).toBeNull();
    expect(redirectSpy).toHaveBeenCalledTimes(1);
  });

  it("surfaces a NetworkError distinct from ApiError on fetch rejection", async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError("Failed to fetch")) as unknown as typeof fetch;

    await expect(apiRequest("/dashboard")).rejects.toBeInstanceOf(NetworkError);
  });

  it("clearStoredAuth removes the persisted auth blob", () => {
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: "t", user: {} }));
    clearStoredAuth();
    expect(getStoredToken()).toBeNull();
  });
});
