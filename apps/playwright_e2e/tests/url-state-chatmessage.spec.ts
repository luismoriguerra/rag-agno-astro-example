import { expect, test } from "@playwright/test";
import { isBackendHealthy, waitForChatSession } from "./helpers";

// ── URL State: Research List Pagination ──

test.describe("url state — research list pagination", () => {
  test("page_size param persists in URL after changing dropdown", async ({ page }) => {
    await page.goto("/");
    const dropdown = page.locator("select");
    if (await dropdown.isVisible({ timeout: 10_000 })) {
      await dropdown.selectOption("5");
      await page.waitForTimeout(500);
      expect(page.url()).toContain("page_size=5");
    }
  });

  test("page param appears when navigating to page 2", async ({ page, request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running");
    await page.goto("/");
    // Only testable if there are enough sessions for pagination
    const nextBtn = page.getByRole("button", { name: /next/i });
    if (await nextBtn.isVisible({ timeout: 5_000 }) && await nextBtn.isEnabled()) {
      await nextBtn.click();
      await page.waitForTimeout(500);
      expect(page.url()).toContain("page=2");
    }
  });

  test("default page/page_size values are not in URL", async ({ page }) => {
    await page.goto("/");
    await page.waitForTimeout(1_000);
    const url = new URL(page.url());
    expect(url.searchParams.has("page")).toBe(false);
    expect(url.searchParams.has("page_size")).toBe(false);
  });

  test("page_size from URL is respected on load", async ({ page }) => {
    await page.goto("/?page_size=5");
    const dropdown = page.locator("select");
    if (await dropdown.isVisible({ timeout: 5_000 })) {
      await expect(dropdown).toHaveValue("5");
    }
  });
});

// ── URL State: Research Workspace run_id ──

test.describe("url state — research workspace run_id", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running");
  });

  test("run_id appears in URL after creating session", async ({ page }) => {
    await page.goto("/");
    const textarea = page.getByRole("textbox");
    await textarea.click();
    await textarea.pressSequentially("E2E url state test", { delay: 5 });
    await page.waitForTimeout(200);
    await page.getByRole("button", { name: /research & draft/i }).click();
    await page.waitForURL(/\/research\/[\w-]+/, { timeout: 30_000 });

    expect(page.url()).toContain("run_id=");
  });

  test("run_id is removed from URL after generation completes", async ({ page }) => {
    test.setTimeout(180_000);
    await page.goto("/");
    const textarea = page.getByRole("textbox");
    await textarea.click();
    await textarea.pressSequentially("E2E run_id cleanup. Be very concise, 1 paragraph.", { delay: 5 });
    await page.waitForTimeout(200);
    await page.getByRole("button", { name: /research & draft/i }).click();
    await page.waitForURL(/\/research\/[\w-]+/, { timeout: 30_000 });

    // Wait for generation to complete (send button reappears)
    await expect(page.getByPlaceholder(/refine/i)).toBeVisible({ timeout: 120_000 });
    await expect(page.getByRole("button", { name: /send/i })).toBeVisible({ timeout: 10_000 });

    // After done, run_id should be removed
    await expect.poll(() => page.url(), { timeout: 15_000 }).not.toContain("run_id=");
  });
});

// ── ChatMessage: Markdown Rendering ──

test.describe("chat message — markdown rendering in /chat", () => {
  test.beforeEach(async ({ page, request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running");
    await page.goto("/chat");
    test.skip((await waitForChatSession(page)) !== "ready", "Chat session did not become ready");
  });

  test("chat page uses light theme (no dark background)", async ({ page }) => {
    const bgColor = await page.locator("div.flex.flex-col.h-full.bg-white").first().evaluate(
      (el) => getComputedStyle(el).backgroundColor,
    );
    // Should be white or near-white, not the old dark theme
    expect(bgColor).toMatch(/rgb\(255, 255, 255\)|rgba\(255, 255, 255/);
  });

  test("user messages are right-aligned", async ({ page }) => {
    await page.getByPlaceholder("Ask a question...").fill("Hello world");
    await page.getByRole("button", { name: "Send" }).click();

    const userBubble = page.locator("div.flex.justify-end").first();
    await expect(userBubble).toBeVisible({ timeout: 5_000 });
  });

  test("assistant messages render markdown (not plain text)", async ({ page }) => {
    test.setTimeout(60_000);
    await page.getByPlaceholder("Ask a question...").fill("What is **Markdown**? Reply in one sentence using bold text.");
    await page.getByRole("button", { name: "Send" }).click();

    // Wait for assistant response with markdown container
    const markdownContainer = page.locator(".chat-markdown").first();
    await expect(markdownContainer).toBeVisible({ timeout: 30_000 });

    // Should contain rendered HTML (e.g. <strong> tag), not raw **text**
    await expect.poll(async () => {
      const html = await markdownContainer.innerHTML();
      return html.includes("<strong>") || html.includes("<p>");
    }, { timeout: 30_000 }).toBe(true);
  });
});

// ── ChatMessage: Research Chat ──

test.describe("chat message — research chat layout", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running");
  });

  test("research chat shows agent avatar and markdown content", async ({ page }) => {
    test.setTimeout(180_000);
    await page.goto("/");
    const textarea = page.getByRole("textbox");
    await textarea.click();
    await textarea.pressSequentially("E2E markdown test. Be very concise, 1 paragraph.", { delay: 5 });
    await page.waitForTimeout(200);
    await page.getByRole("button", { name: /research & draft/i }).click();
    await page.waitForURL(/\/research\/[\w-]+/, { timeout: 30_000 });

    // Wait for agent response
    const markdownBlock = page.locator(".chat-markdown").first();
    await expect(markdownBlock).toBeVisible({ timeout: 120_000 });

    // Agent label should be visible
    await expect(page.getByText("Research Agent")).toBeVisible({ timeout: 5_000 });
  });
});
