import { defineConfig, devices } from '@playwright/test';
// Verifies a served site (DOCS_URL, e.g. `npm run preview` or the deployed docs) in all three engines.
export default defineConfig({
  testDir: './test',
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: { trace: 'retain-on-failure' },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], headless: !process.env.CI } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
});
