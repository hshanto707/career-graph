// Direct DB cleanup for E2E test data. Deliberately bypasses the backend API
// (there is no delete-account endpoint, and we chose not to add one just for
// test cleanup -- see docs/e2e-test-plan.md) and instead mirrors the two
// facts already true of the schema:
//   - `student_profiles.user_id` has ON DELETE CASCADE onto `users.id`
//     (backend/app/models/profile.py), so deleting the Postgres user row
//     also removes their profile.
//   - The Neo4j `Student` node is keyed by that same id, with outgoing
//     HAS_SKILL/TARGETS edges onto shared, MERGE'd Skill/Job nodes
//     (app/services/graph_service.py) -- DETACH DELETE on just the Student
//     node removes it and its edges without touching data other tests rely
//     on.
import { Client } from "pg";
import neo4j from "neo4j-driver";

// Defaults match docker-compose.e2e.yml's remapped host ports (5433/7688),
// not docker-compose.yml's defaults (5432/7687) -- the e2e stack runs
// alongside a dev stack that may already be using the latter.
const PG_CONFIG = {
  host: process.env.E2E_PG_HOST ?? "localhost",
  port: Number(process.env.E2E_PG_PORT ?? 5433),
  user: process.env.E2E_PG_USER ?? "careergraph",
  password: process.env.E2E_PG_PASSWORD ?? "careergraph",
  database: process.env.E2E_PG_DATABASE ?? "careergraph",
};

const NEO4J_URI = process.env.E2E_NEO4J_URI ?? "bolt://localhost:7688";
const NEO4J_USER = process.env.E2E_NEO4J_USER ?? "neo4j";
const NEO4J_PASSWORD = process.env.E2E_NEO4J_PASSWORD ?? "careergraph";

function neo4jDriver() {
  return neo4j.driver(NEO4J_URI, neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD));
}

/** Deletes a single test user's data from both stores. Call this after every
 * test that created a user (see fixtures/auth.ts). */
export async function deleteTestUser(userId: string): Promise<void> {
  const pg = new Client(PG_CONFIG);
  await pg.connect();
  try {
    await pg.query("DELETE FROM users WHERE id = $1", [userId]);
  } finally {
    await pg.end();
  }

  const driver = neo4jDriver();
  try {
    const session = driver.session();
    try {
      await session.run("MATCH (s:Student {id: $id}) DETACH DELETE s", { id: userId });
    } finally {
      await session.close();
    }
  } finally {
    await driver.close();
  }
}

/** Safety-net sweep for a whole run: deletes any user whose email matches
 * this run's prefix, in case a test crashed before its own cleanup ran.
 * Returns the number of users removed. */
export async function sweepTestUsers(emailPrefix: string): Promise<number> {
  const pg = new Client(PG_CONFIG);
  await pg.connect();
  let ids: string[] = [];
  try {
    const result = await pg.query("SELECT id FROM users WHERE email LIKE $1", [`${emailPrefix}%`]);
    ids = result.rows.map((row: { id: string }) => row.id);
    if (ids.length > 0) {
      await pg.query("DELETE FROM users WHERE id = ANY($1)", [ids]);
    }
  } finally {
    await pg.end();
  }

  if (ids.length > 0) {
    const driver = neo4jDriver();
    try {
      const session = driver.session();
      try {
        await session.run("MATCH (s:Student) WHERE s.id IN $ids DETACH DELETE s", { ids });
      } finally {
        await session.close();
      }
    } finally {
      await driver.close();
    }
  }

  return ids.length;
}
