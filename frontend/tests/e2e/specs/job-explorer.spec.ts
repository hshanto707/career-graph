import { test, expect } from "../fixtures/auth";

test.describe("job explorer", () => {
  test("browsing jobs shows results from the seeded catalog", async ({ page }) => {
    await page.goto("/jobs");

    await expect(page.getByText(/Showing \d+ jobs?/)).toBeVisible();
    await expect(page.getByRole("heading", { level: 3 }).first()).toBeVisible();
  });

  test("searching for a nonexistent job shows the empty state", async ({ page }) => {
    await page.goto("/jobs");

    await page.getByLabel("Search jobs or companies").fill("zzznonexistentrolexyz123");

    await expect(page.getByText("No jobs match your filters")).toBeVisible();
    await expect(page.getByText("Couldn't load jobs")).not.toBeVisible();
  });

  test("filtering by type does not error", async ({ page }) => {
    await page.goto("/jobs");
    await expect(page.getByText(/Showing \d+ jobs?/)).toBeVisible();

    await page.getByLabel("Filter by job type").selectOption("Full-time");

    await expect(page.getByText("Couldn't load jobs")).not.toBeVisible();
  });

  test("opening a job shows its details", async ({ page }) => {
    await page.goto("/jobs");
    await expect(page.getByText(/Showing \d+ jobs?/)).toBeVisible();

    const firstJobHeading = page.getByRole("heading", { level: 3 }).first();
    const jobTitle = await firstJobHeading.textContent();
    await firstJobHeading.click();

    await expect(page.getByRole("heading", { name: jobTitle ?? "" }).last()).toBeVisible();
  });
});
