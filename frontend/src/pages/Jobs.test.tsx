import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/hooks/useAuth";
import { AUTH_STORAGE_KEY } from "@/lib/apiClient";
import Jobs from "@/pages/Jobs";
import { jobsApi, type JobOut } from "@/lib/api/jobs";

vi.mock("@/lib/api/jobs", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/jobs")>("@/lib/api/jobs");
  return {
    ...actual,
    jobsApi: {
      ...actual.jobsApi,
      list: vi.fn(),
    },
  };
});

const mockedList = vi.mocked(jobsApi.list);

function makeJob(overrides: Partial<JobOut> = {}): JobOut {
  return {
    id: "job-1",
    title: "Frontend Engineer",
    company: "Acme Corp",
    location: "Remote",
    type: "Full-time",
    source: "kaggle",
    salary_min: 90000,
    salary_max: 120000,
    ...overrides,
  };
}

function renderJobs() {
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
        <MemoryRouter initialEntries={["/jobs"]}>
          <Jobs />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe("Jobs (Job Explorer)", () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockedList.mockReset();
  });

  it("shows a loading state, then fetches and renders jobs from GET /jobs with no filters applied", async () => {
    let resolvePromise: (value: JobOut[]) => void = () => {};
    mockedList.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve;
      })
    );

    renderJobs();

    expect(screen.getByText(/loading jobs/i)).toBeInTheDocument();

    resolvePromise([makeJob({ id: "job-1", title: "Frontend Engineer" })]);

    await waitFor(() => {
      expect(screen.getByText("Frontend Engineer")).toBeInTheDocument();
    });

    expect(mockedList).toHaveBeenCalledWith(
      expect.objectContaining({ type: undefined, location: undefined, search: undefined })
    );
  });

  it("does not show a personalized match score anywhere on the catalog page", async () => {
    mockedList.mockResolvedValue([makeJob()]);
    renderJobs();

    await waitFor(() => expect(screen.getByText("Frontend Engineer")).toBeInTheDocument());

    expect(screen.queryByText(/match/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/why (this job is )?recommended/i)).not.toBeInTheDocument();
  });

  it("filters by type: selecting Internship re-queries and only internship results render", async () => {
    mockedList.mockResolvedValueOnce([
      makeJob({ id: "job-1", title: "Frontend Engineer", type: "Full-time" }),
    ]);
    renderJobs();
    await waitFor(() => expect(screen.getByText("Frontend Engineer")).toBeInTheDocument());

    mockedList.mockResolvedValueOnce([
      makeJob({ id: "job-2", title: "Summer Intern", type: "Internship" }),
    ]);

    fireEvent.change(screen.getByLabelText(/filter by job type/i), {
      target: { value: "Internship" },
    });

    await waitFor(() => {
      expect(screen.getByText("Summer Intern")).toBeInTheDocument();
    });
    expect(screen.queryByText("Frontend Engineer")).not.toBeInTheDocument();

    expect(mockedList).toHaveBeenLastCalledWith(
      expect.objectContaining({ type: "Internship" })
    );
  });

  it("search narrows results after the debounce settles", async () => {
    mockedList.mockResolvedValueOnce([
      makeJob({ id: "job-1", title: "Frontend Engineer" }),
      makeJob({ id: "job-2", title: "Backend Engineer" }),
    ]);
    renderJobs();
    await waitFor(() => expect(screen.getByText("Frontend Engineer")).toBeInTheDocument());

    mockedList.mockResolvedValueOnce([makeJob({ id: "job-1", title: "Frontend Engineer" })]);

    fireEvent.change(screen.getByLabelText(/search jobs or companies/i), {
      target: { value: "Frontend" },
    });

    // Not narrowed immediately -- still debounced.
    expect(mockedList).not.toHaveBeenLastCalledWith(
      expect.objectContaining({ search: "Frontend" })
    );

    await waitFor(
      () => {
        expect(mockedList).toHaveBeenLastCalledWith(
          expect.objectContaining({ search: "Frontend" })
        );
      },
      { timeout: 2000 }
    );
  });

  it("shows an explicit empty-results state when a filter combination matches nothing", async () => {
    mockedList.mockResolvedValue([]);
    renderJobs();

    await waitFor(() => {
      expect(screen.getByText(/no jobs match your filters/i)).toBeInTheDocument();
    });
  });

  it("shows an inline error state on API failure", async () => {
    mockedList.mockRejectedValue(new Error("Server exploded"));
    renderJobs();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/server exploded/i);
    });
  });

  it("supports pagination via Load more, appending the next page's results", async () => {
    const pageOne = Array.from({ length: 10 }, (_, i) =>
      makeJob({ id: `job-${i}`, title: `Job ${i}` })
    );
    mockedList.mockResolvedValueOnce(pageOne);
    renderJobs();

    await waitFor(() => expect(screen.getByText("Job 0")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /load more/i })).toBeInTheDocument();

    const pageTwo = [makeJob({ id: "job-10", title: "Job 10" })];
    mockedList.mockResolvedValueOnce(pageTwo);

    fireEvent.click(screen.getByRole("button", { name: /load more/i }));

    await waitFor(() => expect(screen.getByText("Job 10")).toBeInTheDocument());
    // Previous page's results remain rendered (appended, not replaced).
    expect(screen.getByText("Job 0")).toBeInTheDocument();

    // Fewer than a full page was returned -- no more pages, control disappears.
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: /load more/i })).not.toBeInTheDocument();
    });
  });

  it("guards against out-of-order race conditions on rapid filter changes: only the latest request's results render", async () => {
    mockedList.mockResolvedValueOnce([makeJob({ id: "job-1", title: "Initial Job" })]);
    renderJobs();
    await waitFor(() => expect(screen.getByText("Initial Job")).toBeInTheDocument());

    let resolveSlow: (value: JobOut[]) => void = () => {};
    const slowRequest = new Promise<JobOut[]>((resolve) => {
      resolveSlow = resolve;
    });
    // First filter change fires a slow request...
    mockedList.mockReturnValueOnce(slowRequest);
    fireEvent.change(screen.getByLabelText(/filter by job type/i), {
      target: { value: "Internship" },
    });

    // ...then a second, faster-resolving filter change fires before the first settles.
    mockedList.mockResolvedValueOnce([makeJob({ id: "job-2", title: "Fast Result" })]);
    fireEvent.change(screen.getByLabelText(/filter by job type/i), {
      target: { value: "Contract" },
    });

    await waitFor(() => expect(screen.getByText("Fast Result")).toBeInTheDocument());

    // The slow, stale request for "Internship" now resolves late -- it must
    // never override the currently-selected "Contract" filter's rendered data.
    resolveSlow([makeJob({ id: "job-3", title: "Stale Internship Result" })]);

    await waitFor(() => {
      expect(screen.getByText("Fast Result")).toBeInTheDocument();
    });
    expect(screen.queryByText("Stale Internship Result")).not.toBeInTheDocument();
  });
});
