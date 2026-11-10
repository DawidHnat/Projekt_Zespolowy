import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";
import type { Vehicle, VehicleList, FleetMap } from "../src/features/fleet/model/types";

const id = (n: number) => `00000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const name = (n: number) => `Pojazd E2E ${String(n).padStart(2, "0")}`;
const card = (page: Page, n: number) => page.getByRole("article", { name: `Kafelek ${name(n)}`, exact: true });
const sizePicker = (page: Page) => page.getByRole("combobox", { name: "Rozmiar kafelków", exact: true });
const pageSize = (page: Page) => page.getByRole("combobox", { name: "Elementów na stronę: pojazdy", exact: true });
const next = (page: Page) => page.getByRole("button", { name: "Następna strona: pojazdy", exact: true });
const previous = (page: Page) => page.getByRole("button", { name: "Poprzednia strona: pojazdy", exact: true });
const range = (page: Page) => page.getByRole("navigation", { name: "Strony: pojazdy", exact: true }).locator(".list-range");
const search = (page: Page) => page.getByRole("searchbox", { name: "Szukaj pojazdu", exact: true });

async function login(page: Page, role = "editor") {
  await page.goto("/#vehicles");
  await page.getByLabel("Login", { exact: true }).fill(`e2e-${role}`);
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1, name: /^Pojazdy\.?$/ })).toBeVisible();
}

async function logout(page: Page) {
  const menu = page.getByRole("button", { name: "Otwórz menu", exact: true });
  if (await menu.isVisible()) await menu.click();
  await page.getByRole("button", { name: "Wyloguj się", exact: true }).click();
  await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
}

async function fleet(page: Page, legacy = false) {
  await login(page);
  const list: VehicleList = await (await page.request.get("/api/v1/fleet/vehicles")).json();
  const map: FleetMap = await (await page.request.get("/api/v1/fleet/map")).json();
  const user = (await (await page.request.get("/api/v1/auth/me")).json()).user;
  const vehicles: Vehicle[] = [];
  const add = () => {
    const n = vehicles.length + 1;
    vehicles.push({ ...list.items[0], id: id(n), name: name(n), license_plate: `SYN ${n}` });
  };
  for (let n = 0; n < 26; n++) add();
  const filtered = (url: string) => {
    const params = new URL(url).searchParams;
    const q = (params.get("q") ?? "").toLocaleLowerCase("pl");
    const status = params.get("status");
    return vehicles.filter(v => (!status || v.status === status) && `${v.name} ${v.license_plate}`.toLocaleLowerCase("pl").includes(q));
  };
  await page.route(/\/api\/v1\/fleet\/vehicles\?/, route => {
    const params = new URL(route.request().url()).searchParams;
    const items = filtered(route.request().url());
    const page = Number(params.get("page") ?? 1);
    const page_size = Number(params.get("page_size") ?? 25);
    return route.fulfill({ json: { ...list, page, page_size, total: items.length, items: items.slice((page - 1) * page_size, page * page_size) } });
  });
  const mapRequests: URL[] = [];
  await page.route(/\/api\/v1\/fleet\/map(?:\?|$)/, route => {
    const url = route.request().url();
    mapRequests.push(new URL(url));
    const items = filtered(url);
    return route.fulfill({ json: { ...map, total: items.length, located: items.length,
      features: items.map(v => ({ ...map.features[0], properties: { ...map.features[0].properties, id: v.id, name: v.name } })) } });
  });
  const key = `fleet-flow.vehicles.v2.${user.id}`;
  if (legacy) await page.evaluate(({ userId, first, second }) => {
    localStorage.removeItem(`fleet-flow.vehicles.v2.${userId}`);
    localStorage.setItem(`fleet-flow.vehicles.v1.${userId}`, JSON.stringify({
      [first]: { width: 400, height: 500 }, [second]: { width: 320, height: 600 },
    }));
  }, { userId: user.id, first: id(1), second: id(11) });
  await page.reload();
  await expect(card(page, 1)).toBeVisible();
  return { key, add, mapRequests };
}

test.beforeEach(async ({ page }) => {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" }, stdio: "pipe",
  });
  await page.route("**/*", route => new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
});

test("SCRUM-46: selection spans pages and filters, one-axis edits preserve heights and migration keeps photos", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const fixture = await fleet(page, true);
  await expect(card(page, 1)).toHaveCSS("height", "500px");
  await card(page, 1).getByRole("button", { name: `Zdjęcie: ${name(1)}`, exact: true }).click();
  const png = await page.evaluate(() => {
    const canvas = document.createElement("canvas"); canvas.width = 8; canvas.height = 8;
    canvas.getContext("2d")!.fillRect(0, 0, 8, 8);
    return canvas.toDataURL("image/png").split(",")[1];
  });
  await page.getByRole("dialog").getByLabel("Zdjęcie pojazdu", { exact: true }).setInputFiles({ name: "synthetic-migration.png", mimeType: "image/png", buffer: Buffer.from(png, "base64") });
  await expect(page.getByRole("dialog").getByRole("button", { name: "Usuń zdjęcie", exact: true })).toBeEnabled();
  await page.getByRole("dialog").getByRole("button", { name: "Gotowe", exact: true }).click();
  await pageSize(page).selectOption("10");
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  await card(page, 1).getByRole("checkbox").press("Space");
  await next(page).click();
  await expect(card(page, 11)).toBeVisible();
  await card(page, 11).getByRole("heading", { name: name(11), exact: true }).click();
  await expect(page.getByRole("button", { name: "Zaznaczone 2", exact: true })).toHaveAttribute("aria-pressed", "true");
  await sizePicker(page).selectOption("custom");
  const dialog = page.getByRole("dialog");
  const width = dialog.getByRole("slider", { name: "Szerokość kafelka", exact: true });
  await width.press("Home");
  for (let n = 0; n < 12; n++) await width.press("ArrowRight");
  await page.screenshot({ path: test.info().outputPath("bulk-mixed-sizes.png") });
  await dialog.getByRole("button", { name: "Gotowe", exact: true }).click();
  await expect(card(page, 11)).toHaveCSS("width", "400px");
  await expect(card(page, 11)).toHaveCSS("height", "600px");
  await previous(page).click();
  await expect(card(page, 1)).toHaveCSS("height", "500px");
  await search(page).fill(name(26));
  await expect(card(page, 26)).toBeVisible();
  await expect(page.getByRole("button", { name: "Zaznaczone 2", exact: true })).toBeVisible();
  await sizePicker(page).selectOption("Duże");
  await expect(card(page, 26)).toHaveCSS("width", "320px");
  await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
  const saved = await page.evaluate(key => JSON.parse(localStorage.getItem(key)!), fixture.key);
  expect(saved.version).toBe(2);
  expect(saved.sizes[id(1)]).toEqual({ width: 480, height: 500 });
  expect(saved.sizes[id(11)]).toEqual({ width: 480, height: 500 });
  expect(saved.defaultSize).toEqual({ width: 320, height: 440 });
  await page.reload();
  await expect(card(page, 1)).toHaveCSS("width", "480px");
  await expect(card(page, 1).getByRole("img", { name: `Zdjęcie: ${name(1)}`, exact: true })).toBeVisible();
});

test("SCRUM-46: all scope includes filtered, unloaded and future vehicles; cancel restores sizes", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const fixture = await fleet(page);
  await pageSize(page).selectOption("10");
  await search(page).fill(name(1));
  await expect(card(page, 1)).toBeVisible();
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  await page.getByRole("button", { name: "Wszystkie pojazdy", exact: true }).click();
  await sizePicker(page).selectOption("Duże");
  await search(page).fill("");
  await next(page).click();
  await expect(card(page, 11)).toHaveCSS("width", "480px");
  await page.getByRole("button", { name: "Anuluj", exact: true }).click();
  await expect(card(page, 11)).toHaveCSS("width", "320px");
  await search(page).fill(name(26));
  await expect(card(page, 26)).toBeVisible();
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  await page.getByRole("button", { name: "Wszystkie pojazdy", exact: true }).click();
  await sizePicker(page).selectOption("Małe");
  await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
  fixture.add();
  await page.reload();
  await pageSize(page).selectOption("100");
  await expect(page.getByRole("article")).toHaveCount(27);
  await expect(card(page, 27)).toHaveCSS("width", "280px");
  await expect(card(page, 27)).toHaveCSS("height", "420px");
  const saved = await page.evaluate(key => JSON.parse(localStorage.getItem(key)!), fixture.key);
  expect(saved.defaultSize).toEqual({ width: 280, height: 420 });
  expect(saved.sizes).toEqual({});
});

test("SCRUM-46: page size is shared, resets page one, preserves full map data and is account-local", async ({ page }) => {
  const fixture = await fleet(page);
  await pageSize(page).selectOption("10");
  await expect(range(page)).toHaveText("1–10 z 26");
  await next(page).click();
  await expect(range(page)).toHaveText("11–20 z 26");
  for (const size of [25, 50, 100]) {
    await pageSize(page).selectOption(String(size));
    await expect(previous(page)).toBeDisabled();
    await expect(range(page)).toHaveText(`1–${Math.min(size, 26)} z 26`);
  }
  await pageSize(page).selectOption("10");
  await page.goto("/#map");
  await expect(page.locator(".vehicle-card")).toHaveCount(10);
  await expect.poll(() => fixture.mapRequests.length).toBeGreaterThan(0);
  await next(page).click();
  await expect(range(page)).toHaveText("11–20 z 26");
  await pageSize(page).selectOption("50");
  await expect(page.locator(".vehicle-card")).toHaveCount(26);
  await page.goto("/#dashboard");
  await expect(pageSize(page)).toHaveValue("50");
  await expect(page.locator("table.vehicle-table tbody tr")).toHaveCount(26);
  await pageSize(page).selectOption("10");
  await expect(page.locator("table.vehicle-table tbody tr")).toHaveCount(10);
  await page.goto("/#vehicles");
  await search(page).fill("no-such-synthetic-vehicle");
  await expect(range(page)).toHaveText("0–0 z 0");
  await expect(next(page)).toBeDisabled();
  await expect(previous(page)).toBeDisabled();
  await search(page).fill("");
  await pageSize(page).selectOption("100");
  await logout(page);
  await login(page, "viewer");
  await expect(pageSize(page)).toHaveValue("25");
  await logout(page);
  await login(page);
  await expect(pageSize(page)).toHaveValue("100");
  expect(fixture.mapRequests.length).toBeGreaterThan(0);
  expect(fixture.mapRequests.every(url => !url.searchParams.has("page") && !url.searchParams.has("page_size"))).toBeTruthy();
  await expect(range(page)).toHaveText("1–26 z 26");
  await range(page).scrollIntoViewIfNeeded();
  await page.screenshot({ path: test.info().outputPath("bulk-pagination.png") });
});
