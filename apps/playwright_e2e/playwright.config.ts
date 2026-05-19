import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:4321";
const backendHealthURL =
  process.env.PLAYWRIGHT_BACKEND_HEALTH_URL ?? "http://localhost:8000/health";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  // Start frontend only when requested; default assumes `make dev` (or dev-frontend) is running.
  webServer:
    process.env.PLAYWRIGHT_START_WEB_SERVER === "1"
      ? {
          command: "npm run dev",
          cwd: "../frontend",
          url: `${baseURL}/chat`,
          reuseExistingServer: true,
          timeout: 120_000,
        }
      : undefined,
  metadata: {
    backendHealthURL,
  },
});
