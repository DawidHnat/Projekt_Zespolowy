import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";

const trip = "22222222-2222-4222-8222-222222222222";

function sourceState(value: "ok" | "degraded" | "unavailable") {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "source-state", value], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
    stdio: "pipe",
  });
}

async function login(page: Page, role = "editor") {
  await page.goto("/#vehicles");
  await page.getByLabel("Login", { exact: true }).fill(`e2e-${role}`);
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.getByRole("heading", { name: /^Pojazdy\.?$/, level: 1 })).toBeVisible();
}

async function annotation(page: Page) {
  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await dialog.getByRole("tab", { name: "Podróże", exact: true }).click();
  await dialog.getByRole("list", { name: "Przejazdy pojazdu", exact: true }).getByRole("button").first().click();
  return dialog.getByRole("form", { name: "Cel i opis przejazdu", exact: true });
}

async function confirmUnsaved(page: Page, action: () => Promise<unknown>, accept: boolean) {
  const prompt = page.waitForEvent("dialog");
  const pending = action();
  const dialog = await prompt;
  expect(dialog.type()).toBe("confirm");
  expect(dialog.message()).toContain("niezapisany cel lub opis");
  if (accept) await dialog.accept();
  else await dialog.dismiss();
  await pending;
}

test.beforeEach(async ({ page }) => {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
    stdio: "pipe",
  });
  // Enforce an offline fixture: any accidentally introduced external call is blocked.
  await page.route("**/*", (route) => {
    const url = new URL(route.request().url());
    return url.hostname === "127.0.0.1" ? route.continue() : route.abort();
  });
});

test("login, filter, map API and fallback, details, durable annotation, logout", async ({ page }) => {
  const unauthorized = await page.request.get("/api/v1/fleet/vehicles");
  expect(unauthorized.status()).toBe(401);
  await login(page);
  await page.getByRole("searchbox", { name: "Szukaj pojazdu" }).fill("TEST E2E");
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  await page.getByRole("searchbox", { name: "Szukaj pojazdu" }).fill("no-such-synthetic-vehicle");
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toHaveCount(0);
  await page.getByRole("searchbox", { name: "Szukaj pojazdu" }).fill("");
  const map = await page.request.get("/api/v1/fleet/map");
  expect(map.ok()).toBeTruthy();
  expect((await map.json()).features[0].geometry.coordinates).toEqual([0, 0]);
  await page.goto("/#map");
  await expect(page.getByRole("heading", { name: /^Mapa\.?$/, level: 1 })).toBeVisible();
  await expect(page.getByText("Mapa czeka na konfigurację").first()).toBeVisible();
  await page.goto("/#vehicles");
  const form = await annotation(page);
  const purpose = `Odbiór E2E ${test.info().project.name}`;
  await form.getByLabel(/Cel przejazdu/).fill(purpose);
  await form.getByLabel(/Opis przejazdu/).fill(`Zapis syntetyczny ${Date.now()}`);
  await form.getByRole("button", { name: "Zapisz cel i opis", exact: true }).click();
  await expect(form.getByRole("status")).toHaveText("Cel i opis zostały zapisane.");
  await page.screenshot({ path: test.info().outputPath("saved-annotation.png") });
  await page.reload();
  const reopened = await annotation(page);
  await expect(reopened.getByLabel(/Cel przejazdu/)).toHaveValue(purpose);
  expect((await (await page.request.get(`/api/v1/trips/${trip}`)).json()).annotation.purpose).toBe(purpose);
  await page.getByRole("button", { name: "Zamknij szczegóły pojazdu" }).click();
  const menu = page.getByRole("button", { name: "Otwórz menu", exact: true });
  if (await menu.isVisible()) await menu.click();
  await page.getByRole("button", { name: "Wyloguj się", exact: true }).click();
  await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
  expect((await page.request.get("/api/v1/fleet/vehicles")).status()).toBe(401);
});

test("viewer cannot edit in UI or bypass the policy through the real API", async ({ page }) => {
  await login(page, "viewer");
  const form = await annotation(page);
  await expect(form.getByText("Masz dostęp tylko do odczytu.")).toBeVisible();
  await expect(form.getByLabel(/Cel przejazdu/)).toHaveAttribute("readonly", "");
  await expect(form.getByRole("button", { name: "Zapisz cel i opis", exact: true })).toHaveCount(0);
  const result = await page.request.patch(`/api/v1/trips/${trip}/annotation`, {
    headers: { Origin: "http://127.0.0.1:54173" },
    data: { version: 1, purpose: "Forbidden fixture change" },
  });
  expect(result.status()).toBe(403);
});

