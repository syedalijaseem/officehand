import { randomBytes } from 'node:crypto';
import { defineConfig, devices } from '@playwright/test';

const PORT = 8123;
const baseURL = process.env['E2E_BASE_URL'] ?? `http://localhost:${PORT}`;

// Throwaway secrets for the test server only; never reused anywhere.
const testSecret = (): string => randomBytes(36).toString('base64url');

export default defineConfig({
  testDir: './e2e',
  outputDir: './e2e/.results',
  fullyParallel: true,
  forbidOnly: !!process.env['CI'],
  retries: process.env['CI'] ? 1 : 0,
  reporter: process.env['CI'] ? 'github' : 'list',
  use: {
    baseURL,
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } },
    },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
  webServer: process.env['E2E_BASE_URL']
    ? undefined
    : {
        command: `uv run --project ../backend uvicorn app.main:create_app --factory --app-dir ../backend --port ${PORT}`,
        url: `${baseURL}/healthz`,
        reuseExistingServer: false,
        timeout: 60_000,
        env: {
          ENV: 'test',
          DEMO_MODE: 'true',
          LLM_PROVIDER: 'fake',
          DATA_DIR: './e2e/.data',
          FRONTEND_DIST: './dist/frontend/browser',
          SESSION_SECRET: testSecret(),
          KEK_KEYS: testSecret(),
          LOG_HASH_PEPPER: testSecret(),
        },
      },
});
