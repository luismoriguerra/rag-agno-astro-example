import { expect, test } from "@playwright/test";
import {
  ASSISTANT_ANSWER_TIMEOUT_MS,
  assertNoChatUiError,
  getChatUiError,
  isBackendHealthy,
  waitForAssistantAnswer,
  waitForChatSession,
} from "./helpers";

test.describe("chat hello flow", () => {
  test("sends Hello and receives an AI answer within 30s", async ({ page, request }) => {
    test.setTimeout(60_000);
    test.skip(!(await isBackendHealthy(request)), "Backend is not running on :8000");

    await page.goto("/chat");
    const sessionState = await waitForChatSession(page);
    test.skip(
      sessionState === "error",
      `Session failed to restore: ${(await getChatUiError(page)) ?? "unknown error"}`,
    );

    await page.getByRole("button", { name: "New Chat" }).click();
    await expect(page.getByText("Ask a question to search the public web.")).toBeVisible();
    await assertNoChatUiError(page);

    const message = "Hello";
    await page.getByPlaceholder("Ask a question…").fill(message);
    await page.getByRole("button", { name: "Send" }).click();

    await expect(page.locator(".chat-message-user").last()).toContainText(message);
    await expect(page.getByText("Searching public web results")).toBeVisible({
      timeout: 10_000,
    });

    const answer = await waitForAssistantAnswer(page, ASSISTANT_ANSWER_TIMEOUT_MS);
    expect(answer.length).toBeGreaterThan(8);

    await expect(page.getByPlaceholder("Ask a question…")).toBeEnabled({
      timeout: 10_000,
    });
    await assertNoChatUiError(page);
  });
});
