import { test, expect } from "@playwright/test";
import { makeTestUser } from "../fixtures/users";
import { registerViaApi, readStoredAuth } from "../fixtures/auth";
import { deleteTestUser } from "../fixtures/db";

test.describe("registration", () => {
  test("a new user can register and lands on the dashboard", async ({ page }, testInfo) => {
    const candidate = makeTestUser(testInfo);

    await page.goto("/register");
    await page.getByLabel("Full Name").fill(candidate.name);
    await page.getByLabel("Email").fill(candidate.email);
    await page.getByLabel("Password").fill(candidate.password);
    await page.getByRole("button", { name: "Create Account" }).click();

    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

    const stored = await readStoredAuth(page);
    expect(stored?.user.email).toBe(candidate.email);

    if (stored) {
      await deleteTestUser(stored.user.id);
    }
  });

  test("registering with an email that already exists is rejected", async ({ page, request }, testInfo) => {
    const candidate = makeTestUser(testInfo);
    const existing = await registerViaApi(request, candidate);

    try {
      await page.goto("/register");
      await page.getByLabel("Full Name").fill("Second Attempt");
      await page.getByLabel("Email").fill(candidate.email);
      await page.getByLabel("Password").fill("AnotherPass123!");
      await page.getByRole("button", { name: "Create Account" }).click();

      await expect(page.getByRole("alert")).toContainText(/already exists/i);
      await expect(page).toHaveURL(/\/register$/);
    } finally {
      await deleteTestUser(existing.user.id);
    }
  });

  test("invalid input is rejected before any request is sent", async ({ page }) => {
    await page.goto("/register");
    await page.getByRole("button", { name: "Create Account" }).click();

    await expect(page.getByText("Name is required.")).toBeVisible();
    await expect(page.getByText("Email is required.")).toBeVisible();
    await expect(page.getByText("Password must be at least 8 characters.")).toBeVisible();
    await expect(page).toHaveURL(/\/register$/);
  });
});
