import { chromium } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:4321';

async function saveAuth() {
  const authDir = path.join(__dirname, '..', 'playwright', '.auth');
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  const browser = await chromium.launch({
    channel: 'chrome',
    headless: false,
    args: ['--disable-blink-features=AutomationControlled'],
    ignoreDefaultArgs: ['--enable-automation'],
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto(baseURL);

  // Pause so you can log in manually.
  // After logging in, click "Resume" in the Playwright Inspector.
  await page.pause();

  await context.storageState({ path: path.join(authDir, 'user.json') });
  console.log('Auth state saved to playwright/.auth/user.json');

  await browser.close();
}

saveAuth().catch((err) => {
  console.error(err);
  process.exit(1);
});
