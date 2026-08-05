// Safety-net sweep for any test that crashed before its own per-test
// cleanup ran (see fixtures/db.ts), then tears down the compose stack.
// Ephemeral (tmpfs) volumes mean `down -v` always leaves a clean slate.
import { execSync } from "node:child_process";
import path from "node:path";
import { emailPrefixForRun } from "./fixtures/users";
import { sweepTestUsers } from "./fixtures/db";

// Playwright is always run via `npm run test:e2e` from frontend/, so cwd is
// frontend/ -- resolving from there avoids __dirname, which isn't available
// once this file loads as an ES module (package.json has "type": "module").
const REPO_ROOT = path.resolve(process.cwd(), "..");
const COMPOSE_PROJECT = "careergraph-e2e";
const COMPOSE_FILES = "-f docker-compose.yml -f docker-compose.e2e.yml";
const COMPOSE = `docker compose -p ${COMPOSE_PROJECT} ${COMPOSE_FILES}`;

export default async function globalTeardown(): Promise<void> {
  const runId = process.env.E2E_RUN_ID;
  if (runId) {
    try {
      const swept = await sweepTestUsers(emailPrefixForRun(runId));
      console.log(`[e2e:global-teardown] swept ${swept} leftover test user(s) for run ${runId}`);
    } catch (err) {
      console.warn("[e2e:global-teardown] sweep failed (stack may already be down):", err);
    }
  }

  if (process.env.E2E_SKIP_STACK === "1") {
    console.log("[e2e:global-teardown] E2E_SKIP_STACK=1 set, leaving stack running.");
    return;
  }

  console.log(`[e2e:global-teardown] ${COMPOSE} down -v`);
  execSync(`${COMPOSE} down -v`, { cwd: REPO_ROOT, stdio: "inherit" });
}
