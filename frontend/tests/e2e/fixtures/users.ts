import crypto from "node:crypto";
import type { TestInfo } from "@playwright/test";

/** All test users created by this run share this prefix, so global-teardown
 * can sweep any left behind by a crashed test (see global-teardown.ts). */
export function emailPrefixForRun(runId: string): string {
  return `e2e-${runId}-`;
}

export interface TestUserCandidate {
  name: string;
  email: string;
  password: string;
}

/** A unique, throwaway user for a single test. Unique per test (not just per
 * run) so tests can execute concurrently without colliding on email.
 *
 * Deliberately short: RFC 5321 caps the local part (before the @) at 64
 * characters, and `testInfo.testId` alone can exceed that -- a random
 * 8-char suffix is unique enough for a suite this size without the risk. */
export function makeTestUser(testInfo: TestInfo): TestUserCandidate {
  const runId = process.env.E2E_RUN_ID ?? "local";
  const unique = `${testInfo.retry}${crypto.randomBytes(4).toString("hex")}`;
  return {
    name: "E2E Test User",
    email: `${emailPrefixForRun(runId)}${unique}@example.com`.toLowerCase(),
    password: "TestPass123!",
  };
}