test("degraded cache keeps vehicles and displays a source warning", async ({ page }) => {
  sourceState("degraded");
  await login(page);
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  const result = await page.request.get("/api/v1/fleet/vehicles");
  expect((await result.json()).source.status).toBe("degraded");
  await expect(page.getByText("WEBFLEET jest chwilowo niedostępny. Wyświetlamy ostatnie pomiary.").first()).toBeVisible();
});

test("cold unavailable source shows a recoverable error instead of an empty fleet", async ({ page }) => {
  sourceState("unavailable");
  await login(page);
  expect((await page.request.get("/api/v1/fleet/vehicles")).status()).toBe(503);
  await expect(page.getByText("Oczekiwanie na pierwszy odczyt WEBFLEET.").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toHaveCount(0);
});

test("invalidated session returns to login", async ({ page }) => {
  await login(page);
  expect((await page.request.post("/api/v1/auth/logout", {
    headers: { Origin: "http://127.0.0.1:54173" },
  })).ok()).toBeTruthy();
  await page.reload();
  await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
});

test("concurrent annotation edit returns 409 and preserves the browser draft", async ({ page }) => {
  await login(page);
  const form = await annotation(page);
  await form.getByLabel(/Cel przejazdu/).fill(`Mój szkic ${Date.now()}`);
  const draft = await form.getByLabel(/Cel przejazdu/).inputValue();
  const current = (await (await page.request.get(`/api/v1/trips/${trip}`)).json()).annotation;
  const changed = await page.request.patch(`/api/v1/trips/${trip}/annotation`, {
    headers: { Origin: "http://127.0.0.1:54173" },
    data: { version: current.version, purpose: `Równoległy zapis ${Date.now()}` },
  });
  expect(changed.ok()).toBeTruthy();
  const conflict = page.waitForResponse(response => response.url().endsWith(`/trips/${trip}/annotation`) && response.status() === 409);
  await form.getByRole("button", { name: "Zapisz cel i opis", exact: true }).click();
  await conflict;
  await expect(form.getByLabel(/Cel przejazdu/)).toHaveValue(draft);
  await form.getByRole("button", { name: "Sprawdź bieżącą wersję", exact: true }).click();
  await expect(form.getByRole("heading", { name: "Bieżąca wersja w bazie" })).toBeVisible();
  await form.getByRole("button", { name: "Anuluj zmiany", exact: true }).click();
});

test("login rate limit is enforced and shown in the browser", async ({ page }) => {
  for (let attempt = 0; attempt < 10; attempt++) {
    const response = await page.request.post("/api/v1/auth/login", {
      headers: { Origin: "http://127.0.0.1:54173" },
      data: { username: "e2e-editor", password: "synthetic-wrong-password" },
    });
    expect(response.status()).toBe(401);
  }
  await page.goto("/#vehicles");
  await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.getByRole("alert")).toHaveText("Zbyt wiele prób. Spróbuj ponownie za minutę.");
});

test("rejecting close, tab change and Escape preserves an unsaved annotation", async ({ page }) => {
  await login(page);
  const original = (await (await page.request.get(`/api/v1/trips/${trip}`)).json()).annotation;
  const form = await annotation(page);
  const draft = `Niezapisany szkic ${Date.now()}`;
  await form.getByLabel(/Cel przejazdu/).fill(draft);
  await expect(page.getByText("Przed zmianą dnia lub przejazdu zapisz albo anuluj edycję.")).toBeVisible();
  const close = () => page.getByRole("button", { name: "Zamknij szczegóły pojazdu" }).click();
  await confirmUnsaved(page, close, false);
  await expect(form.getByLabel(/Cel przejazdu/)).toHaveValue(draft);
  await confirmUnsaved(page, () => page.getByRole("tab", { name: "Pojazd", exact: true }).click(), false);
  await expect(page.getByRole("tab", { name: "Podróże", exact: true })).toHaveAttribute("aria-selected", "true");
  await confirmUnsaved(page, () => page.keyboard.press("Escape"), false);
  await expect(form.getByLabel(/Cel przejazdu/)).toHaveValue(draft);
  expect((await (await page.request.get(`/api/v1/trips/${trip}`)).json()).annotation).toEqual(original);
  await confirmUnsaved(page, close, true);
  await expect(page.getByRole("dialog")).not.toBeVisible();
  const reopened = await annotation(page);
  await expect(reopened.getByLabel(/Cel przejazdu/)).toHaveValue(original.purpose ?? "");
});

