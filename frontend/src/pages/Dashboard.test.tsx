import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/hooks/useAuth";
import { AUTH_STORAGE_KEY } from "@/lib/apiClient";
import Dashboard from "@/pages/Dashboard";
import { dashboardApi, type DashboardStatsOut } from "@/lib/api/dashboard";

vi.mock("@/lib/api/dashboard", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/dashboard")>("@/lib/api/dashboard");
  return {
    ...actual,
    dashboardApi: {
      ...actual.dashboardApi,
      get: vi.fn(),
    },
  };
});

const mockedGet = vi.mocked(dashboardApi.get);

const FULL_PAYLOAD: DashboardStatsOut = {
  job_readiness_score: 72,
  skills_matched: 5,
  total_required_skills: 8,
  missing_high_demand_skills: ["React", "AWS", "Docker"],
  matched_market_skills: ["Python"],
  market_demand: [
    { skill_name: "Python", demand_count: 120, demand_score: 95, trend: null },
    { skill_name: "React", demand_count: 100, demand_score: 88, trend: null },
    { skill_name: "AWS", demand_count: 90, demand_score: 85, trend: null },
  ],
};

function renderDashboard() {
  window.localStorage.setItem(
    AUTH_STORAGE_KEY,
    JSON.stringify({ token: "tok-1", user: { id: "u1", email: "a@b.com", name: "Alex" } })
  );
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter initialEntries={["/dashboard"]}>
          <Dashboard />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe("Dashboard", () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockedGet.mockReset();
  });

  it("renders the loading skeleton before data resolves", async () => {
    let resolvePromise: (value: DashboardStatsOut) => void = () => {};
    mockedGet.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      })
    );

    renderDashboard();

    expect(screen.getByTestId("dashboard-skeleton")).toBeInTheDocument();

    resolvePromise(FULL_PAYLOAD);
    await waitFor(() => expect(screen.queryByTestId("dashboard-skeleton")).not.toBeInTheDocument());
  });

  it("renders StatCard/SkillBar values matching the mocked payload exactly", async () => {
    mockedGet.mockResolvedValue(FULL_PAYLOAD);

    renderDashboard();

    await waitFor(() => expect(screen.getByText("72%")).toBeInTheDocument());
    expect(screen.getByText("5 / 8")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("React, AWS, Docker")).toBeInTheDocument();

    // Market demand list renders all three skills with their demand scores.
    expect(screen.getAllByText("Python").length).toBeGreaterThan(0);
    expect(screen.getAllByText("React").length).toBeGreaterThan(0);
    expect(screen.getAllByText("AWS").length).toBeGreaterThan(0);
    expect(screen.getAllByText("95%").length).toBeGreaterThan(0);
  });

  it("shows a 'complete your profile' prompt when skills/required skills are both zero", async () => {
    mockedGet.mockResolvedValue({
      job_readiness_score: 0,
      skills_matched: 0,
      total_required_skills: 0,
      missing_high_demand_skills: [],
      matched_market_skills: [],
      market_demand: [],
    });

    renderDashboard();

    await waitFor(() =>
      expect(screen.getByText(/complete your profile/i)).toBeInTheDocument()
    );
    // Must not render broken 0/0 math stat cards.
    expect(screen.queryByText("0 / 0")).not.toBeInTheDocument();
  });

  it("shows an error state with a retry affordance on API failure, and retry re-fetches", async () => {
    mockedGet.mockRejectedValueOnce(new Error("network down"));
    mockedGet.mockResolvedValueOnce(FULL_PAYLOAD);

    renderDashboard();

    await waitFor(() => expect(screen.getByText(/couldn't load your dashboard/i)).toBeInTheDocument());

    const retryButton = screen.getByRole("button", { name: /retry/i });
    retryButton.click();

    await waitFor(() => expect(screen.getByText("72%")).toBeInTheDocument());
    expect(mockedGet).toHaveBeenCalledTimes(2);
  });

  it("renders a positive 'covered' state when missingHighDemandSkills is empty", async () => {
    mockedGet.mockResolvedValue({
      job_readiness_score: 100,
      skills_matched: 8,
      total_required_skills: 8,
      missing_high_demand_skills: [],
      matched_market_skills: ["Python"],
      market_demand: [
        { skill_name: "Python", demand_count: 120, demand_score: 95, trend: null },
      ],
    });

    renderDashboard();

    await waitFor(() =>
      expect(screen.getByText(/you're covered on high-demand skills/i)).toBeInTheDocument()
    );
    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.getByText(/you're covered — no high-demand skills missing/i)).toBeInTheDocument();
  });
});
