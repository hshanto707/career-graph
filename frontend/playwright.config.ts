import { defineConfig, devices } from "@playwright/test";

// One id per whole run, shared by every test's generated email (see
// fixtures/users.ts) and by global-teardown's safety-net sweep. Computed
// once here (config is loaded once in the main process before workers are
// spawned) and inherited by worker processes via process.env.
const RUN_ID =
  process.env.E2E_RUN_ID ?? `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
process.env.E2E_RUN_ID = RUN_ID;

export default defineConfig({
  testDir: "./tests/e2e/specs",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  // The stack behind this suite is one dev-mode uvicorn process (`--reload`,
  // not multi-worker) plus one Postgres/Neo4j container each -- it isn't
  // built to absorb many concurrent full user journeys. Too much
  // parallelism here shows up as flaky timeouts, not real bugs.
  workers: 3,
  reporter: [["html", { open: "never" }], ["list"]],
  globalSetup: "./tests/e2e/global-setup.ts",
  globalTeardown: "./tests/e2e/global-teardown.ts",
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8080",
    trace: "on-first-retry",
    video: "retain-on-failure",
    screenshot: "only-on-failure",
    actionTimeout: 10_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
