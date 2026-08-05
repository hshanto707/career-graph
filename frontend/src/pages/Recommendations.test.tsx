import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Recommendations from "@/pages/Recommendations";
import { recommendationsApi } from "@/lib/api/recommendations";
import { ApiError, AUTH_STORAGE_KEY } from "@/lib/apiClient";
import { AuthProvider } from "@/hooks/useAuth";

vi.mock("@/lib/api/recommendations", () => ({
  recommendationsApi: {
    jobs: vi.fn(),
    skills: vi.fn(),
    courses: vi.fn(),
  },
}));

const mockedJobs = vi.mocked(recommendationsApi.jobs);
const mockedSkills = vi.mocked(recommendationsApi.skills);
const mockedCourses = vi.mocked(recommendationsApi.courses);

function renderPage() {
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
        <MemoryRouter>
          <Recommendations />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

const sampleJob = {
  job_id: "job-1",
  title: "Data Analyst",
  match_percentage: 78,
  matched_skills: ["Python", "SQL"],
  why_recommended: "Strong match with your Python and SQL skills.",
  match_source: "algorithmic" as const,
};

const sampleSkill = {
  skill_name: "Tableau",
  demand_score: 82,
  demand_count: 120,
};

const sampleCourse = {
  course_id: "course-1",
  title: "Intro to Tableau",
  provider: "Coursera",
  url: "https://example.com/course",
  duration: "4 weeks",
  free: true,
  skill_name: "Tableau",
};

describe("Recommendations page", () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockedJobs.mockReset();
    mockedSkills.mockReset();
    mockedCourses.mockReset();
  });

  it("loads and renders all three independent sections", async () => {
    mockedJobs.mockResolvedValue([sampleJob]);
    mockedSkills.mockResolvedValue([sampleSkill]);
    mockedCourses.mockResolvedValue([sampleCourse]);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Data Analyst")).toBeInTheDocument();
    });
    expect(screen.getByRole("tab", { name: /skills/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /courses/i })).toBeInTheDocument();
  });

  it("shows an AI-ranked badge only for jobs the GNN reranked", async () => {
    mockedJobs.mockResolvedValue([
      { ...sampleJob, job_id: "job-gnn", title: "GNN Job", match_source: "gnn" as const },
      { ...sampleJob, job_id: "job-algo", title: "Algo Job", match_source: "algorithmic" as const },
    ]);
    mockedSkills.mockResolvedValue([]);
    mockedCourses.mockResolvedValue([]);

    renderPage();

    await waitFor(() => expect(screen.getByText("GNN Job")).toBeInTheDocument());
    expect(screen.getByText("Algo Job")).toBeInTheDocument();
    expect(screen.getAllByText(/ai-ranked/i)).toHaveLength(1);
  });

  it("isolates failures: a failing courses section does not break jobs/skills", async () => {
    mockedJobs.mockResolvedValue([sampleJob]);
    mockedSkills.mockResolvedValue([sampleSkill]);
    mockedCourses.mockRejectedValue(new ApiError("SERVER_ERROR", "Courses backend is down.", 500));

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Data Analyst")).toBeInTheDocument();
    });

    fireEvent.mouseDown(screen.getByRole("tab", { name: /courses/i }));
    await waitFor(() => {
      expect(screen.getByText(/couldn't load course recommendations/i)).toBeInTheDocument();
    });

    // Switching back to jobs proves its section's data/state survived the
    // courses section's failure -- one section's query error never tore
    // down the others' independently-cached React Query state.
    fireEvent.mouseDown(screen.getByRole("tab", { name: /^jobs$/i }));
    await waitFor(() => {
      expect(screen.getByText("Data Analyst")).toBeInTheDocument();
    });
    expect(screen.queryByText(/couldn't load job recommendations/i)).not.toBeInTheDocument();
  });

  it("falls back to templated why_recommended text when the LLM narrative is absent", async () => {
    mockedJobs.mockResolvedValue([{ ...sampleJob, why_recommended: "" }]);
    mockedSkills.mockResolvedValue([]);
    mockedCourses.mockResolvedValue([]);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/matched on python, sql/i)).toBeInTheDocument();
    });
  });

  it("shows a positive empty state for a single section with zero results", async () => {
    mockedJobs.mockResolvedValue([sampleJob]);
    mockedSkills.mockResolvedValue([]);
    mockedCourses.mockResolvedValue([sampleCourse]);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Data Analyst")).toBeInTheDocument();
    });
    fireEvent.mouseDown(screen.getByRole("tab", { name: /skills/i }));
    await waitFor(() => {
      expect(screen.getByText(/no skill gaps to close right now/i)).toBeInTheDocument();
    });
  });

  it("shows an overall empty state pointing back to Profile setup when all three sections are empty", async () => {
    mockedJobs.mockResolvedValue([]);
    mockedSkills.mockResolvedValue([]);
    mockedCourses.mockResolvedValue([]);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/no recommendations yet/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: /complete profile/i })).toHaveAttribute(
      "href",
      "/profile/edit"
    );
  });
});
