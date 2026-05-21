import { defineConfig, devices } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:4321";
const backendHealthURL =
  process.env.PLAYWRIGHT_BACKEND_HEALTH_URL ?? "http://localhost:8000/health";

const authFile = path.join(__dirname, "playwright", ".auth", "user.json");

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
      name: "setup",
      testDir: "./scripts",
      testMatch: /save-auth\.ts/,
    },
    {
      name: "setup-chrome",
      testDir: "./scripts",
      testMatch: /save-auth\.ts/,
      use: { channel: "chrome" },
    },
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        storageState: authFile,
      },
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
