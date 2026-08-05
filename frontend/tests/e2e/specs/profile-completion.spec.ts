import { test, expect } from "../fixtures/auth";

// Discovered while wiring this suite up against the real backend: an empty
// profile does NOT hide job recommendations -- the engine still ranks and
// returns the full job catalog, just at a 0% skill fit for every role. So
// "recommendations are blocked/unlocked" isn't the right mental model here;
// what actually changes as the profile fills in is the match score.
test.describe("profile completion", () => {
  test("an incomplete profile still shows ranked jobs, all at 0% fit", async ({ page }) => {
    await page.goto("/recommendations");

    await expect(page.getByRole("tab", { name: "Jobs" })).toBeVisible();
    await expect(page.getByText(/skill fit of 0% with this role/).first()).toBeVisible();
  });

  test("completing the profile raises the match score for at least one job", async ({ page }) => {
    const gradYear = new Date().getFullYear() + 1;

    await page.goto("/profile/edit");

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
    await expect(targetRolesSection.getByText("Software Engineer")).toBeVisible();

    await page.getByRole("button", { name: /Save Changes/ }).click();
    await expect(page).toHaveURL(/\/profile$/);

    await page.goto("/recommendations");
    await expect(page.getByRole("tab", { name: "Jobs" })).toBeVisible();

    // allTextContents() is a one-shot read, not an auto-retrying assertion --
    // poll until a non-zero score actually lands (covers both the initial
    // fetch and any stale-then-refetch race from React Query's cache).
    await expect
      .poll(async () => {
        const scores = await page.locator(".match-score:visible").allTextContents();
        return scores.some((score) => parseInt(score, 10) > 0);
      })
      .toBe(true);
  });
});