test("temporary save failure preserves the draft and retry writes to PostgreSQL", async ({ page }) => {
  await login(page);
  const original = (await (await page.request.get(`/api/v1/trips/${trip}`)).json()).annotation;
  const form = await annotation(page);
  const draft = `Ponowienie ${Date.now()}`;
  await form.getByLabel(/Cel przejazdu/).fill(draft);
  await page.route(`**/api/v1/trips/${trip}/annotation`, route => route.fulfill({
    status: 503, contentType: "application/json",
    body: JSON.stringify({ error: { code: "TEMPORARY_FAILURE", message: "synthetic failure" } }),
  }));
  await form.getByRole("button", { name: "Zapisz cel i opis", exact: true }).click();
  await expect(form.getByRole("alert")).toBeVisible();
  await expect(form.getByLabel(/Cel przejazdu/)).toHaveValue(draft);
  expect((await (await page.request.get(`/api/v1/trips/${trip}`)).json()).annotation).toEqual(original);
  await page.unroute(`**/api/v1/trips/${trip}/annotation`);
  await form.getByRole("button", { name: "Zapisz cel i opis", exact: true }).click();
  await expect(form.getByRole("status")).toHaveText("Cel i opis zostały zapisane.");
  expect((await (await page.request.get(`/api/v1/trips/${trip}`)).json()).annotation.purpose).toBe(draft);
});

test("expired session removes the private draft when a save is rejected", async ({ page }) => {
  await login(page);
  const form = await annotation(page);
  await form.getByLabel(/Cel przejazdu/).fill("Prywatny niezapisany szkic E2E");
  expect((await page.request.post("/api/v1/auth/logout", {
    headers: { Origin: "http://127.0.0.1:54173" },
  })).ok()).toBeTruthy();
  await form.getByRole("button", { name: "Zapisz cel i opis", exact: true }).click();
  await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
  await expect(page.getByRole("form", { name: "Cel i opis przejazdu", exact: true })).toHaveCount(0);
  await expect(page.getByLabel(/Cel przejazdu/)).toHaveCount(0);
});

test("polling pauses in a hidden/offline page and keeps an annotation draft on refresh", async ({ page }) => {
  await page.clock.install();
  await page.clock.pauseAt(new Date());
  let lists = 0;
  let details = 0;
  page.on("request", request => {
    const path = new URL(request.url()).pathname;
    if (path === "/api/v1/fleet/vehicles") lists++;
    if (/\/api\/v1\/fleet\/vehicles\/[^/]+$/.test(path)) details++;
  });
  await login(page);
  const form = await annotation(page);
  await form.getByLabel(/Cel przejazdu/).fill("Szkic przy odświeżaniu");
  const beforeHidden = lists;
  await page.evaluate(() => {
    Object.defineProperty(document, "visibilityState", { configurable: true, value: "hidden" });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await page.clock.fastForward(180_000);
  expect(lists).toBe(beforeHidden);
  await page.evaluate(() => {
    Object.defineProperty(document, "visibilityState", { configurable: true, value: "visible" });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect.poll(() => lists).toBe(beforeHidden + 1);
  await expect.poll(() => details).toBe(2);
  await expect(form.getByLabel(/Cel przejazdu/)).toHaveValue("Szkic przy odświeżaniu");
  const beforeOffline = lists;
  await page.evaluate(() => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: false });
    window.dispatchEvent(new Event("offline"));
  });
  await page.clock.fastForward(180_000);
  expect(lists).toBe(beforeOffline);
  await page.evaluate(() => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
    window.dispatchEvent(new Event("online"));
  });
  await expect.poll(() => lists).toBe(beforeOffline + 1);
  await expect(form.getByLabel(/Cel przejazdu/)).toHaveValue("Szkic przy odświeżaniu");
  await page.screenshot({ path: test.info().outputPath("polling-preserves-draft.png") });
});

