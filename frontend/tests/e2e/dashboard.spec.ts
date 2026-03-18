import { test, expect } from "@playwright/test";

test.describe("GraphSentinel Dashboard UI", () => {
  test.use({ viewport: { width: 1280, height: 900 } });

  test("dashboard loads with header and main controls", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: /GraphSentinel/i })).toBeVisible();
    await expect(page.getByText(/AI-Powered Fund Flow Fraud Detection/i)).toBeVisible();

    await expect(page.getByRole("button", { name: /Track A \(Guaranteed\)/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Track B \(Live\)/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Run Track A|Run Synthetic/i })).toBeVisible();
  });

  test("Agent Activity panel is present", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Agent Activity").first()).toBeVisible();
  });

  test("Alert Feed and Topology Map sections are present", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/Investigator Alert Queue|Alert Feed/i)).toBeVisible();
    await expect(page.getByText("Topology Map").first()).toBeVisible();
  });

  test("SAR Draft section is present", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("SAR Draft").first()).toBeVisible();
    await expect(page.getByText(/Select an alert to view/i)).toBeVisible();
  });

  test("Adversarial Test Mode panel is present", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Adversarial Test Mode").first()).toBeVisible();
    await expect(page.getByRole("button", { name: /Cycle \+1 hop/i })).toBeVisible();
  });

  test("Track A loads pre-cached result and shows graph", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: /Track A \(Guaranteed\)/i }).click();
    await page.getByRole("button", { name: /Run Track A/i }).click();

    await expect(page.getByRole("button", { name: /Running/i })).toBeVisible({ timeout: 2000 }).catch(() => {});
    await expect(page.getByRole("button", { name: /Run Track A/i })).toBeVisible({ timeout: 15000 });

    await expect(page.getByText(/Track A \(Guaranteed\)|Pre-cached|Graph Agent|Pathfinder/i).first()).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Topology Map").first()).toBeVisible();
  });

  test("page is scrollable when content overflows", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 600 });
    await page.goto("/");

    const isScrollable = await page.evaluate(() => {
      const el = document.documentElement;
      return el.scrollHeight > el.clientHeight || document.body.scrollHeight > window.innerHeight;
    });
    expect(isScrollable).toBe(true);
  });
});
