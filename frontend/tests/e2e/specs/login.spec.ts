import { test, expect } from "@playwright/test";
import { makeTestUser } from "../fixtures/users";
import { registerViaApi } from "../fixtures/auth";
import { deleteTestUser } from "../fixtures/db";

test.describe("login", () => {
  test("correct credentials log the user in", async ({ page, request }, testInfo) => {
    const candidate = makeTestUser(testInfo);
    const registered = await registerViaApi(request, candidate);

    try {
      await page.goto("/");
      await page.getByLabel("Email").fill(candidate.email);
      await page.getByLabel("Password").fill(candidate.password);
      await page.getByRole("button", { name: "Sign In" }).click();

      await expect(page).toHaveURL(/\/dashboard$/);
      await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    } finally {
      await deleteTestUser(registered.user.id);
    }
  });

  test("wrong password is rejected", async ({ page, request }, testInfo) => {
    const candidate = makeTestUser(testInfo);
    const registered = await registerViaApi(request, candidate);

    try {
      await page.goto("/");
      await page.getByLabel("Email").fill(candidate.email);
      await page.getByLabel("Password").fill("TheWrongPassword1!");
      await page.getByRole("button", { name: "Sign In" }).click();

      await expect(page.getByRole("alert")).toContainText("Invalid email or password.");
      await expect(page).toHaveURL(/\/$/);
    } finally {
      await deleteTestUser(registered.user.id);
    }
  });

  test("unknown email is rejected with the same generic message", async ({ page }, testInfo) => {
    const candidate = makeTestUser(testInfo);

    await page.goto("/");
    await page.getByLabel("Email").fill(candidate.email);
    await page.getByLabel("Password").fill(candidate.password);
    await page.getByRole("button", { name: "Sign In" }).click();

    await expect(page.getByRole("alert")).toContainText("Invalid email or password.");
    await expect(page).toHaveURL(/\/$/);
  });
});