test("list page size changes do not fetch an unrelated selected detail again", async ({ page }) => {
  await page.clock.install();
  await page.clock.pauseAt(new Date());
  let details = 0;
  page.on("request", request => {
    if (/\/api\/v1\/fleet\/vehicles\/[^/]+$/.test(new URL(request.url()).pathname)) details++;
  });
  await login(page);
  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  await expect(page.getByRole("dialog").getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Zamknij szczegóły pojazdu" }).click();
  expect(details).toBe(1);
  const listUpdate = page.waitForResponse(response => response.url().includes("/api/v1/fleet/vehicles?") && response.url().includes("page_size=10"));
  await page.getByRole("combobox", { name: "Elementów na stronę: pojazdy", exact: true }).selectOption("10");
  await listUpdate;
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  expect(details).toBe(1);
});

test("switching accounts resets selected details, filters and the per-user page size", async ({ page }) => {
  await login(page);
  await page.getByRole("combobox", { name: "Elementów na stronę: pojazdy", exact: true }).selectOption("10");
  await page.getByRole("searchbox", { name: "Szukaj pojazdu" }).fill("TEST E2E");
  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Zamknij szczegóły pojazdu" }).click();
  const menu = page.getByRole("button", { name: "Otwórz menu", exact: true });
  if (await menu.isVisible()) await menu.click();
  await page.getByRole("button", { name: "Wyloguj się", exact: true }).click();
  await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
  await login(page, "viewer");
  await expect(page.getByRole("combobox", { name: "Elementów na stronę: pojazdy", exact: true })).toHaveValue("25");
  await expect(page.getByRole("searchbox", { name: "Szukaj pojazdu" })).toHaveValue("");
  await expect(page.getByRole("dialog")).toHaveCount(0);
});


async function accessible(page: Page, state: string) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  const findings = result.violations.map(item => ({
    id: item.id, impact: item.impact,
    targets: item.nodes.map(node => node.target),
  }));
  expect(findings, `axe: ${state}`).toEqual([]);
}

for (const theme of ["light", "dark"]) {
  test(`axe ${theme}: login, list, map fallback, details, annotation and error`, async ({ page }) => {
    await page.goto("/#vehicles");
    await expect(page.getByLabel("Login", { exact: true })).toBeVisible();
    await page.evaluate(value => document.documentElement.setAttribute("data-theme", value), theme);
    await accessible(page, "login");
    await login(page);
    await page.evaluate(value => document.documentElement.setAttribute("data-theme", value), theme);
    await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
    await accessible(page, "vehicle list");
    await page.goto("/#map");
    await expect(page.getByText("Mapa czeka na konfigurację").first()).toBeVisible();
    await accessible(page, "map fallback");
    await page.goto("/#vehicles");
    await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await accessible(page, "vehicle details dialog");
    await page.getByRole("dialog").getByRole("tab", { name: "Podróże", exact: true }).click();
    await page.getByRole("dialog").getByRole("list", { name: "Przejazdy pojazdu", exact: true }).getByRole("button").first().click();
    const form = page.getByRole("form", { name: "Cel i opis przejazdu", exact: true });
    await expect(form).toBeVisible();
    await accessible(page, "annotation editor");
    await form.getByLabel(/Cel przejazdu/).fill("Syntetyczny błąd dostępności");
    await page.route(`**/api/v1/trips/${trip}/annotation`, route => route.fulfill({
      status: 503, contentType: "application/json", body: JSON.stringify({ error: { code: "UNAVAILABLE" } }),
    }));
    await form.getByRole("button", { name: "Zapisz cel i opis", exact: true }).click();
    await expect(form.getByRole("alert")).toBeVisible();
    await accessible(page, "save error with retained draft");
    await page.screenshot({ path: test.info().outputPath(`axe-${theme}-error.png`) });
  });
}

test("keyboard opens details, traps focus, switches tabs and returns focus on Escape", async ({ page }) => {
  await login(page);
  const opener = page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ });
  await opener.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Zamknij szczegóły pojazdu" })).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  expect(await dialog.evaluate(element => element.contains(document.activeElement))).toBe(true);
  await page.keyboard.press("Tab");
  expect(await dialog.evaluate(element => element.contains(document.activeElement))).toBe(true);
  const vehicleTab = dialog.getByRole("tab", { name: "Pojazd", exact: true });
  await vehicleTab.focus();
  await page.keyboard.press("ArrowRight");
  await expect(dialog.getByRole("tab", { name: "Podróże", exact: true })).toBeFocused();
  await expect(dialog.getByRole("tab", { name: "Podróże", exact: true })).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(opener).toBeFocused();
});
