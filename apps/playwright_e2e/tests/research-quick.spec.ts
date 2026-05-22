import { expect, test } from "@playwright/test";
import { isBackendHealthy } from "./helpers";

const IDEA = "What is Tavily search API? Be very concise, 2 short paragraphs.";

test.describe("research — quick article generation", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running");
  });

  test("generates article with TL;DR and shows action buttons", async ({ page }) => {
    test.setTimeout(180_000);

    await page.goto("/");
    const textarea = page.getByRole("textbox");
    await textarea.click();
    await textarea.pressSequentially(IDEA, { delay: 5 });
    await page.waitForTimeout(200);
    await page.getByRole("button", { name: /research & draft/i }).click();
    await page.waitForURL(/\/research\/[\w-]+/, { timeout: 30_000 });

    // Article should render with TL;DR
    await expect(page.getByText(/tl;dr/i)).toBeVisible({ timeout: 120_000 });

    // Version badge visible
    await expect(page.getByText(/^v\d+$/)).toBeVisible({ timeout: 10_000 });

    // Chat response from agent visible via markdown-rendered message
    await expect(page.locator(".chat-markdown").first()).toBeVisible({ timeout: 5_000 });

    // Action buttons should appear after article generation
    await expect(
      page.getByRole("button").filter({ hasText: /add|compare|include|expand|improve/i }).first(),
    ).toBeVisible({ timeout: 15_000 });
  });
});
