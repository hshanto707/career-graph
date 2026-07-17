import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { AUTH_STORAGE_KEY } from "@/lib/apiClient";
import * as authApiModule from "@/lib/api/auth";

vi.mock("@/lib/api/auth", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/auth")>("@/lib/api/auth");
  return {
    ...actual,
    authApi: {
      ...actual.authApi,
      login: vi.fn(),
    },
  };
});

const mockedLogin = vi.mocked(authApiModule.authApi.login);

function wrapper({ children }: { children: React.ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}

describe("useAuth", () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockedLogin.mockReset();
  });

  it("starts unauthenticated with no stored token", () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.token).toBeNull();
    expect(result.current.user).toBeNull();
  });

  it("login() populates token/user and persists to localStorage", async () => {
    mockedLogin.mockResolvedValue({
      token: "tok-1",
      user: { id: "u1", email: "a@b.com", name: "Alex", created_at: "2026-01-01" },
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({ email: "a@b.com", password: "pw" });
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.token).toBe("tok-1");
    expect(result.current.user?.email).toBe("a@b.com");

    const stored = JSON.parse(window.localStorage.getItem(AUTH_STORAGE_KEY) ?? "{}");
    expect(stored.token).toBe("tok-1");
  });

  it("restores auth state from localStorage on mount (survives reload)", () => {
    window.localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({ token: "persisted-tok", user: { id: "u1", email: "a@b.com", name: "Alex" } })
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.token).toBe("persisted-tok");
  });

  it("logout() clears token/user from state and storage", async () => {
    mockedLogin.mockResolvedValue({
      token: "tok-1",
      user: { id: "u1", email: "a@b.com", name: "Alex", created_at: "2026-01-01" },
    });
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login({ email: "a@b.com", password: "pw" });
    });
    expect(result.current.isAuthenticated).toBe(true);

    act(() => {
      result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.token).toBeNull();
    expect(window.localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  });

  it("throws if used outside AuthProvider", () => {
    // Suppress React's expected console.error for the thrown-render case.
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => renderHook(() => useAuth())).toThrow(/AuthProvider/);
    spy.mockRestore();
  });
});
