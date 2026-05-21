import { expect, test } from "@playwright/test";
import { isBackendHealthy } from "./helpers";

async function fillResearchIdea(page: import("@playwright/test").Page, idea: string) {
  const textarea = page.getByRole("textbox");
  await textarea.click();
  await textarea.pressSequentially(idea, { delay: 10 });
  await page.waitForTimeout(200);
}

async function createSessionAndWaitForArticle(page: import("@playwright/test").Page, idea: string) {
  await page.goto("/");
  await fillResearchIdea(page, idea);
  await page.getByRole("button", { name: /research & draft/i }).click();
  await page.waitForURL(/\/research\/[\w-]+/, { timeout: 30_000 });

  // Wait for the article to render — look for version badge (v1) which only appears when article exists
  await expect(page.getByText(/^v1$/)).toBeVisible({ timeout: 240_000 });
}

// ── Home page UI ──

test.describe("research — home page (UI)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("shows navbar with logo and nav links", async ({ page }) => {
    await expect(page.getByRole("link", { name: "Lumen" })).toBeVisible();
    await expect(page.getByRole("link", { name: /home/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /chat/i })).toBeVisible();
  });

  test("shows compose area with textarea and submit button", async ({ page }) => {
    await expect(page.getByRole("textbox")).toBeVisible();
    await expect(page.getByRole("button", { name: /research & draft/i })).toBeVisible();
  });

  test("submit button is disabled when textarea is empty", async ({ page }) => {
    await expect(page.getByRole("button", { name: /research & draft/i })).toBeDisabled();
  });

  test("submit button enables when text is entered", async ({ page }) => {
    await fillResearchIdea(page, "WebAssembly 2026");
    await expect(page.getByRole("button", { name: /research & draft/i })).toBeEnabled({ timeout: 5_000 });
  });

  test("shows research list or empty state", async ({ page }) => {
    await expect(
      page.getByText(/no research sessions/i)
        .or(page.getByText(/drafts/i)),
    ).toBeVisible({ timeout: 10_000 });
  });
});

// ── Session creation ──

test.describe("research — session creation (with backend)", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running");
  });

  test("submitting an idea creates a session and redirects", async ({ page }) => {
    await page.goto("/");
    await fillResearchIdea(page, "E2E small modular reactors");
    await page.getByRole("button", { name: /research & draft/i }).click();
    await page.waitForURL(/\/research\/[\w-]+/, { timeout: 30_000 });
    expect(page.url()).toMatch(/\/research\/[\w-]+/);
  });
});

// ── Workspace page ──

test.describe("research — workspace (with backend)", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running");
  });

  test("workspace loads with chat and article panels", async ({ page }) => {
    await page.goto("/");
    await fillResearchIdea(page, "E2E state of Rust");
    await page.getByRole("button", { name: /research & draft/i }).click();
    await page.waitForURL(/\/research\/[\w-]+/, { timeout: 30_000 });

    await expect(page.getByRole("heading", { name: /research thread/i })).toBeVisible({ timeout: 15_000 });
  });

  test("navbar shows on workspace page with home link", async ({ page }) => {
    await page.goto("/");
    await fillResearchIdea(page, "E2E navbar check");
    await page.getByRole("button", { name: /research & draft/i }).click();
    await page.waitForURL(/\/research\/[\w-]+/, { timeout: 30_000 });

    await expect(page.getByRole("link", { name: "Lumen" })).toBeVisible();
    await expect(page.getByRole("link", { name: /home/i })).toBeVisible();
  });
});

// ── Article generation ──

test.describe("research — article generation (with backend, long)", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running");
  });

  test("generates an article with TL;DR", async ({ page }) => {
    test.setTimeout(300_000);

    await createSessionAndWaitForArticle(page, "E2E comparison Deno vs Bun");

    const pageContent = await page.content();
    expect(pageContent.toLowerCase()).toContain("tl;dr");
  });
});

// ── Article refinement (edition) ──

