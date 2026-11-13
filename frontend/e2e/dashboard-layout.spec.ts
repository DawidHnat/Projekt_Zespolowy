import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";

const storageKey = "fleet-flow.dashboard.v2";
let browserErrors: string[];

async function preferences(page: Page) {
  return page.evaluate(key => JSON.parse(localStorage.getItem(key)!), storageKey);
}

async function login(page: Page) {
  await page.goto("/#dashboard");
  await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.locator("[data-widget]")).toHaveCount(6);
  await page.evaluate(() => document.fonts.ready);
}

async function layoutProblems(page: Page) {
  return page.evaluate(() => {
    const problems: string[] = [];
    const root = document.querySelector<HTMLElement>(".dashboard-canvas");
    if (!root) return ["canvas has not mounted yet"];
    const canvas = root.getBoundingClientRect();
    const tiles = [...root.querySelectorAll<HTMLElement>("[data-widget]")];
    if (tiles.length === 0) return ["widgets have not mounted yet"];
    if (document.documentElement.scrollWidth > innerWidth) problems.push("page overflows horizontally");
    if (root.dataset.profile !== (canvas.width < 720 ? "compact" : "desktop")) problems.push("wrong screen profile");
    for (const tile of tiles) {
      const box = tile.getBoundingClientRect();
      const id = tile.dataset.widget;
      if (box.left < canvas.left - 1 || box.right > canvas.right + 1) problems.push(`${id} outside canvas`);
      const body = tile.querySelector<HTMLElement>(".widget-content")!;
      if (id !== "vehicles" && body.scrollHeight > body.clientHeight + 2) problems.push(`${id} clips static content`);
      const records = tile.querySelector<HTMLElement>(".table-scroll, .vehicle-cards");
      const row = tile.querySelector("tbody tr, .vehicle-card");
      if (records && row && row.getBoundingClientRect().bottom > records.getBoundingClientRect().bottom + 1)
        problems.push(`${id} clips its first record`);
      for (const other of tiles) {
        if (other === tile) continue;
        const next = other.getBoundingClientRect();
        if (Math.min(box.right, next.right) - Math.max(box.left, next.left) > 1 &&
          Math.min(box.bottom, next.bottom) - Math.max(box.top, next.top) > 1)
          problems.push(`${id} overlaps ${other.dataset.widget}`);
      }
    }
    return problems;
  });
}

test.beforeEach(async ({ page }) => {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" }, stdio: "pipe",
  });
  await page.route("**/*", route => new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
  browserErrors = [];
  page.on("pageerror", error => browserErrors.push(error.message));
});

test.afterEach(() => expect(browserErrors).toEqual([]));

test("SCRUM-38: default pairs share a row through window resize, themes and edit mode", async ({ page }) => {
  test.setTimeout(90_000);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await login(page);
  const savedLayouts = (await preferences(page)).layouts;
  for (const [theme, material] of [["Jasny", "Szkło"], ["Ciemny", "Klasyczny"]]) {
    await page.goto("/#settings");
    await page.getByRole("button", { name: theme, exact: true }).click();
    await page.getByRole("button", { name: material, exact: true }).click();
    await page.goto("/#dashboard");
    for (const editing of [false, true]) {
      if (editing) await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
      for (const width of [1440, 1200, 1024, 980, 972, 971, 970, 960, 900, 800, 761, 760, 756, 755, 720, 600, 390, 320, 760, 1024, 1440]) {
        await page.setViewportSize({ width, height: 1000 });
        await expect.poll(() => layoutProblems(page), { message: `${theme}, edit=${editing}, ${width}px` }).toEqual([]);
        if (await page.locator(".dashboard-canvas").getAttribute("data-profile") === "desktop") {
          for (const [left, right] of [["map", "activity"], ["vehicles", "utilization"]]) {
            await expect.poll(async () => Math.abs(
              (await page.locator(`[data-widget="${left}"]`).boundingBox())!.y -
              (await page.locator(`[data-widget="${right}"]`).boundingBox())!.y,
            )).toBeLessThan(2);
          }
        }
        if ([1440, 980, 320].includes(width)) await page.screenshot({
          path: test.info().outputPath(`${theme}-${editing ? "edit" : "view"}-${width}.png`), fullPage: true,
        });
      }
      if (editing) await page.getByRole("button", { name: "Anuluj", exact: true }).click();
    }
  }
  expect((await preferences(page)).layouts).toEqual(savedLayouts);
});

