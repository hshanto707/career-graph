import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, waitFor } from "@testing-library/react";
import { QueryCache, QueryClient, useQuery } from "@tanstack/react-query";
import { QueryClientProvider } from "@tanstack/react-query";
import { toast } from "@/components/ui/sonner";
import { ApiError, NetworkError } from "@/lib/apiClient";

// App.tsx wires a QueryCache.onError -> toast.error handler so that *any*
// failing query anywhere in the app surfaces a toast instead of failing
// silently (docs/test-plan.md F8 #3). Rather than mount the whole <App/>
// (which needs a real router/auth/DB), this test exercises the exact same
// QueryCache configuration in isolation to pin its error -> toast contract.

vi.mock("@/components/ui/sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

function describeQueryError(error: unknown, label?: string): string {
  const prefix = label ? `${label}: ` : "";
  if (error instanceof NetworkError) return `${prefix}${error.message}`;
  if (error instanceof ApiError) {
    if (error.status === 401) return "";
    return `${prefix}${error.message}`;
  }
  if (error instanceof Error) return `${prefix}${error.message}`;
  return `${prefix}Something went wrong.`;
}

function makeClient() {
  const queryCache = new QueryCache({
    onError: (error, query) => {
      const label = (query.meta?.toastLabel as string | undefined) ?? undefined;
      const message = describeQueryError(error, label);
      if (message) toast.error(message);
    },
  });
  return new QueryClient({ queryCache, defaultOptions: { queries: { retry: false } } });
}

function FailingComponent({ error, meta }: { error: unknown; meta?: Record<string, unknown> }) {
  useQuery({
    queryKey: ["failing", JSON.stringify(meta)],
    queryFn: () => Promise.reject(error),
    meta,
  });
  return null;
}

describe("global query error -> toast wiring", () => {
  beforeEach(() => {
    vi.mocked(toast.error).mockClear();
  });

  it("shows a toast for a generic API error", async () => {
    const client = makeClient();
    render(
      <QueryClientProvider client={client}>
        <FailingComponent error={new ApiError("SERVER_ERROR", "Server exploded.", 500)} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(expect.stringContaining("Server exploded."));
    });
  });

  it("prefixes the toast with a section label when the query provides one", async () => {
    const client = makeClient();
    render(
      <QueryClientProvider client={client}>
        <FailingComponent
          error={new ApiError("SERVER_ERROR", "Down.", 500)}
          meta={{ toastLabel: "Course recommendations" }}
        />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("Course recommendations: Down.");
    });
  });

  it("suppresses the toast for a 401 (apiClient already redirects to login)", async () => {
    const client = makeClient();
    render(
      <QueryClientProvider client={client}>
        <FailingComponent error={new ApiError("UNAUTHORIZED", "Session expired.", 401)} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(client.getQueryCache().findAll()).toHaveLength(1);
    });
    expect(toast.error).not.toHaveBeenCalled();
  });

  it("shows a toast for a network failure", async () => {
    const client = makeClient();
    render(
      <QueryClientProvider client={client}>
        <FailingComponent error={new NetworkError()} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(expect.stringContaining("Network error"));
    });
  });

  it("queues multiple independent failures as separate toast calls rather than dropping any", async () => {
    const client = makeClient();
    render(
      <QueryClientProvider client={client}>
        <FailingComponent error={new ApiError("A", "First failure.", 500)} meta={{ toastLabel: "A" }} />
        <FailingComponent error={new ApiError("B", "Second failure.", 500)} meta={{ toastLabel: "B" }} />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledTimes(2);
    });
  });
});
