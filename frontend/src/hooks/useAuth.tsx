import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { authApi, type LoginPayload, type RegisterPayload, type UserOut } from "@/lib/api/auth";
import { AUTH_STORAGE_KEY, clearStoredAuth, type StoredAuth } from "@/lib/apiClient";

interface AuthContextValue {
  token: string | null;
  user: UserOut | null;
  isAuthenticated: boolean;
  isLoggingIn: boolean;
  isRegistering: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredAuth(): { token: string | null; user: UserOut | null } {
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return { token: null, user: null };
    const parsed = JSON.parse(raw) as StoredAuth;
    return { token: parsed.token ?? null, user: (parsed.user as UserOut) ?? null };
  } catch {
    return { token: null, user: null };
  }
}

function persistAuth(token: string, user: UserOut): void {
  try {
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token, user }));
  } catch {
    // Storage unavailable -- auth still works for this session via in-memory
    // state, it just won't survive a reload. Documented limitation.
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const initial = readStoredAuth();
  const [token, setToken] = useState<string | null>(initial.token);
  const [user, setUser] = useState<UserOut | null>(initial.user);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);

  // If apiClient clears storage out-of-band (global 401 handler), reflect
  // that in this context's state too so the UI re-renders as logged out.
  useEffect(() => {
    const syncFromStorage = () => {
      const current = readStoredAuth();
      setToken(current.token);
      setUser(current.user);
    };
    window.addEventListener("storage", syncFromStorage);
    return () => window.removeEventListener("storage", syncFromStorage);
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    setIsLoggingIn(true);
    try {
      const result = await authApi.login(payload);
      persistAuth(result.token, result.user);
      setToken(result.token);
      setUser(result.user);
    } finally {
      setIsLoggingIn(false);
    }
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    setIsRegistering(true);
    try {
      const result = await authApi.register(payload);
      persistAuth(result.token, result.user);
      setToken(result.token);
      setUser(result.user);
    } finally {
      setIsRegistering(false);
    }
  }, []);

  const logout = useCallback(() => {
    clearStoredAuth();
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      isLoggingIn,
      isRegistering,
      login,
      register,
      logout,
    }),
    [token, user, isLoggingIn, isRegistering, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
