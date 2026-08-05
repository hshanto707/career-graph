import { test as base, expect, type APIRequestContext, type Page } from "@playwright/test";
import { makeTestUser, type TestUserCandidate } from "./users";
import { deleteTestUser } from "./db";

export function apiBaseURL(): string {
  return process.env.E2E_API_BASE_URL ?? "http://localhost:8001";
}

interface StoredAuthUser {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

interface RegisterResult {
  token: string;
  user: StoredAuthUser;
}

/** Hits POST /auth/register directly -- used both by the authedUser fixture
 * (fast setup for tests that aren't testing registration itself) and by
 * specs that need a pre-existing user (e.g. the login spec, or the
 * duplicate-email case in the registration spec). */
export async function registerViaApi(
  request: APIRequestContext,
  candidate: TestUserCandidate
): Promise<RegisterResult> {
  const response = await request.post(`${apiBaseURL()}/auth/register`, {
    data: { name: candidate.name, email: candidate.email, password: candidate.password },
  });
  expect(response.ok(), `registerViaApi failed: ${await response.text()}`).toBeTruthy();
  const body = await response.json();
  return body.data as RegisterResult;
}

export interface ProfileUpdatePayload {
  major?: string | null;
  graduation_year?: number;
  skills?: Array<{ name: string; proficiency: number; years: number }>;
  target_roles?: string[];
}

/** Hits PUT /profile directly -- lets recommendation/job-explorer specs seed
 * a completed profile without re-testing the EditProfile form (that's
 * profile-completion.spec.ts's job). */
export async function updateProfileViaApi(
  request: APIRequestContext,
  token: string,
  payload: ProfileUpdatePayload
): Promise<void> {
  const response = await request.put(`${apiBaseURL()}/profile`, {
    headers: { Authorization: `Bearer ${token}` },
    data: payload,
  });
  expect(response.ok(), `updateProfileViaApi failed: ${await response.text()}`).toBeTruthy();
}

const AUTH_STORAGE_KEY = "careergraph.auth";

/** Injects a token/user into localStorage so the page loads already
 * authenticated, without going through the login UI. */
export async function signInAs(page: Page, token: string, user: StoredAuthUser): Promise<void> {
  await page.goto("/");
  await page.evaluate(
    ({ key, token, user }) => {
      window.localStorage.setItem(key, JSON.stringify({ token, user }));
    },
    { key: AUTH_STORAGE_KEY, token, user }
  );
}

export async function readStoredAuth(page: Page): Promise<RegisterResult | null> {
  return page.evaluate((key) => {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  }, AUTH_STORAGE_KEY);
}

interface AuthFixtures {
  /** A freshly registered user, already "logged in" (localStorage primed)
   * on `page`. Its Postgres row + Neo4j node are deleted after the test. */
  authedUser: RegisterResult;
}

export const test = base.extend<AuthFixtures>({
  // auto: true -- Playwright only instantiates a fixture a test actually
  // destructures. Every spec that imports `test` from here is an
  // authenticated-app spec, so this must run even for tests that don't need
  // the returned user object directly (e.g. job-explorer.spec.ts), or they
  // silently run as a logged-out page and get redirected by ProtectedRoute.
  authedUser: [async ({ page, request }, use, testInfo) => {
    const candidate = makeTestUser(testInfo);
    const result = await registerViaApi(request, candidate);

    await signInAs(page, result.token, result.user);
    await page.goto("/dashboard");

    await use(result);

    await deleteTestUser(result.user.id);
  }, { auto: true }],
});

export { expect };
