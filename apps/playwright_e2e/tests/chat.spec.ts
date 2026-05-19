import { expect, test } from "@playwright/test";
import { isBackendHealthy, waitForChatSession } from "./helpers";

test.describe("chat page (UI)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chat");
    await expect(page.getByRole("heading", { name: "Chat" })).toBeVisible();
  });

  test("renders composer and session actions", async ({ page }) => {
    await expect(page.getByPlaceholder("Ask a question…")).toBeVisible();
    await expect(page.getByRole("button", { name: "Send" })).toBeVisible();
    await expect(page.getByRole("button", { name: "New Chat" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Stop" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Delete active session" })).toBeVisible();
  });

  test("shows restore or empty-state copy", async ({ page }) => {
    await expect(
      page
        .getByText("Ask a question to search the public web.")
        .or(page.getByText("Restoring conversation…"))
        .or(page.getByRole("alert")),
    ).toBeVisible({ timeout: 15_000 });
  });

  test("disables send for empty input when session is ready", async ({ page, request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running on :8000");
    test.skip((await waitForChatSession(page)) !== "ready", "Chat session did not become ready");

    const composer = page.getByPlaceholder("Ask a question…");
    await expect(page.getByRole("button", { name: "Send" })).toBeDisabled();
    await composer.fill("Hello");
    await expect(page.getByRole("button", { name: "Send" })).toBeEnabled();
    await composer.fill("");
    await expect(page.getByRole("button", { name: "Send" })).toBeDisabled();
  });
});

test.describe("chat page (with backend)", () => {
  test.beforeEach(async ({ page, request }) => {
    test.skip(!(await isBackendHealthy(request)), "Backend is not running on :8000");
    await page.goto("/chat");
    test.skip((await waitForChatSession(page)) !== "ready", "Chat session did not become ready");
  });

  test("creates a new chat session", async ({ page }) => {
    await page.getByRole("button", { name: "New Chat" }).click();
    await expect(page.getByText("Ask a question to search the public web.")).toBeVisible();
    await expect(page.getByPlaceholder("Ask a question…")).toBeEnabled();
  });

  test("submits a message and shows assistant activity", async ({ page }) => {
    const question = "What is DuckDuckGo?";
    await page.getByPlaceholder("Ask a question…").fill(question);
    await page.getByRole("button", { name: "Send" }).click();

    await expect(page.locator(".chat-message-user")).toContainText(question);
    await expect(
      page
        .getByText("Searching public web results")
        .or(page.locator(".chat-message-assistant")),
    ).toBeVisible({ timeout: 30_000 });
  });
});
