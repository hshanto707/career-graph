import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import SkillAnalysis from "@/pages/SkillAnalysis";
import { AuthProvider } from "@/hooks/useAuth";
import * as profileApiModule from "@/lib/api/profile";
import * as gapApiModule from "@/lib/api/gap";
import type { ProfileOut } from "@/lib/api/profile";
import type { GapAnalysisResponse } from "@/lib/api/skills";

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

vi.mock("@/lib/api/gap", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/gap")>("@/lib/api/gap");
  return {
    ...actual,
    gapApi: {
      ...actual.gapApi,
      analyze: vi.fn(),
    },
  };
});

const mockedProfileGet = vi.mocked(profileApiModule.profileApi.get);
const mockedAnalyze = vi.mocked(gapApiModule.gapApi.analyze);

function baseProfile(targetRoles: string[]): ProfileOut {
  return {
    id: "profile-1",
    user_id: "user-1",
    major: "Computer Science",
    graduation_year: 2026,
    skills: [],
    target_roles: targetRoles,
    experience: [],
    updated_at: "2026-01-01T00:00:00Z",
  };
}

function baseGapResponse(overrides: Partial<GapAnalysisResponse> = {}): GapAnalysisResponse {
  return {
    target_job_id: "job-1",
    readiness_score: 62,
    matched_skills: ["Python", "SQL"],
    missing_skills: [
      { skill_name: "React", importance: "must", estimated_learning_weeks: 4 },
      { skill_name: "Docker", importance: "nice", estimated_learning_weeks: 2 },
    ],
    explanation: "You match 62% of the required skills for this role.",
    encouragement: "You're making great progress -- keep building on your fundamentals.",
    roadmap: [
      {
        week_range: "3-4",
        skill_name: "React",
        course_title: "React Fundamentals",
        course_url: "https://example.com/react",
        goal: "Build a small component-based app",
      },
      {
        week_range: "1-2",
        skill_name: "Docker",
        course_title: "Docker Basics",
        course_url: "https://example.com/docker",
        goal: "Containerize a simple service",
      },
    ],
    ...overrides,
  };
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <MemoryRouter>
          <SkillAnalysis />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe("SkillAnalysis page", () => {
  beforeEach(() => {
    mockedProfileGet.mockReset();
    mockedAnalyze.mockReset();
  });

  it("prompts to set a target role when the student has none", async () => {
    mockedProfileGet.mockResolvedValue(baseProfile([]));
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/set a target role to get started/i)).toBeInTheDocument();
    });
    expect(screen.queryByLabelText(/target job/i)).not.toBeInTheDocument();
    expect(mockedAnalyze).not.toHaveBeenCalled();
  });

  it("renders the target-job selector and auto-triggers gap analysis on load", async () => {
    mockedProfileGet.mockResolvedValue(baseProfile(["job-1", "job-2"]));
    mockedAnalyze.mockResolvedValue(baseGapResponse());
    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/target job/i)).toBeInTheDocument();
    });
    // Last entry ("job-2") is the auto-selected "current" target role.
    await waitFor(() => {
      expect(mockedAnalyze).toHaveBeenCalledWith("job-2");
    });
  });

  it("selecting a different target job triggers a new gap analysis", async () => {
    mockedProfileGet.mockResolvedValue(baseProfile(["job-1", "job-2"]));
    mockedAnalyze.mockResolvedValue(baseGapResponse());
    renderPage();

    const select = await screen.findByLabelText(/target job/i);
    await waitFor(() => expect(mockedAnalyze).toHaveBeenCalledWith("job-2"));

    mockedAnalyze.mockClear();
    fireEvent.change(select, { target: { value: "job-1" } });

    await waitFor(() => {
      expect(mockedAnalyze).toHaveBeenCalledWith("job-1");
    });
  });

  it("shows a distinct loading state while the gap analysis call is pending", async () => {
    mockedProfileGet.mockResolvedValue(baseProfile(["job-1"]));
    let resolveAnalyze: (value: GapAnalysisResponse) => void = () => {};
    mockedAnalyze.mockReturnValue(
      new Promise((resolve) => {
        resolveAnalyze = resolve;
      })
    );
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("gap-analysis-loading")).toBeInTheDocument();
      expect(screen.getByText(/analyzing your skills/i)).toBeInTheDocument();
    });

    resolveAnalyze(baseGapResponse());
    await waitFor(() => {
      expect(screen.queryByTestId("gap-analysis-loading")).not.toBeInTheDocument();
    });
  });

  it("renders the gap analysis result: readiness score, matched and missing skills", async () => {
    mockedProfileGet.mockResolvedValue(baseProfile(["job-1"]));
    mockedAnalyze.mockResolvedValue(baseGapResponse());
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("62%")).toBeInTheDocument();
    });
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("SQL")).toBeInTheDocument();
    expect(screen.getAllByText("React").length).toBeGreaterThan(0);
    expect(screen.getByText(/4 wks/i)).toBeInTheDocument();
    expect(screen.getAllByText("Docker").length).toBeGreaterThan(0);
    expect(screen.getByText(/2 wks/i)).toBeInTheDocument();
  });

  it("renders roadmap milestones in week-range order regardless of API order", async () => {
    mockedProfileGet.mockResolvedValue(baseProfile(["job-1"]));
    mockedAnalyze.mockResolvedValue(baseGapResponse());
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("React Fundamentals")).toBeInTheDocument();
    });

    const roadmapContainer = screen.getByTestId("roadmap-scroll-container");
    const milestoneNames = within(roadmapContainer)
      .getAllByText(/^(React|Docker)$/)
      .map((el) => el.textContent);
    expect(milestoneNames).toEqual(["Docker", "React"]);
  });

  it("shows the LLM explanation and encouragement when present", async () => {
    mockedProfileGet.mockResolvedValue(baseProfile(["job-1"]));
    mockedAnalyze.mockResolvedValue(baseGapResponse());
    renderPage();

    await waitFor(() => {
      expect(
        screen.getByText("You match 62% of the required skills for this role.")
      ).toBeInTheDocument();
    });
    expect(
      screen.getByText(/you're making great progress -- keep building on your fundamentals/i)
    ).toBeInTheDocument();
  });

  it("shows fallback narrative text when the LLM explanation/encouragement are absent", async () => {
    mockedProfileGet.mockResolvedValue(baseProfile(["job-1"]));
    mockedAnalyze.mockResolvedValue(baseGapResponse({ explanation: "", encouragement: "" }));
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/detailed ai insights aren't available right now/i)).toBeInTheDocument();
    });
    expect(
      screen.getByText(/keep going -- every skill you close on this list/i)
    ).toBeInTheDocument();
  });

  it("shows a positive 'you're ready' state when readiness is 100% with no missing skills", async () => {
    mockedProfileGet.mockResolvedValue(baseProfile(["job-1"]));
    mockedAnalyze.mockResolvedValue(
      baseGapResponse({ readiness_score: 100, missing_skills: [], roadmap: [] })
    );
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/you're fully ready for this role/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/no roadmap needed/i)).toBeInTheDocument();
  });

  it("renders a scrollable container for a long roadmap", async () => {
    mockedProfileGet.mockResolvedValue(baseProfile(["job-1"]));
    const longRoadmap = Array.from({ length: 20 }, (_, i) => ({
      week_range: `${i + 1}-${i + 2}`,
      skill_name: `Skill ${i}`,
      course_title: `Course ${i}`,
      course_url: `https://example.com/${i}`,
      goal: `Goal ${i}`,
    }));
    mockedAnalyze.mockResolvedValue(baseGapResponse({ roadmap: longRoadmap }));
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("roadmap-scroll-container")).toBeInTheDocument();
    });
    const container = screen.getByTestId("roadmap-scroll-container");
    expect(container.className).toMatch(/overflow-y-auto/);
    expect(container.className).toMatch(/max-h-/);
  });
});
