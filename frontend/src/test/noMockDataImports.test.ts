import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";

// F8 TODO: "decide fate of mockData.ts -- delete once all pages are wired".
// This is the literal, automatable version of that gate: once every page
// under src/pages is wired to real API hooks, no page module should still
// import from lib/mockData. Until the remaining pages (Dashboard, Jobs,
// Profile, EditProfile, SkillAnalysis) are wired in their own phases, this
// test intentionally stays RED and lists exactly which files still need
// migrating -- that is the point of the check, not a bug in it.

const PAGES_DIR = path.resolve(__dirname, "../pages");

function findMockDataImporters(): string[] {
  const offenders: string[] = [];
  for (const entry of fs.readdirSync(PAGES_DIR)) {
    if (!/\.(tsx|ts)$/.test(entry) || entry.endsWith(".test.tsx") || entry.endsWith(".test.ts")) {
      continue;
    }
    const contents = fs.readFileSync(path.join(PAGES_DIR, entry), "utf-8");
    if (/from\s+['"]@\/lib\/mockData['"]/.test(contents)) {
      offenders.push(entry);
    }
  }
  return offenders;
}

describe("mockData retirement (F8)", () => {
  it("has no page module importing from lib/mockData", () => {
    const offenders = findMockDataImporters();
    expect(
      offenders,
      `These pages still import lib/mockData and need wiring in their own phase: ${offenders.join(", ")}`
    ).toEqual([]);
  });

  it("Recommendations.tsx specifically no longer imports lib/mockData (this phase's scope)", () => {
    const contents = fs.readFileSync(path.join(PAGES_DIR, "Recommendations.tsx"), "utf-8");
    expect(contents).not.toMatch(/from\s+['"]@\/lib\/mockData['"]/);
  });
});
