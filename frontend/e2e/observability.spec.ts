import { execFileSync } from "node:child_process";
import { expect, test } from "@playwright/test";

function resetDatabase() {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
    cwd: "../backend",
    env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true", SYNC_ENABLED: "false" },
  });
}

test.beforeEach(() => {
  resetDatabase();
});

test("SCRUM-114: UI surfaces correlation ID on 5xx errors and enforces admin RBAC on metrics", async ({ page }) => {
  const incidentCid = "incident-e2e-2026-11-25";
  await page.route("**/api/v1/fleet/vehicles**", (route) =>
    route.fulfill({
      status: 503,
      headers: { "Content-Type": "application/json", "X-Correlation-ID": incidentCid },
      body: JSON.stringify({
        error: {
          code: "DATABASE_UNAVAILABLE",
          message: "Baza jest niedostępna",
          correlation_id: incidentCid,
        },
      }),
    }),
  );

  await page.goto("/#vehicles");
  await page.getByLabel("Login").fill("e2e-editor");
  await page.getByLabel("Hasło").fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się" }).click();

  await expect(page.getByRole("alert")).toContainText(`ID zgłoszenia: ${incidentCid}`);

  // Editor cannot read operator metrics, while X-Correlation-ID header is returned.
  const denied = await page.request.get("/api/v1/observability/metrics", {
    headers: { "X-Correlation-ID": "check-rbac-editor-01" },
  });
  expect(denied.status()).toBe(403);
  expect(denied.headers()["x-correlation-id"]).toBe("check-rbac-editor-01");

  await page.unroute("**/api/v1/fleet/vehicles**");
  const openMenu = page.getByRole("button", { name: "Otwórz menu" });
  if (await openMenu.isVisible()) await openMenu.click();
  await page.getByRole("button", { name: "Wyloguj się" }).click();

  await page.getByLabel("Login").fill("e2e-admin");
  await page.getByLabel("Hasło").fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się" }).click();
  await expect(page.getByRole("heading", { name: "Pojazd E2E" })).toBeVisible();

  const metrics = await page.request.get("/api/v1/observability/metrics");
  expect(metrics.status()).toBe(200);
  const body = await metrics.json();
  expect(body.api_up).toBe(1);
  expect(body.backup.status).toBe("not_configured");
  expect(body.backup.deferred_to).toBe("SCRUM-84");
});
