import { expect, test, type Page } from "@playwright/test";

function getRequiredEnv(name: string): string {
  const value = process.env[name];

  if (!value) {
    throw new Error(`${name} must be set to run Playwright admin smoke tests.`);
  }

  return value;
}

async function signInAsAdmin(page: Page) {
  const email = getRequiredEnv("PLAYWRIGHT_ADMIN_EMAIL");
  const password = getRequiredEnv("PLAYWRIGHT_ADMIN_PASSWORD");

  await page.goto("/dashboard");

  const signInButton = page.getByRole("button", { name: "Sign in" });
  const dashboard = page.getByRole("heading", { name: "Operations Summary" });

  // Wait for auth state to settle: either the sign-in form or the dashboard appears
  await Promise.race([
    signInButton.waitFor({ state: "visible", timeout: 20000 }),
    dashboard.waitFor({ state: "visible", timeout: 20000 }),
  ]);

  if (await signInButton.isVisible()) {
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    // window.location.reload() is called after sign-in — wait for the navigation
    await Promise.all([
      page.waitForURL("**/dashboard", { timeout: 30000 }),
      signInButton.click(),
    ]);
  }

  await expect(dashboard).toBeVisible({ timeout: 15000 });
}

async function openFirstLinkNamed(page: Page, name: string) {
  const link = page.getByRole("link", { name }).first();
  await expect(link).toBeVisible();
  await link.click();
}

test.describe("admin smoke flows", () => {
  test.beforeEach(async ({ page }) => {
    await signInAsAdmin(page);
  });

  test("admin sees dashboard", async ({ page }) => {
    await page.goto("/dashboard");

    await expect(page.getByRole("heading", { name: "Operations Summary" })).toBeVisible();
    await expect(page.getByText("Admin Queue")).toBeVisible();
  });

  test("admin opens Daily Submissions", async ({ page }) => {
    await page.goto("/daily-submissions");

    await expect(page.getByRole("heading", { name: "Daily Submissions" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Export CSV" })).toBeVisible();
  });

  test("admin filters Daily Submissions", async ({ page }) => {
    await page.goto("/daily-submissions");

    await page.getByLabel("Date").fill("2026-04-22");

    await expect(page).toHaveURL(/work_date=2026-04-22/);
  });

  test("admin opens Daily Submission Detail", async ({ page }) => {
    await page.goto("/daily-submissions");
    await openFirstLinkNamed(page, "Open");

    await expect(page.getByRole("button", { name: "Edit Submission" }).first()).toBeVisible();
    await expect(page.getByText("Active Attachment")).toBeVisible();
  });

  test("admin opens edit drawer from Daily Submission Detail", async ({ page }) => {
    await page.goto("/daily-submissions");
    await openFirstLinkNamed(page, "Open");

    await page.getByRole("button", { name: "Edit Submission" }).first().click();

    await expect(page.getByRole("dialog", { name: "Edit Submission" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Save" })).toBeVisible();
  });

  test("admin opens Workorders", async ({ page }) => {
    await page.goto("/workorders");

    await expect(page.getByRole("heading", { name: "Workorders" })).toBeVisible();
    await expect(page.getByLabel("Workorder Code", { exact: true })).toBeVisible();
  });

  test("admin opens Workorder Detail", async ({ page }) => {
    await page.goto("/workorders");
    await openFirstLinkNamed(page, "Open");

    await expect(page.getByRole("button", { name: "Edit Workorder" })).toBeVisible();
    await expect(page.getByText("Submission History")).toBeVisible();
  });

  test("admin opens Pending Users", async ({ page }) => {
    await page.goto("/users/pending");

    await expect(page.getByRole("heading", { name: "Pending Users" })).toBeVisible();
    await expect(page.getByText("Role requests awaiting admin approval")).toBeVisible();
  });

  test("admin opens No Submission Yet", async ({ page }) => {
    await page.goto("/no-submission-yet");

    await expect(page.getByRole("heading", { name: "No Submission Yet" })).toBeVisible();
    await expect(page.getByText("Meaning of this view")).toBeVisible();
  });

  test("admin opens Reports", async ({ page }) => {
    await page.goto("/reports");

    await expect(page.getByRole("heading", { name: "Reports" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Export Filtered CSV" })).toBeVisible();
  });
});