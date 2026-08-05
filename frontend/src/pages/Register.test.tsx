import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Register from "@/pages/Register";
import { AuthProvider } from "@/hooks/useAuth";
import * as authApiModule from "@/lib/api/auth";
import { ApiError, NetworkError, AUTH_STORAGE_KEY } from "@/lib/apiClient";

vi.mock("@/lib/api/auth", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/auth")>("@/lib/api/auth");
  return {
    ...actual,
    authApi: {
      ...actual.authApi,
      register: vi.fn(),
    },
  };
});

const mockedRegister = vi.mocked(authApiModule.authApi.register);

function renderRegister() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  );
}

function fillForm(name: string, email: string, password: string) {
  fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: name } });
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: email } });
  fireEvent.change(screen.getByLabelText(/password/i), { target: { value: password } });
}

describe("Register page", () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockedRegister.mockReset();
  });

  it("shows validation errors on empty submit and does not call the API", async () => {
    renderRegister();
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument();
    });
    expect(mockedRegister).not.toHaveBeenCalled();
  });

  it("shows a validation error for an invalid email format and does not call the API", async () => {
    renderRegister();
    fillForm("Alex Student", "not-an-email", "password123");
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/enter a valid email/i)).toBeInTheDocument();
    });
    expect(mockedRegister).not.toHaveBeenCalled();
  });

  it("shows a validation error for a password under 8 characters and does not call the API", async () => {
    renderRegister();
    fillForm("Alex Student", "a@b.com", "short");
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument();
    });
    expect(mockedRegister).not.toHaveBeenCalled();
  });

  it("calls authApi.register and navigates to /dashboard on valid input", async () => {
    mockedRegister.mockResolvedValue({
      token: "tok-1",
      user: { id: "u1", email: "a@b.com", name: "Alex Student", created_at: "2026-01-01" },
    });
    renderRegister();
    fillForm("Alex Student", "a@b.com", "password123");
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
    });
    expect(mockedRegister).toHaveBeenCalledWith({
      name: "Alex Student",
      email: "a@b.com",
      password: "password123",
    });
    expect(JSON.parse(window.localStorage.getItem(AUTH_STORAGE_KEY) ?? "{}").token).toBe("tok-1");
  });

  it("shows an error message and stays on the register page for a duplicate email", async () => {
    mockedRegister.mockRejectedValue(
      new ApiError("CONFLICT", "An account with this email already exists.", 409)
    );
    renderRegister();
    fillForm("Alex Student", "a@b.com", "password123");
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/already exists/i);
    });
    expect(screen.queryByText("Dashboard Page")).not.toBeInTheDocument();
    expect(window.localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  });

  it("shows a generic network error message on network failure", async () => {
    mockedRegister.mockRejectedValue(new NetworkError());
    renderRegister();
    fillForm("Alex Student", "a@b.com", "password123");
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/couldn't reach the server/i);
    });
  });

  it("shows a loading state while the request is in flight, then re-enables the button", async () => {
    let resolveRegister: (value: unknown) => void;
    mockedRegister.mockReturnValue(
      new Promise((resolve) => {
        resolveRegister = resolve;
      }) as never
    );
    renderRegister();
    fillForm("Alex Student", "a@b.com", "password123");
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /creating account/i })).toBeDisabled();
    });

    resolveRegister!({
      token: "tok-1",
      user: { id: "u1", email: "a@b.com", name: "Alex Student", created_at: "2026-01-01" },
    });

    await waitFor(() => {
      expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
    });
  });

  it("redirects an already-authenticated user straight to /dashboard", async () => {
    window.localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({ token: "existing-tok", user: { id: "u1", email: "a@b.com", name: "Alex" } })
    );
    renderRegister();

    await waitFor(() => {
      expect(screen.getByText("Dashboard Page")).toBeInTheDocument();
    });
  });
});