test.describe("research — article refinement (with backend, long)", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running");
  });

  test("sending a follow-up prompt updates the article", async ({ page }) => {
    test.setTimeout(360_000);

    await createSessionAndWaitForArticle(page, "E2E OpenFGA authorization");

    // Capture the initial article text
    const articleBefore = await page.locator("main").textContent();

    // Find the chat input and send a refinement
    const chatInput = page.getByPlaceholder(/refine/i);
    await expect(chatInput).toBeVisible({ timeout: 10_000 });
    await chatInput.click();
    await chatInput.pressSequentially("Add a section about performance benchmarks", { delay: 10 });
    await page.waitForTimeout(200);
    await page.getByRole("button", { name: /send/i }).click();

    // Send should be disabled during run
    await expect(page.getByRole("button", { name: /stop/i })).toBeVisible({ timeout: 10_000 });

    // Wait for the article to update (new heading or content change)
    await expect(async () => {
      const articleAfter = await page.locator("main").textContent();
      expect(articleAfter).not.toBe(articleBefore);
      expect(articleAfter?.toLowerCase()).toContain("benchmark");
    }).toPass({ timeout: 240_000 });
  });

  test("version badge increments after refinement", async ({ page }) => {
    test.setTimeout(360_000);

    await createSessionAndWaitForArticle(page, "E2E version test topic");

    // Should see v1 badge
    await expect(page.getByText(/v1/)).toBeVisible({ timeout: 10_000 });

    // Send refinement
    const chatInput = page.getByPlaceholder(/refine/i);
    await expect(chatInput).toBeVisible({ timeout: 10_000 });
    await chatInput.click();
    await chatInput.pressSequentially("Add a conclusion section", { delay: 10 });
    await page.waitForTimeout(200);
    await page.getByRole("button", { name: /send/i }).click();

    // Wait for v2 badge
    await expect(page.getByText(/v2/)).toBeVisible({ timeout: 240_000 });
  });
});

// ── Article controls ──

test.describe("research — article controls (with backend, long)", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running");
  });

  test("can toggle article status to published and back", async ({ page }) => {
    test.setTimeout(300_000);

    await createSessionAndWaitForArticle(page, "E2E publish toggle test");

    // Click Publish button
    const publishBtn = page.getByRole("button", { name: /publish/i });
    await expect(publishBtn).toBeVisible({ timeout: 10_000 });
    await publishBtn.click();

    // Should now show "Published"
    await expect(page.getByRole("button", { name: /published/i })).toBeVisible({ timeout: 5_000 });

    // Click again to unpublish
    await page.getByRole("button", { name: /published/i }).click();
    await expect(page.getByRole("button", { name: /publish/i })).toBeVisible({ timeout: 5_000 });
  });

  test("download button triggers .md download", async ({ page }) => {
    test.setTimeout(300_000);

    await createSessionAndWaitForArticle(page, "E2E download test");

    const downloadBtn = page.getByRole("button", { name: /\.md/i });
    await expect(downloadBtn).toBeVisible({ timeout: 10_000 });

    const [download] = await Promise.all([
      page.waitForEvent("download", { timeout: 10_000 }),
      downloadBtn.click(),
    ]);

    expect(download.suggestedFilename()).toMatch(/\.md$/);
  });
});

// ── Home page list ──

test.describe("research — home page list (with backend)", () => {
  test.beforeEach(async ({ request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running");
  });

  test("session appears in list after creation", async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto("/");
    const uniqueTopic = `E2E list ${Date.now()}`;
    await fillResearchIdea(page, uniqueTopic);
    await page.getByRole("button", { name: /research & draft/i }).click();
    await page.waitForURL(/\/research\/[\w-]+/, { timeout: 30_000 });

    await page.goto("/");
    await expect(page.getByText(uniqueTopic.substring(0, 20))).toBeVisible({ timeout: 15_000 });
  });

  test("page size dropdown changes list", async ({ page }) => {
    await page.goto("/");
    const dropdown = page.locator("select");
    if (await dropdown.isVisible()) {
      await dropdown.selectOption("5");
      await page.waitForTimeout(1_000);
      await expect(
        page.getByText(/drafts/i).or(page.getByText(/no research sessions/i)),
      ).toBeVisible();
    }
  });
});
