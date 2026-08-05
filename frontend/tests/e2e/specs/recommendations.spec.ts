import { test, expect, updateProfileViaApi } from "../fixtures/auth";

test.describe("recommendations", () => {
  test("recommendations reflect the skills on the profile", async ({ page, request, authedUser }) => {
    await updateProfileViaApi(request, authedUser.token, {
      major: "Computer Science",
      graduation_year: new Date().getFullYear() + 1,
      skills: [{ name: "Python", proficiency: 8, years: 2 }],
      target_roles: ["Software Engineer"],
    });

    await page.goto("/recommendations");

    await expect(page.getByRole("tab", { name: "Jobs" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Skills" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Courses" })).toBeVisible();

    // With a real, seeded "Python" skill on the profile, at least one job's
    // match score should be non-zero -- an empty profile gets 0% on every
    // job (see profile-completion.spec.ts), so this is what "reflects the
    // profile" actually looks like here.
    // allTextContents() is a one-shot read, not an auto-retrying assertion --
    // poll until a non-zero score actually lands (covers both the initial
    // fetch and any stale-then-refetch race from React Query's cache).
    await expect
      .poll(async () => {
        const scores = await page.locator(".match-score:visible").allTextContents();
        return scores.some((score) => parseInt(score, 10) > 0);
      })
      .toBe(true);

    // Switching tabs works without erroring.
    await page.getByRole("tab", { name: "Skills" }).click();
    await expect(page.getByText(/Couldn't load skill recommendations/)).not.toBeVisible();

    await page.getByRole("tab", { name: "Courses" }).click();
    await expect(page.getByText(/Couldn't load course recommendations/)).not.toBeVisible();
  });
});
