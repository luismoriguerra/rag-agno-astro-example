import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const backendHealthURL =
  process.env.PLAYWRIGHT_BACKEND_HEALTH_URL ?? "http://localhost:8000/health";

export const ASSISTANT_ANSWER_TIMEOUT_MS = 30_000;

export async function isBackendHealthy(request: APIRequestContext): Promise<boolean> {
  try {
    const response = await request.get(backendHealthURL);
    return response.ok();
  } catch {
    return false;
  }
}

/** Returns visible chat error banner text, if any. */
export async function getChatUiError(page: Page): Promise<string | null> {
  const alert = page.getByRole("alert");
  if (!(await alert.isVisible())) return null;
  return (await alert.textContent())?.trim() ?? null;
}

/** Fails the test with the UI error message when the red alert banner is shown. */
export async function assertNoChatUiError(page: Page): Promise<void> {
  const error = await getChatUiError(page);
  if (error) {
    throw new Error(`Chat UI error: ${error}`);
  }
}

/** Waits until restore finishes: composer enabled (session ready) or error shown. */
export async function waitForChatSession(page: Page): Promise<"ready" | "error"> {
  const composer = page.getByPlaceholder("Ask a question…");
  await expect(composer).toBeVisible({ timeout: 15_000 });

  await page
    .getByText("Restoring conversation…")
    .waitFor({ state: "hidden", timeout: 20_000 })
    .catch(() => undefined);

  for (let i = 0; i < 40; i++) {
    const uiError = await getChatUiError(page);
    if (uiError) return "error";
    if (await composer.isEnabled()) return "ready";
    await page.waitForTimeout(500);
  }
  return (await composer.isEnabled()) ? "ready" : "error";
}

/** Waits up to 30s for a real assistant reply; surfaces UI errors immediately. */
export async function waitForAssistantAnswer(
  page: Page,
  timeoutMs = ASSISTANT_ANSWER_TIMEOUT_MS,
): Promise<string> {
  const assistantReply = page.locator(".chat-message-assistant p").last();

  await expect
    .poll(
      async () => {
        const uiError = await getChatUiError(page);
        if (uiError) {
          throw new Error(`Chat UI error: ${uiError}`);
        }

        const text = (await assistantReply.textContent())?.trim() ?? "";
        return text.length > 8 && text !== "…";
      },
      {
        timeout: timeoutMs,
        message: `No assistant answer within ${timeoutMs / 1000}s`,
      },
    )
    .toBe(true);

  await assertNoChatUiError(page);
  return (await assistantReply.textContent())?.trim() ?? "";
}
