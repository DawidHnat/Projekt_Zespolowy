import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";

// SCRUM-27: the active mileage view (period, partial data, read error). Synthetic data only.

function fixture(command: string) {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", command], {
    cwd: "../backend",
    env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
    stdio: "pipe",
  });
}

function warsawToday() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Warsaw", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(new Date());
  const get = (type: string) => parts.find(part => part.type === type)!.value;
  return { year: get("year"), month: get("month"), day: get("day") };
}

const trip = (id: string, distance: number | null, purpose: string | null) => ({
  id,
  vehicle_id: "11111111-1111-4111-8111-111111111111",
  start_at: "2026-11-03T08:00:00Z",
  end_at: "2026-11-03T09:00:00Z",
  distance_km: distance,
  duration_seconds: 3600,
  annotation: { purpose, description: null, version: 2, updated_at: null, updated_by: null },
  geometry: null,
});

const partial = {
  items: [trip("aaaaaaaa-0000-4000-8000-000000000001", 12.5, "Dostawa"), trip("aaaaaaaa-0000-4000-8000-000000000002", null, null)],
  total: 2,
  page: 1,
  page_size: 10,
  summary: { distance_km: 12.5, documented_km: 12.5, missing_purpose: 1, missing_distance: 1 },
};

async function openMileage(page: Page) {
  await page.goto("/#dashboard");
  await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.locator(".main-shell")).toBeVisible();
  const menu = page.getByRole("button", { name: "Otwórz menu", exact: true });
  if (await menu.isVisible()) await menu.click();
  // Active module: no "Planowane" suffix in the accessible name.
  const mileageLink = page.getByRole("navigation", { name: "Sekcje aplikacji" })
    .getByRole("link", { name: "Ewidencja przebiegu", exact: true });
  await mileageLink.focus();
  await expect(mileageLink).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { level: 1, name: /^Ewidencja przebiegu\.?$/ })).toBeVisible();
  await expect(page.locator(".planned-page")).toHaveCount(0);
}

test.beforeEach(async ({ page }) => {
  fixture("reset-case");
  await page.route("**/*", route =>
    new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
});

test("SCRUM-27: mileage view shows the current month, partial data and recovers from a read error", async ({ page }) => {
  let failNext = true;
  const queries: URLSearchParams[] = [];
  await page.route("**/api/v1/trips/mileage?*", async route => {
    queries.push(new URL(route.request().url()).searchParams);
    if (failNext) {
      failNext = false;
      await route.fulfill({ status: 503, json: { error: { code: "DATABASE_UNAVAILABLE", message: "x" } } });
      return;
    }
    await route.fulfill({ json: partial });
  });

  await openMileage(page);
  const { year, month, day } = warsawToday();
  await expect(page.getByRole("button", { name: `Od dnia: 01.${month}.${year}` })).toBeVisible();
  await expect(page.getByRole("button", { name: `Do dnia: ${day}.${month}.${year}` })).toBeVisible();
  await expect(page.getByText("Wybierz pojazd, aby obliczyć ewidencję.")).toBeVisible();

  await page.getByRole("radio", { name: /Pojazd E2E/ }).check();
  await expect(page.getByRole("alert").filter({ hasText: "Nie można pobrać ewidencji." })).toBeVisible();
  expect(queries[0].get("from_day")).toBe(`${year}-${month}-01`);
  expect(queries[0].get("through")).toBe(`${year}-${month}-${day}`);

  await page.getByRole("button", { name: "Ponów odczyt", exact: true }).click();
  const summary = page.getByRole("region", { name: "Podsumowanie ewidencji" });
  await expect(summary).toBeVisible();
  await expect(summary.locator("dd").nth(0)).toHaveText("2");
  await expect(summary.getByText("Brak danych · Brak celu")).toBeVisible();
  await expect(summary.locator("dt", { hasText: "Brak dystansu" }).locator("+ dd")).toHaveText("1");

  const result = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  expect(result.violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) }))).toEqual([]);
});
