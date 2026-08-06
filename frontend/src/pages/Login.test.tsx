import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Login from "@/pages/Login";
import { AuthProvider } from "@/hooks/useAuth";
import * as authApiModule from "@/lib/api/auth";
import { ApiError, NetworkError, AUTH_STORAGE_KEY } from "@/lib/apiClient";

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

function renderLogin() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  );
}

function fillForm(email: string, password: string) {
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: email } });
  fireEvent.change(screen.getByLabelText(/password/i), { target: { value: password } });
}

describe("Login page", () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockedLogin.mockReset();
  });

  it("shows validation errors on empty submit and does not call the API", async () => {
    renderLogin();
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    });
    expect(mockedLogin).not.toHaveBeenCalled();
  });

  it("shows a validation error for an invalid email format and does not call the API", async () => {
    renderLogin();
    fillForm("not-an-email", "password123");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/enter a valid email/i)).toBeInTheDocument();
    });
    expect(mockedLogin).not.toHaveBeenCalled();
  });

  it("treats whitespace-only input as empty", async () => {
    renderLogin();
    fillForm("   ", "   ");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
    });
    expect(mockedLogin).not.toHaveBeenCalled();
  });

  it("calls authApi.login and navigates to /dashboard on valid credentials", async () => {
    mockedLogin.mockResolvedValue({
      token: "tok-1",
      user: { id: "u1", email: "a@b.com", name: "Alex", created_at: "2026-01-01" },
    });
    renderLogin();
    fillForm("a@b.com", "correct-password");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
    });
    expect(mockedLogin).toHaveBeenCalledWith({ email: "a@b.com", password: "correct-password" });
    expect(JSON.parse(window.localStorage.getItem(AUTH_STORAGE_KEY) ?? "{}").token).toBe("tok-1");
  });

  it("shows an error message and stays on the login page for invalid credentials", async () => {
    mockedLogin.mockRejectedValue(new ApiError("UNAUTHORIZED", "Invalid email or password.", 401));
    renderLogin();
    fillForm("a@b.com", "wrong-password");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/invalid email or password/i);
    });
    expect(screen.queryByText("Dashboard Page")).not.toBeInTheDocument();
    expect(window.localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  });

  it("shows the backend's lockout message when rate-limited after too many failed attempts", async () => {
    mockedLogin.mockRejectedValue(
      new ApiError("TOO_MANY_ATTEMPTS", "Too many failed login attempts. Try again in 300 seconds.", 429)
    );
    renderLogin();
    fillForm("a@b.com", "wrong-password");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/too many failed login attempts/i);
    });
    expect(window.localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  });

  it("shows a generic network error message on network failure", async () => {
    mockedLogin.mockRejectedValue(new NetworkError());
    renderLogin();
    fillForm("a@b.com", "password123");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/couldn't reach the server/i);
    });
  });

  it("shows a loading state while the request is in flight, then re-enables the button", async () => {
    let resolveLogin: (value: unknown) => void;
    mockedLogin.mockReturnValue(
      new Promise((resolve) => {
        resolveLogin = resolve;
      }) as never
    );
    renderLogin();
    fillForm("a@b.com", "password123");
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /signing in/i })).toBeDisabled();
    });

    resolveLogin!({
      token: "tok-1",
      user: { id: "u1", email: "a@b.com", name: "Alex", created_at: "2026-01-01" },
    });

    await waitFor(() => {
      expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
    });
  });

  it("submits the form on native submit event (Enter-key path)", async () => {
    mockedLogin.mockResolvedValue({
      token: "tok-1",
      user: { id: "u1", email: "a@b.com", name: "Alex", created_at: "2026-01-01" },
    });
    const { container } = renderLogin();
    fillForm("a@b.com", "correct-password");

    const form = container.querySelector("form");
    expect(form).not.toBeNull();
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(mockedLogin).toHaveBeenCalledWith({ email: "a@b.com", password: "correct-password" });
    });
  });

  it("redirects an already-authenticated user straight to /dashboard", async () => {
    window.localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({ token: "existing-tok", user: { id: "u1", email: "a@b.com", name: "Alex" } })
    );
    renderLogin();

    await waitFor(() => {
      expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
    });
  });
});
