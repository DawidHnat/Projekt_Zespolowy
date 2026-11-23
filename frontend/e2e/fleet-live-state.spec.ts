import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";

async function wake(page: Page) {
  await page.evaluate(() => {
    Object.defineProperty(document, "visibilityState", { configurable: true, value: "hidden" });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await page.evaluate(() => {
    Object.defineProperty(document, "visibilityState", { configurable: true, value: "visible" });
    document.dispatchEvent(new Event("visibilitychange"));
  });
}

async function login(page: Page, section = "map") {
  await page.goto(`/#${section}`);
  await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.getByRole("searchbox", { name: "Szukaj pojazdu" })).toBeEnabled();
}

function fleetFixture(caseName: "reset-case" | "drivers-case") {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", caseName], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
    stdio: "pipe",
  });
}

test.beforeEach(async ({ context }) => {
  fleetFixture("reset-case");
  await context.route("**/*", route => new URL(route.request().url()).hostname === "127.0.0.1"
    ? route.continue() : route.abort());
});

test("source refresh shares cooldown between tabs and reloads, and preserves filters and selection", async ({ page, context }) => {
  let allowedAt = 0;
  let posts = 0;
  const state = () => ({
    enabled: true, running: false, server_time: new Date().toISOString(),
    next_allowed_at: allowedAt ? new Date(allowedAt).toISOString() : null,
    retry_after_seconds: Math.max(0, Math.ceil((allowedAt - Date.now()) / 1000)),
  });
  await context.route("**/api/v1/fleet/refresh", async route => {
    if (route.request().method() === "POST") {
      posts++;
      const result = Date.now() < allowedAt ? "cooldown" : "updated";
      if (result === "updated") allowedAt = Date.now() + 60_000;
      await new Promise(resolve => setTimeout(resolve, 100));
      return route.fulfill({ status: 200, json: { ...state(), result } });
    }
    return route.fulfill({ status: 200, json: state() });
  });
  await login(page);
  await page.getByRole("searchbox", { name: "Szukaj pojazdu" }).fill("TEST E2E");
  const selected = page.locator(".vehicle-card").filter({ hasText: "Pojazd E2E" });
  await selected.click();
  const refresh = page.getByRole("button", { name: /^Odśwież dane floty/ });
  await expect(refresh).toHaveAttribute("aria-disabled", "false");
  const request = page.waitForResponse(r => r.request().method() === "POST" && r.url().endsWith("/fleet/refresh"));
  await refresh.click();
  await expect(refresh).toContainText("Odświeżanie");
  await request;
  await expect(refresh).toContainText(/Za \d+ s/);
  await expect(selected).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("searchbox", { name: "Szukaj pojazdu" })).toHaveValue("TEST E2E");
  // aria-disabled keeps this control focusable so it can explain the wait.
  await refresh.click({ force: true });
  expect(posts).toBe(1);

  const other = await context.newPage();
  await other.goto("/#map");
  const otherRefresh = other.getByRole("button", { name: /^Odśwież dane floty/ });
  await expect(otherRefresh).toContainText(/Za \d+ s/);
  await otherRefresh.click({ force: true });
  await other.reload();
  await expect(otherRefresh).toContainText(/Za \d+ s/);
  expect(posts).toBe(1);
  allowedAt = 0;
  await wake(page);
  await expect(refresh).toHaveAttribute("aria-disabled", "false");
  await refresh.click();
  await expect(refresh).toContainText(/Za \d+ s/);
  expect(posts).toBe(2);
});

test("utilization shows whole-fleet counts, preserves cache on error and distinguishes unknown from empty", async ({ page, context }) => {
  const source = { status: "ok", last_success_at: new Date().toISOString(), error_code: null };
  let summary = { total: 5, moving: 2, stopped: 1, offline: 1, unknown: 1, source };
  let failed = false;
  await context.route("**/api/v1/fleet/summary", route => route.fulfill({
    status: failed ? 503 : 200,
    json: failed ? { error: { code: "TEST_FAILURE", message: "Syntetyczna awaria" } } : summary,
  }));
  await login(page, "dashboard");
  const widget = page.locator(".utilization-widget");
  await expect(widget.locator(".fleet-gauge")).toContainText("40%");
  await expect(widget.locator(".gauge-legend li").nth(0)).toHaveText("W ruchu 2");
  await expect(widget.locator(".gauge-legend li").nth(1)).toHaveText("Na postoju 1");
  await expect(widget.locator(".gauge-legend li").nth(2)).toHaveText("Pozostałe 2");
  await page.getByRole("searchbox", { name: "Szukaj pojazdu" }).fill("no-such-vehicle");
  await expect(page.locator(".vehicle-table tbody tr")).toHaveCount(0);
  await expect(widget.locator(".fleet-gauge")).toContainText("40%");

  failed = true;
  await wake(page);
  await expect(widget).toContainText("Pokazujemy ostatni poprawny odczyt");
  await expect(widget.locator(".fleet-gauge")).toContainText("40%");
  const fresh = await context.newPage();
  await fresh.goto("/#dashboard");
  await expect(fresh.locator(".utilization-widget")).toContainText("Nie można pobrać stanu floty");
  await expect(fresh.locator(".fleet-gauge")).not.toContainText("0%");
  await fresh.close();

  failed = false;
  summary = { ...summary, moving: 0, stopped: 0, offline: 3, unknown: 2 };
  await wake(page);
  await expect(widget.locator(".gauge-legend li").nth(2)).toHaveText("Pozostałe 5");
  await expect(widget.locator(".fleet-gauge")).toContainText("—");
  summary = { ...summary, total: 0, moving: 0, stopped: 0, offline: 0, unknown: 0 };
  await wake(page);
  await expect(widget).toContainText("We flocie nie ma jeszcze pojazdów");
  await expect(widget.locator(".fleet-gauge")).not.toContainText("%");
});

test.describe("fleet pagination", () => {
  test.afterEach(() => fleetFixture("reset-case"));

  test("pagination changes only the list and a shared filter refreshes the map", async ({ page }) => {
    fleetFixture("drivers-case");
    const mapQueries: string[] = [];
    page.on("request", request => {
      const url = new URL(request.url());
      if (url.pathname === "/api/v1/fleet/map") mapQueries.push(url.searchParams.get("q") ?? "");
    });
    await login(page, "vehicles");
    await expect.poll(() => mapQueries.length).toBeGreaterThan(0);
    const mapCount = mapQueries.length;
    const paginated = page.waitForResponse(response =>
      response.url().includes("/api/v1/fleet/vehicles?") && response.url().includes("page_size=10")
    );
    await page.getByRole("combobox", { name: "Elementów na stronę: pojazdy", exact: true }).selectOption("10");
    await paginated;
    const next = page.waitForResponse(response =>
      response.url().includes("/api/v1/fleet/vehicles?") && new URL(response.url()).searchParams.get("page") === "2"
    );
    await page.getByRole("button", { name: "Następna strona: pojazdy", exact: true }).click();
    await next;
    expect(mapQueries).toHaveLength(mapCount);

    await page.getByRole("searchbox", { name: "Szukaj pojazdu" }).fill("Auto kierowcy");
    await expect.poll(() => mapQueries.at(-1)).toBe("Auto kierowcy");
  });
});
