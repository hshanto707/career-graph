import { test, expect } from "@playwright/test";
import { makeTestUser } from "../fixtures/users";
import { readStoredAuth } from "../fixtures/auth";
import { deleteTestUser } from "../fixtures/db";

// The full journey: register -> login lands automatically -> complete
// profile -> see recommendations -> explore jobs. Tagged @smoke so it can be
// run on its own with `playwright test --grep @smoke` as a fast sanity check.
test("register, complete profile, see recommendations, explore jobs @smoke", async ({ page }, testInfo) => {
  const candidate = makeTestUser(testInfo);
  const gradYear = new Date().getFullYear() + 1;

  await page.goto("/register");
  await page.getByLabel("Full Name").fill(candidate.name);
  await page.getByLabel("Email").fill(candidate.email);
  await page.getByLabel("Password").fill(candidate.password);
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page).toHaveURL(/\/dashboard$/);

  try {
    await page.getByRole("link", { name: "Recommendations" }).click();
    // An empty profile still shows the ranked job catalog, just at 0% fit
    // for every role -- there's no "blocked" empty state to wait for here.
    await expect(page.getByText(/skill fit of 0% with this role/).first()).toBeVisible();
    await page.getByRole("link", { name: "Profile" }).click();
    await page.getByRole("link", { name: "Edit Profile" }).click();
    await expect(page).toHaveURL(/\/profile\/edit$/);

    await page.getByLabel("Major").fill("Computer Science");
    await page.keyboard.press("Escape");

    await page.getByRole("combobox", { name: /Graduation Year/ }).click();
    await page.getByRole("option", { name: String(gradYear) }).click();

    await page.getByLabel("Skill name").fill("Python");
    await page.keyboard.press("Escape");
    await page.getByLabel("Proficiency (0-10)").fill("8");
    await page.getByLabel("Years").fill("2");
    await page.getByRole("button", { name: "Add Skill" }).click();
    await expect(page.getByText(/Python.*P8.*2y/)).toBeVisible();

    const targetRolesSection = page.locator("div.stat-card", {
      has: page.getByRole("heading", { name: "Target Job Roles" }),
    });
    await targetRolesSection.getByLabel("New target role").fill("Software Engineer");
    await page.keyboard.press("Escape");
    await targetRolesSection.getByRole("button", { name: "Add" }).click();

    await page.getByRole("button", { name: /Save Changes/ }).click();
    await expect(page).toHaveURL(/\/profile$/);

    await page.getByRole("link", { name: "Recommendations" }).click();
    await expect(page.getByRole("tab", { name: "Jobs" })).toBeVisible();
    // React Query serves the stale (0%) cached result instantly on this
    // client-side nav, then silently refetches in the background once the
    // profile-update invalidation kicks in -- a one-shot read here can catch
    // that stale snapshot, so poll until a non-zero score actually lands.
    await expect
      .poll(
        async () => {
          const scores = await page.locator(".match-score:visible").allTextContents();
          return scores.some((score) => parseInt(score, 10) > 0);
        },
        { message: "expected at least one non-zero match score after the profile update refetch" }
      )
      .toBe(true);

    await page.getByRole("link", { name: "Job Explorer" }).click();
    await expect(page).toHaveURL(/\/jobs$/);
    await expect(page.getByText(/Showing \d+ jobs?/)).toBeVisible();
    await expect(page.getByRole("heading", { level: 3 }).first()).toBeVisible();
  } finally {
    const stored = await readStoredAuth(page);
    if (stored) {
      await deleteTestUser(stored.user.id);
    }
  }
});
