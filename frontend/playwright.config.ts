import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: Boolean(process.env.CI),
  reporter: [["list"], ["junit", { outputFile: "test-results/results.xml" }]],
  use: {
    baseURL: "http://127.0.0.1:54173",
    timezoneId: "Europe/Warsaw",
    locale: "pl-PL",
    screenshot: "only-on-failure",
    trace: "off",
    video: "off",
  },
  projects: [
    { name: "desktop", use: { browserName: "chromium", viewport: { width: 1440, height: 1000 } } },
    { name: "mobile", use: { browserName: "chromium", viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
  webServer: [
    {
      command: `${process.env.E2E_PYTHON || "python3"} tests/e2e_server.py`,
      cwd: "../backend",
      url: "http://127.0.0.1:58000/api/health/ready",
      reuseExistingServer: false,
      env: { PYTHONPATH: ".", FLEET_FLOW_E2E: "true", SYNC_ENABLED: "false" },
    },
    {
      command: "npm run dev -- --config vite.e2e.config.ts",
      url: "http://127.0.0.1:54173",
      reuseExistingServer: false,
      env: { VITE_MAPBOX_TOKEN: "", SYNC_ENABLED: "false" },
    },
  ],
});