test("SCRUM-38: the dedicated map adapts without overwriting either saved layout", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await login(page);
  const savedLayouts = (await preferences(page)).layouts;
  await page.goto("/#map");
  await expect(page.locator("[data-widget]")).toHaveCount(2);
  await expect(page.getByText("Mapa czeka na konfigurację", { exact: true })).toBeVisible();
  for (const width of [1440, 980, 971, 960, 760, 755, 390, 320, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await expect.poll(() => layoutProblems(page), { message: `Map at ${width}px` }).toEqual([]);
    if ([980, 320].includes(width)) await page.screenshot({
      path: test.info().outputPath(`map-${width}.png`), fullPage: true,
    });
  }
  expect((await preferences(page)).layouts).toEqual(savedLayouts);
});

for (const gesture of ["drag", "resize"]) {
  test(`SCRUM-38: editing continues after window resize during a held ${gesture}`, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await login(page);
    await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
    const tile = page.locator('[data-widget="map"]');
    const handle = gesture === "drag"
      ? page.getByRole("button", { name: "Przesuń: Mapa floty", exact: true })
      : tile.locator(".react-resizable-handle");
    await handle.scrollIntoViewIfNeeded();
    const box = (await handle.boundingBox())!;
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + 80, box.y + 80, { steps: 8 });
    await expect(page.locator(".dashboard-canvas.is-interacting")).toHaveCount(1);
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.mouse.up();
    await expect(page.locator(".dashboard-canvas")).toHaveAttribute("data-profile", "compact");
    await expect(page.locator(".dashboard-canvas.is-interacting")).toHaveCount(0);
    await expect.poll(() => layoutProblems(page)).toEqual([]);
    const before = (await tile.boundingBox())!.height;
    await page.getByRole("button", { name: "Przesuń: Mapa floty", exact: true }).press("Shift+ArrowDown");
    await expect.poll(async () => (await tile.boundingBox())!.height).toBeGreaterThan(before + 10);
  });
}

test("SCRUM-38: widening an open mobile menu removes its blocking backdrop", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await page.getByRole("button", { name: "Otwórz menu", exact: true }).click();
  await expect(page.locator(".sidebar-backdrop")).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect(page.locator(".sidebar-backdrop")).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("button", { name: "Otwórz menu", exact: true })).toHaveAttribute("aria-expanded", "false");
  await page.getByRole("button", { name: "Otwórz menu", exact: true }).click();
  await page.keyboard.press("Escape");
  await expect(page.locator(".sidebar-backdrop")).toHaveCount(0);
});

test("SCRUM-38: desktop and compact edits persist independently and cancel restores hidden widgets", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await login(page);
  const original = await preferences(page);
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  await page.getByRole("button", { name: "Przesuń: Mapa floty", exact: true }).press("Shift+ArrowDown");
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".dashboard-canvas")).toHaveAttribute("data-profile", "compact");
  await page.getByRole("button", { name: "Przesuń: Mapa floty", exact: true }).press("Shift+ArrowDown");
  await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
  const saved = await preferences(page);
  for (const profile of ["desktop", "compact"])
    expect(saved.layouts.dashboard[profile].find((item: { i: string }) => item.i === "map").h)
      .toBe(original.layouts.dashboard[profile].find((item: { i: string }) => item.i === "map").h + 0.5);
  expect(saved.layouts.map).toEqual(original.layouts.map);
  await page.reload();
  await expect.poll(() => layoutProblems(page)).toEqual([]);
  expect(await preferences(page)).toEqual(saved);
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  await page.getByRole("button", { name: "Edytuj: Mapa floty", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Ukryj na Pulpicie", exact: true }).click();
  await expect(page.locator('[data-widget="map"]')).toHaveCount(0);
  await page.getByRole("button", { name: "Anuluj", exact: true }).click();
  await expect(page.locator("[data-widget]")).toHaveCount(6);
  expect(await preferences(page)).toEqual(saved);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect.poll(() => layoutProblems(page)).toEqual([]);
});

test("SCRUM-38: appearance persists, system theme responds and module search recovers", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await login(page);
  await page.goto("/#settings");
  await page.getByRole("button", { name: "System", exact: true }).click();
  await page.getByRole("button", { name: "Klasyczny", exact: true }).click();
  await page.getByRole("button", { name: "Akcent: Turkus", exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.emulateMedia({ colorScheme: "light" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.getByRole("button", { name: "System", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("html")).toHaveAttribute("data-material", "solid");
  expect((await preferences(page)).accent).toBe("#008b83");
  await page.goto("/#dashboard");
  const search = page.getByRole("searchbox", { name: "Szukaj modułu", exact: true });
  await search.fill("nieistniejący-moduł");
  await expect(page.getByRole("heading", { name: "Nie znaleziono modułu", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Wyczyść wyszukiwanie", exact: true }).click();
  await expect(page.locator("[data-widget]")).toHaveCount(6);
  await search.fill("mapa");
  await expect(page.locator("[data-widget]")).toHaveCount(1);
  await expect(page.locator('[data-widget="map"]')).toBeVisible();
});
