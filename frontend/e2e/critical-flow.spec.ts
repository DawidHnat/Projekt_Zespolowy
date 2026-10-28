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
