// Brings up the full stack (Postgres, Neo4j, API, built frontend) via the
// root docker-compose.yml + docker-compose.e2e.yml override, then runs
// migrations and seeds the demo dataset (50 real jobs + courses + skills)
// so Job Explorer / Recommendations specs have real data to assert against.
import { execSync } from "node:child_process";
import path from "node:path";

// Playwright is always run via `npm run test:e2e` from frontend/, so cwd is
// frontend/ -- resolving from there avoids __dirname, which isn't available
// once this file loads as an ES module (package.json has "type": "module").
const REPO_ROOT = path.resolve(process.cwd(), "..");
const COMPOSE_PROJECT = "careergraph-e2e";
const COMPOSE_FILES = "-f docker-compose.yml -f docker-compose.e2e.yml";
const COMPOSE = `docker compose -p ${COMPOSE_PROJECT} ${COMPOSE_FILES}`;

function run(cmd: string): void {
  console.log(`[e2e:global-setup] ${cmd}`);
  execSync(cmd, { cwd: REPO_ROOT, stdio: "inherit" });
}

// `docker compose up --wait` only waits on containers with a healthcheck
// (postgres, neo4j) -- the api container itself has none, so uvicorn may
// still be starting up when this returns. Poll its health endpoint before
// declaring the stack ready.
async function waitForApiHealth(url: string, timeoutMs = 60_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Not up yet -- keep polling.
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  throw new Error(`[e2e:global-setup] API did not become healthy at ${url} within ${timeoutMs}ms`);
}

export default async function globalSetup(): Promise<void> {
  if (process.env.E2E_SKIP_STACK === "1") {
    console.log("[e2e:global-setup] E2E_SKIP_STACK=1 set, assuming stack is already running.");
    return;
  }

  run(`${COMPOSE} up -d --build --wait`);
  run(`${COMPOSE} exec -T api alembic upgrade head`);
  run(`${COMPOSE} exec -T api python -m app.etl.seed_demo_data`);

  const healthUrl = `${process.env.E2E_API_BASE_URL ?? "http://localhost:8001"}/health`;
  console.log(`[e2e:global-setup] waiting for ${healthUrl} ...`);
  await waitForApiHealth(healthUrl);
}
