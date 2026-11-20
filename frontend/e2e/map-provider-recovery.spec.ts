import { execFileSync } from "node:child_process";
import { expect, test } from "@playwright/test";

test.skip(process.env.E2E_SYNTHETIC_MAP !== "true", "Uses a build with a synthetic public map token");

for (const trigger of ["retry", "online"] as const) {
  test(`recovers a map style after 503 on ${trigger} without losing selection`, async ({ context, page }) => {
    execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
      cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
      stdio: "pipe",
    });
    let failStyle = true;
    let styleRequests = 0;
    await context.route("**/*", async route => {
      const url = new URL(route.request().url());
      if (url.hostname === "127.0.0.1") return route.continue();
      if (url.hostname !== "api.mapbox.com" || !url.pathname.startsWith("/styles/v1/")) return route.abort();
      styleRequests++;
      return route.fulfill({
        headers: { "Access-Control-Allow-Origin": "*" },
        status: failStyle ? 503 : 200,
        json: failStyle ? { message: "Synthetic outage" } : {
          version: 8,
          sources: {},
          layers: [{ id: "background", type: "background", paint: { "background-color": "#ffffff" } }],
        },
      });
    });

    await page.goto("/#map");
    await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
    await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
    await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
    const retry = page.getByRole("button", { name: "Ponów mapę", exact: true });
    await expect(retry).toBeVisible();
    expect(styleRequests).toBeGreaterThan(0);
    const vehicle = page.locator(".vehicle-card").filter({ hasText: "Pojazd E2E" });
    await vehicle.click();
    await expect(vehicle).toHaveAttribute("aria-pressed", "true");

    failStyle = false;
    if (trigger === "retry") await retry.click();
    else await page.evaluate(() => window.dispatchEvent(new Event("online")));
    await expect(page.locator(".map-fallback")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Pokaż całą flotę na mapie" })).toBeEnabled();
    await expect(page.locator(".fleet-map-marker")).toHaveAttribute("aria-pressed", "true");
    await expect(vehicle).toHaveAttribute("aria-pressed", "true");
  });
}
