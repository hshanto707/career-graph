import { describe, expect, it, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AuthProvider } from "@/hooks/useAuth";
import { AUTH_STORAGE_KEY } from "@/lib/apiClient";

function renderProtected(initialPath = "/dashboard") {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/" element={<div>Login Page</div>} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <div>Dashboard Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  );
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("redirects to / when there is no token", () => {
    renderProtected("/dashboard");
    expect(screen.getByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Dashboard Content")).not.toBeInTheDocument();
  });

  it("renders the child route when a valid token is present", () => {
    window.localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({ token: "tok-1", user: { id: "u1", email: "a@b.com", name: "Alex" } })
    );
    renderProtected("/dashboard");
    expect(screen.getByText("Dashboard Content")).toBeInTheDocument();
  });
});
