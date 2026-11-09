import { defineConfig, devices } from "@playwright/test"
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60000,
  use: {
    baseURL: "http://127.0.0.1:5174",
    channel: "msedge",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Edge"] } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
  webServer: [
    {
      command:
        "powershell -NoProfile -ExecutionPolicy Bypass -File ../scripts/start-e2e-backend.ps1",
      url: "http://127.0.0.1:8001/api/health/ready",
      reuseExistingServer: false,
      timeout: 120000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5174 --strictPort",
      url: "http://127.0.0.1:5174",
      env: { VITE_API_PROXY: "http://127.0.0.1:8001" },
      reuseExistingServer: false,
    },
  ],
  reporter: "list",
})
