import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/hooks/useAuth";
import { AUTH_STORAGE_KEY } from "@/lib/apiClient";
import Profile from "@/pages/Profile";
import { profileApi, type ProfileOut } from "@/lib/api/profile";

vi.mock("@/lib/api/profile", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/profile")>("@/lib/api/profile");
  return {
    ...actual,
    profileApi: {
      ...actual.profileApi,
      get: vi.fn(),
    },
  };
});

const mockedGet = vi.mocked(profileApi.get);

const FULL_PROFILE: ProfileOut = {
  id: "p1",
  user_id: "u1",
  major: "Computer Science",
  graduation_year: 2026,
  skills: [
    { name: "Python", proficiency: 8, years: 3 },
    { name: "SQL", proficiency: 6, years: 2 },
  ],
  target_roles: ["Data Analyst", "ML Engineer"],
  experience: [
    {
      title: "Intern",
      company: "Acme",
      start_month: 6,
      start_year: 2024,
      end_month: 8,
      end_year: 2024,
      is_current: false,
      description: "Built things.",
    },
  ],
  updated_at: "2026-01-01T00:00:00Z",
};

function renderProfile() {
  window.localStorage.setItem(
    AUTH_STORAGE_KEY,
    JSON.stringify({ token: "tok-1", user: { id: "u1", email: "alex@school.edu", name: "Alex Chen" } })
  );
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={["/profile"]}>
          <Profile />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe("Profile page", () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockedGet.mockReset();
  });

  it("shows a loading state before data resolves", async () => {
    let resolvePromise: (value: ProfileOut) => void = () => {};
    mockedGet.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      })
    );

    renderProfile();
    expect(screen.getByTestId("profile-loading")).toBeInTheDocument();

    resolvePromise(FULL_PROFILE);
    await waitFor(() => expect(screen.queryByTestId("profile-loading")).not.toBeInTheDocument());
  });

  it("renders fetched profile data exactly, with no leftover mock data", async () => {
    mockedGet.mockResolvedValue(FULL_PROFILE);

    renderProfile();

    await waitFor(() => expect(screen.getByText("Computer Science")).toBeInTheDocument());
    expect(screen.getByText("2026")).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("SQL")).toBeInTheDocument();
    expect(screen.getByText("Data Analyst")).toBeInTheDocument();
    expect(screen.getByText("ML Engineer")).toBeInTheDocument();
    expect(screen.getByText("Intern")).toBeInTheDocument();
    expect(screen.getByText(/June 2024 - August 2024/)).toBeInTheDocument();

    // No hardcoded mock student data (e.g. from lib/mockData.ts) present.
    expect(screen.getAllByText("Alex Chen").length).toBeGreaterThan(0); // real authenticated user, not mock
    expect(screen.queryByText("alex.chen@university.edu")).not.toBeInTheDocument();
  });

  it("renders a zero-skills empty state without crashing", async () => {
    mockedGet.mockResolvedValue({ ...FULL_PROFILE, skills: [] });

    renderProfile();

    await waitFor(() => expect(screen.getByText(/haven't added any skills yet/i)).toBeInTheDocument());
  });

  it("shows an error state with retry on API failure", async () => {
    mockedGet.mockRejectedValueOnce(new Error("network down"));
    mockedGet.mockResolvedValueOnce(FULL_PROFILE);

    renderProfile();

    await waitFor(() => expect(screen.getByText(/couldn't load your profile/i)).toBeInTheDocument());
    screen.getByRole("button", { name: /try again/i }).click();

    await waitFor(() => expect(screen.getByText("Computer Science")).toBeInTheDocument());
    expect(mockedGet).toHaveBeenCalledTimes(2);
  });
});
