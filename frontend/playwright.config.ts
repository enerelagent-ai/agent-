import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "desktop-chromium",
      use: { ...devices["Desktop Chrome"] },
      grepInvert: /@mobile/,
    },
    { name: "mobile-chromium", use: { ...devices["Pixel 5"] }, grep: /@mobile/ },
  ],
  webServer: [
    {
      command: "cd ../backend && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8100",
      url: "http://127.0.0.1:8100/health",
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command: "npm run dev -- --hostname 127.0.0.1 --port 3100",
      url: "http://127.0.0.1:3100/sale",
      reuseExistingServer: true,
      timeout: 120_000,
      env: {
        BACKEND_API_URL: "http://127.0.0.1:8100",
        MARKETPLACE_V2_ENABLED: "true",
        COMPLEX_INSIGHTS_ENABLED: "false",
      },
    },
  ],
});
