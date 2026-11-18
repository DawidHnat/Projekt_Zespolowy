import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";

const trip = "22222222-2222-4222-8222-222222222222";
const vehicle = "11111111-1111-4111-8111-111111111111";

function sourceState(value: "ok" | "degraded" | "unavailable") {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "source-state", value], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
    stdio: "pipe",
  });
}

function measurementState(value: "moving" | "stopped" | "offline" | "unknown") {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "measurement-state", value], {
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

test.beforeEach(async ({ context }) => {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
    stdio: "pipe",
  });
  // Enforce an offline fixture: any accidentally introduced external call is blocked.
  await context.route("**/*", (route) => {
    const url = new URL(route.request().url());
    return url.hostname === "127.0.0.1" ? route.continue() : route.abort();
  });
});

test("account preferences sync between independent browsers and resolve concurrent edits", async ({ page, browser }) => {
  await login(page);
  const search = page.getByRole("searchbox", { name: "Szukaj pojazdu" });
  await expect(search).toBeEnabled();
  await search.fill("SYNC E2E");
  await page.getByLabel("Status pojazdu").selectOption("moving");
  await page.getByLabel("Sortowanie pojazdów").selectOption("odometer-desc");
  await page.getByRole("combobox", { name: "Elementów na stronę: pojazdy", exact: true }).selectOption("10");
  await expect.poll(async () => {
    const response = await page.request.get("/api/v1/preferences/vehicles");
    const { value } = await response.json();
    return [value?.filters?.q, value?.filters?.status, value?.sort, value?.pageSize];
  }).toEqual(["SYNC E2E", "moving", "odometer-desc", 10]);

  await page.evaluate(() => { window.location.hash = "#dashboard"; });
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  await page.getByRole("button", { name: "Wybierz widgety", exact: true }).click();
  const vehiclesWidget = page.getByRole("checkbox", { name: "Pokaż moduł: Pojazdy", exact: true });
  await expect(vehiclesWidget).toBeChecked();
  await vehiclesWidget.uncheck();
  await page.evaluate(() => { window.location.hash = "#dashboard"; });
  await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
  await expect.poll(async () => {
    const response = await page.request.get("/api/v1/preferences/dashboard");
    const { value } = await response.json();
    return value?.visibleWidgets;
  }).toEqual(["metrics", "map", "activity", "utilization", "trips"]);

  const mobile = test.info().project.name === "mobile";
  const secondContext = await browser.newContext({
    baseURL: "http://127.0.0.1:54173",
    locale: "pl-PL",
    timezoneId: "Europe/Warsaw",
    viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1000 },
    ...(mobile ? { isMobile: true, hasTouch: true } : {}),
  });
  try {
    await secondContext.route("**/*", (route) => {
      const url = new URL(route.request().url());
      return url.hostname === "127.0.0.1" ? route.continue() : route.abort();
    });
    const secondPage = await secondContext.newPage();
    await login(secondPage);
    await secondPage.evaluate(() => { window.location.hash = "#dashboard"; });
    await expect(secondPage.locator(".vehicles-widget")).toHaveCount(0);
    await secondPage.evaluate(() => { window.location.hash = "#vehicles"; });
    await expect(secondPage.getByRole("searchbox", { name: "Szukaj pojazdu" })).toHaveValue("SYNC E2E");
    await expect(secondPage.getByLabel("Status pojazdu")).toHaveValue("moving");
    await expect(secondPage.getByLabel("Sortowanie pojazdów")).toHaveValue("odometer-desc");

    await secondPage.getByRole("searchbox", { name: "Szukaj pojazdu" }).fill("SECOND DEVICE");
    await expect.poll(async () => {
      const response = await secondPage.request.get("/api/v1/preferences/vehicles");
      const { value } = await response.json();
      return value?.filters?.q;
    }).toBe("SECOND DEVICE");
    await page.evaluate(() => { window.location.hash = "#vehicles"; });
    await expect(page.getByLabel("Sortowanie pojazdów")).toBeVisible();
    await page.getByLabel("Sortowanie pojazdów").selectOption("name-desc");
    const conflict = page.getByRole("alert").filter({ hasText: "zmieniły się na innym urządzeniu" });
    await expect(conflict).toBeVisible();
    await conflict.getByRole("button", { name: "Zapisz moje zmiany", exact: true }).click();
    await expect.poll(async () => {
      const response = await page.request.get("/api/v1/preferences/vehicles");
      const { value } = await response.json();
      return [value?.filters?.q, value?.sort];
    }).toEqual(["SYNC E2E", "name-desc"]);
  } finally {
    await secondContext.close();
  }
});

test("dashboard preferences stay isolated when switching accounts in one browser", async ({ page, browser }) => {
  const widgets = ["metrics", "map", "activity", "vehicles", "utilization", "trips"];
  const localSettings = {
    theme: "light",
    accent: "#1479e8",
    material: "glass",
    visibleWidgets: [],
    layouts: {
      dashboard: {
        desktop: widgets.map((i, index) => ({ i, x: 0, y: index * 4, w: 12, h: 4 })),
        compact: widgets.map((i, index) => ({ i, x: 0, y: index * 4, w: 1, h: 4 })),
      },
    },
  };
  await page.addInitScript((value) => {
    localStorage.setItem("fleet-flow.dashboard.v2", JSON.stringify(value));
  }, localSettings);
  await login(page);
  await page.evaluate(() => { window.location.hash = "#dashboard"; });
  const migration = page.getByRole("region", { name: "Migracja ustawień: Pulpit" });
  await expect(migration).toBeVisible();
  await migration.getByRole("button", {
    name: "Przenieś z tej przeglądarki",
    exact: true,
  }).click();
  await expect.poll(async () => {
    const response = await page.request.get("/api/v1/preferences/dashboard");
    const { value } = await response.json();
    return value?.visibleWidgets;
  }).toEqual([]);

  const secondContext = await browser.newContext({
    baseURL: "http://127.0.0.1:54173",
    locale: "pl-PL",
    timezoneId: "Europe/Warsaw",
    viewport: test.info().project.name === "mobile"
      ? { width: 390, height: 844 }
      : { width: 1440, height: 1000 },
    ...(test.info().project.name === "mobile"
      ? { isMobile: true, hasTouch: true }
      : {}),
  });
  try {
    await secondContext.route("**/*", (route) => {
      const url = new URL(route.request().url());
      return url.hostname === "127.0.0.1" ? route.continue() : route.abort();
    });
    const accountAPage = await secondContext.newPage();
    await login(accountAPage);

    await page.evaluate(() => { window.location.hash = "#dashboard"; });
    await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
    await page.getByRole("button", { name: "Wybierz widgety", exact: true }).click();
    for (const widget of [
      "Przegląd floty",
      "Mapa floty",
      "Alerty i aktywność",
      "Pojazdy",
      "Wykorzystanie floty",
      "Ostatnie przejazdy",
    ]) {
      const checkbox = page.getByRole("checkbox", {
        name: `Pokaż moduł: ${widget}`,
        exact: true,
      });
      if (await checkbox.isChecked()) await checkbox.uncheck();
    }
    await page.evaluate(() => { window.location.hash = "#dashboard"; });
    await expect(page.getByRole("heading", { name: /^Pulpit\.?$/, level: 1 })).toBeVisible();
    await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
    await expect.poll(async () => {
      const response = await page.request.get("/api/v1/preferences/dashboard");
      const { value } = await response.json();
      return value?.visibleWidgets;
    }).toEqual([]);

    const menu = page.getByRole("button", { name: "Otwórz menu", exact: true });
    if (await menu.isVisible()) await menu.click();
    await page.getByRole("button", { name: "Wyloguj się", exact: true }).click();
    await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
    await login(page, "editor-two");
    await page.evaluate(() => { window.location.hash = "#dashboard"; });
    await expect(page.locator("[data-widget]")).toHaveCount(6);
    await expect(page.getByRole("region", { name: "Migracja ustawień: Pulpit" })).toHaveCount(0);

    const accountBBeforeSave = await page.request.get("/api/v1/preferences/dashboard");
    expect(await accountBBeforeSave.json()).toMatchObject({
      version: 0,
      value: null,
    });
    await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
    await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
    await expect.poll(async () => {
      const response = await page.request.get("/api/v1/preferences/dashboard");
      const { version, value } = await response.json();
      return [version, value?.visibleWidgets?.length];
    }).toEqual([1, 6]);

    const accountA = await accountAPage.request.get("/api/v1/preferences/dashboard");
    expect((await accountA.json()).value.visibleWidgets).toEqual([]);
  } finally {
    await secondContext.close();
  }
});

for (const initialRead of ["failed", "cancelled"] as const) {
  test(`dashboard migration stays with its first account after a ${initialRead} initial read`, async ({ page }) => {
    const widgets = ["metrics", "map", "activity", "vehicles", "utilization", "trips"];
    await page.addInitScript((ids) => {
      if (sessionStorage.getItem("migration-fixture-seeded")) return;
      localStorage.setItem("fleet-flow.dashboard.v2", JSON.stringify({
        theme: "light",
        accent: "#1479e8",
        material: "glass",
        visibleWidgets: [],
        layouts: {
          dashboard: {
            desktop: ids.map((i, index) => ({ i, x: 0, y: index * 4, w: 12, h: 4 })),
            compact: ids.map((i, index) => ({ i, x: 0, y: index * 4, w: 1, h: 4 })),
          },
        },
      }));
      sessionStorage.setItem("migration-fixture-seeded", "true");
    }, widgets);

    let firstReadSeen = false;
    let releaseRead = () => {};
    const heldRead = new Promise<void>((resolve) => { releaseRead = resolve; });
    await page.route("**/api/v1/preferences/dashboard", async (route) => {
      if (route.request().method() !== "GET" || firstReadSeen) {
        await route.continue();
        return;
      }
      firstReadSeen = true;
      if (initialRead === "failed") {
        await route.fulfill({
          status: 503,
          json: { error: { code: "UNAVAILABLE", message: "Testowy błąd odczytu ustawień." } },
        });
      } else {
        await heldRead;
        await route.abort();
      }
    });

    const loginWithoutReload = async (role: string) => {
      await page.getByLabel("Login", { exact: true }).fill(`e2e-${role}`);
      await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
      await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
      await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toHaveCount(0);
    };
    const logout = async () => {
      const menu = page.getByRole("button", { name: "Otwórz menu", exact: true });
      if (await menu.isVisible()) await menu.click();
      await page.getByRole("button", { name: "Wyloguj się", exact: true }).click();
      await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
    };

    try {
      await login(page);
      await expect.poll(() => firstReadSeen).toBe(true);
      await page.evaluate(() => { window.location.hash = "#dashboard"; });
      if (initialRead === "failed") {
        await expect(page.getByRole("alert").filter({ hasText: "Nie udało się pobrać danych. Spróbuj ponownie." })).toBeVisible();
      }
      await logout();
      releaseRead();
      await loginWithoutReload("editor-two");
      await page.evaluate(() => { window.location.hash = "#dashboard"; });
      await expect(page.getByText("Pobieranie zapisanych ustawień: Pulpit…")).toHaveCount(0);
      await expect(page.locator("[data-widget]")).toHaveCount(6);
      const migration = page.getByRole("region", { name: "Migracja ustawień: Pulpit" });
      await expect(migration).toHaveCount(0);
      expect(await (await page.request.get("/api/v1/preferences/dashboard")).json()).toMatchObject({
        version: 0,
        value: null,
      });
      await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
      await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
      await expect.poll(async () => {
        const { value } = await (await page.request.get("/api/v1/preferences/dashboard")).json();
        return value?.visibleWidgets?.length;
      }).toBe(6);

      await logout();
      await loginWithoutReload("editor");
      await expect(migration).toBeVisible();
      await migration.getByRole("button", { name: "Przenieś z tej przeglądarki", exact: true }).click();
      await expect.poll(async () => {
        const { value } = await (await page.request.get("/api/v1/preferences/dashboard")).json();
        return value?.visibleWidgets;
      }).toEqual([]);
      await page.screenshot({ path: test.info().outputPath(`migration-${initialRead}-owner.png`) });
    } finally {
      releaseRead();
    }
  });
}

test("local dashboard settings require explicit migration and cannot replace account settings", async ({ page, browser }) => {
  const widgets = ["metrics", "map", "activity", "vehicles", "utilization", "trips"];
  const localSettings = {
    theme: "light",
    accent: "#1479e8",
    material: "glass",
    visibleWidgets: ["metrics"],
    layouts: {
      dashboard: {
        desktop: widgets.map((i, index) => ({ i, x: 0, y: index * 4, w: 12, h: 4 })),
        compact: widgets.map((i, index) => ({ i, x: 0, y: index * 4, w: 1, h: 4 })),
      },
    },
  };
  await page.addInitScript(({ key, value }) => {
    if (sessionStorage.getItem("migration-reload-seeded")) return;
    localStorage.setItem(key, JSON.stringify(value));
    sessionStorage.setItem("migration-reload-seeded", "true");
  }, { key: "fleet-flow.dashboard.v2", value: localSettings });
  await login(page);
  await page.evaluate(() => { window.location.hash = "#dashboard"; });
  const migration = page.getByRole("region", { name: "Migracja ustawień: Pulpit" });
  await expect(migration).toBeVisible();
  await page.reload();
  await page.evaluate(() => { window.location.hash = "#dashboard"; });
  await expect(migration).toBeVisible();
  await page.evaluate(() => { window.location.hash = "#dashboard"; });
  await expect(page.getByRole("button", { name: "Edytuj układ", exact: true })).toBeDisabled();
  await page.evaluate(() => { window.location.hash = "#settings"; });
  await page.getByRole("button", { name: /Układ i moduły/ }).click();
  await expect(page.getByRole("checkbox", { name: "Pokaż moduł: Pojazdy", exact: true })).toBeDisabled();
  const beforeMigration = await page.request.get("/api/v1/preferences/dashboard");
  expect((await beforeMigration.json()).version).toBe(0);
  await migration.getByRole("button", { name: "Przenieś z tej przeglądarki", exact: true }).click();
  await expect.poll(async () => {
    const response = await page.request.get("/api/v1/preferences/dashboard");
    const { version, value } = await response.json();
    return [version, value?.visibleWidgets];
  }).toEqual([1, ["metrics"]]);

  const mobile = test.info().project.name === "mobile";
  const secondContext = await browser.newContext({
    baseURL: "http://127.0.0.1:54173",
    locale: "pl-PL",
    timezoneId: "Europe/Warsaw",
    viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1000 },
    ...(mobile ? { isMobile: true, hasTouch: true } : {}),
  });
  try {
    await secondContext.route("**/*", (route) => {
      const url = new URL(route.request().url());
      return url.hostname === "127.0.0.1" ? route.continue() : route.abort();
    });
    const secondPage = await secondContext.newPage();
    await secondPage.addInitScript(({ key, value }) => {
      localStorage.setItem(key, JSON.stringify(value));
    }, {
      key: "fleet-flow.dashboard.v2",
      value: { ...localSettings, visibleWidgets: ["trips"] },
    });
    await login(secondPage);
    await expect(secondPage.getByRole("region", { name: "Migracja ustawień: Pulpit" })).toHaveCount(0);
    const remote = await secondPage.request.get("/api/v1/preferences/dashboard");
    expect((await remote.json()).value.visibleWidgets).toEqual(["metrics"]);
  } finally {
    await secondContext.close();
  }

  const { user: { id } } = await (await page.request.get("/api/v1/auth/me")).json();
  await page.evaluate((userId) => {
    localStorage.setItem(`fleet-flow.list-page-size.v1.${userId}`, "10");
  }, id);
  await page.reload();
  await page.evaluate(() => { window.location.hash = "#vehicles"; });
  const vehicleMigration = page.getByRole("region", { name: "Migracja ustawień: Pojazdy" });
  const pageSize = page.getByRole("combobox", { name: "Elementów na stronę: pojazdy", exact: true });
  await expect(vehicleMigration).toBeVisible();
  await expect(pageSize).toHaveValue("10");
  await expect(pageSize).toBeDisabled();
  const beforeVehicleMigration = await page.request.get("/api/v1/preferences/vehicles");
  expect((await beforeVehicleMigration.json()).version).toBe(0);
  await vehicleMigration.getByRole("button", { name: "Przenieś z tej przeglądarki", exact: true }).click();
  await expect.poll(async () => {
    const response = await page.request.get("/api/v1/preferences/vehicles");
    const { version, value } = await response.json();
    return [version, value?.pageSize];
  }).toEqual([1, 10]);
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

test("vehicle details recover from an initial 503 without signing in again", async ({ page }) => {
  const pageErrors: string[] = [];
  page.on("pageerror", error => pageErrors.push(error.message));
  const detailPath = `**/api/v1/fleet/vehicles/${vehicle}`;
  await page.route(detailPath, route => route.fulfill({
    status: 503,
    contentType: "application/json",
    body: JSON.stringify({ error: { code: "DATABASE_UNAVAILABLE" } }),
  }));
  await login(page);
  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  const dialog = page.getByRole("dialog");
  const alert = dialog.getByRole("alert");
  await expect(alert).toContainText("Baza danych jest chwilowo niedostępna.");
  await expect(alert.getByRole("button", { name: "Spróbuj ponownie" })).toBeVisible();
  await expect(dialog.getByRole("status")).toHaveCount(0);
  await page.unroute(detailPath);
  await alert.getByRole("button", { name: "Spróbuj ponownie" }).click();
  await expect(dialog.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  await expect(dialog.getByRole("tab", { name: "Pojazd", exact: true })).toBeVisible();
  expect(pageErrors).toEqual([]);
});

test("detail refresh failure warns and preserves an unsaved trip draft", async ({ page }) => {
  await page.clock.install();
  await page.clock.pauseAt(new Date());
  const pageErrors: string[] = [];
  page.on("pageerror", error => pageErrors.push(error.message));
  const detailPath = `**/api/v1/fleet/vehicles/${vehicle}`;
  await login(page);
  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  await dialog.getByRole("tab", { name: "Podróże", exact: true }).click();
  await dialog.getByRole("list", { name: "Przejazdy pojazdu", exact: true }).getByRole("button").first().click();
  const form = dialog.getByRole("form", { name: "Cel i opis przejazdu", exact: true });
  const draft = `Szkic po błędzie odświeżania ${Date.now()}`;
  await form.getByLabel(/Cel przejazdu/).fill(draft);
  await page.route(detailPath, route => route.fulfill({
    status: 503,
    contentType: "application/json",
    body: JSON.stringify({ error: { code: "DATABASE_UNAVAILABLE" } }),
  }));
  const failedRefresh = page.waitForResponse(response =>
    new URL(response.url()).pathname === `/api/v1/fleet/vehicles/${vehicle}` &&
    response.status() === 503,
  );
  await page.evaluate(() => window.dispatchEvent(new Event("online")));
  await failedRefresh;
  const alert = dialog.getByRole("alert");
  await expect(alert).toContainText("Baza danych jest chwilowo niedostępna.");
  await expect(form.getByLabel(/Cel przejazdu/)).toHaveValue(draft);
  await page.unroute(detailPath);
  await alert.getByRole("button", { name: "Spróbuj ponownie" }).click();
  await expect(dialog.getByRole("alert")).toHaveCount(0);
  await expect(form.getByLabel(/Cel przejazdu/)).toHaveValue(draft);
  expect(pageErrors).toEqual([]);
});

test("missing vehicle details close the dialog without changing list state", async ({ page }) => {
  const detailPath = `**/api/v1/fleet/vehicles/${vehicle}`;
  await page.route(detailPath, route => route.fulfill({
    status: 404,
    contentType: "application/json",
    body: JSON.stringify({ error: { code: "NOT_FOUND" } }),
  }));
  await login(page);
  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
});

test("unauthorized detail refresh removes private state and returns to login", async ({ page }) => {
  await page.clock.install();
  await page.clock.pauseAt(new Date());
  const detailPath = `**/api/v1/fleet/vehicles/${vehicle}`;
  await login(page);
  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  await dialog.getByRole("tab", { name: "Podróże", exact: true }).click();
  await dialog.getByRole("list", { name: "Przejazdy pojazdu", exact: true }).getByRole("button").first().click();
  const form = dialog.getByRole("form", { name: "Cel i opis przejazdu", exact: true });
  await form.getByLabel(/Cel przejazdu/).fill("Prywatny szkic do usunięcia");
  await page.route(detailPath, route => route.fulfill({
    status: 401,
    contentType: "application/json",
    body: JSON.stringify({ error: { code: "UNAUTHENTICATED" } }),
  }));
  const unauthorizedRefresh = page.waitForResponse(response =>
    new URL(response.url()).pathname === `/api/v1/fleet/vehicles/${vehicle}` &&
    response.status() === 401,
  );
  await page.evaluate(() => window.dispatchEvent(new Event("online")));
  await unauthorizedRefresh;
  await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByLabel(/Cel przejazdu/)).toHaveCount(0);
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
  // Always cross Polish midnight: the old CI failure depended on the run hour.
  const beforeMidnight = await page.evaluate(() => {
    const time = new Date();
    time.setHours(23, 55, 0, 0);
    return time.toISOString();
  });
  await page.clock.pauseAt(new Date(beforeMidnight));
  let lists = 0;
  let details = 0;
  let tripLists = 0;
  page.on("request", request => {
    const path = new URL(request.url()).pathname;
    if (path === "/api/v1/fleet/vehicles") lists++;
    if (path === "/api/v1/trips") tripLists++;
    if (/\/api\/v1\/fleet\/vehicles\/[^/]+$/.test(path)) details++;
  });
  await login(page);
  const form = await annotation(page);
  await form.getByLabel(/Cel przejazdu/).fill("Szkic przy odświeżaniu");
  await expect(page.getByText("Przed zmianą dnia lub przejazdu zapisz albo anuluj edycję.")).toBeVisible();
  const beforeEditing = tripLists;
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
  expect(tripLists).toBe(beforeEditing);
  await page.screenshot({ path: test.info().outputPath("polling-preserves-draft.png") });
  // Once the user finishes the draft, relative Today catches up to the new day.
  await form.getByRole("button", { name: "Anuluj zmiany", exact: true }).click();
  await expect.poll(() => tripLists).toBe(beforeEditing + 1);
  await expect(page.getByRole("heading", { name: "Brak zapisanych przejazdów", exact: true })).toBeVisible();
  await expect(form).toHaveCount(0);
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

test("SCRUM-20: pending and failed filters never display vehicles from the previous query", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/v1/fleet/vehicles?**", async route => {
    if (new URL(route.request().url()).searchParams.get("q") !== "no-such-synthetic-vehicle")
      return route.continue();
    await held;
    await route.fulfill({ status: 503, contentType: "application/json",
      body: JSON.stringify({ error: { code: "TEMPORARY_FAILURE", message: "Nie udało się pobrać wyników testowych." } }) });
  });
  try {
    const pending = page.waitForRequest(request => new URL(request.url()).searchParams.get("q") === "no-such-synthetic-vehicle");
    await page.getByRole("searchbox", { name: "Szukaj pojazdu" }).fill("no-such-synthetic-vehicle");
    await pending;
    await expect(page.getByRole("heading", { name: "Pobieranie pojazdów…", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toHaveCount(0);
  } finally {
    release();
  }
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toHaveCount(0);
  await page.unroute("**/api/v1/fleet/vehicles?**");
  await page.getByRole("button", { name: "Ponów", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Brak pasujących pojazdów", exact: true })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page.getByRole("button", { name: "Wyczyść filtry", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
});

test("SCRUM-20: pending and failed sorting never displays results from the previous order", async ({ page }) => {
  await login(page);
  const vehicle = page.getByRole("heading", { name: "Pojazd E2E", exact: true });
  await expect(vehicle).toBeVisible();
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/v1/fleet/vehicles?**", async route => {
    if (new URL(route.request().url()).searchParams.get("sort") !== "name-desc")
      return route.continue();
    await held;
    await route.fulfill({ status: 503, contentType: "application/json",
      body: JSON.stringify({ error: { code: "TEMPORARY_FAILURE", message: "Sortowanie testowe niedostępne." } }) });
  });
  try {
    const pending = page.waitForRequest(request => new URL(request.url()).searchParams.get("sort") === "name-desc");
    await page.getByRole("combobox", { name: "Sortowanie pojazdów", exact: true }).selectOption("name-desc");
    await pending;
    await expect(page.getByRole("heading", { name: "Pobieranie pojazdów…", exact: true })).toBeVisible();
    await expect(vehicle).toHaveCount(0);
  } finally {
    release();
  }
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(vehicle).toHaveCount(0);
  await page.unroute("**/api/v1/fleet/vehicles?**");
  await page.getByRole("button", { name: "Ponów", exact: true }).click();
  await expect(vehicle).toBeVisible();
});

test("SCRUM-20: failed pagination hides the previous page and lets the user return", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  const data = await (await page.request.get("/api/v1/fleet/vehicles")).json();
  await page.route("**/api/v1/fleet/vehicles?**", async route => {
    if (new URL(route.request().url()).searchParams.get("page") === "2")
      return route.fulfill({ status: 503, contentType: "application/json",
        body: JSON.stringify({ error: { code: "TEMPORARY_FAILURE", message: "Strona testowa niedostępna." } }) });
    // A synthetic multi-page response, confined to this browser test.
    await route.fulfill({ json: { ...data, total: 26, page_size: 10 } });
  });
  await page.getByRole("combobox", { name: "Elementów na stronę: pojazdy", exact: true }).selectOption("10");
  await page.getByRole("button", { name: "Następna strona: pojazdy", exact: true }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toHaveCount(0);
  await expect(page.getByLabel("Strona 2 z 3", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Poprzednia strona: pojazdy", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
});

test("SCRUM-20: search, status, selection and reset are shared with the map list", async ({ page }) => {
  await login(page);
  await page.getByRole("searchbox", { name: "Szukaj pojazdu" }).fill("TEST E2E");
  await page.getByRole("combobox", { name: "Status pojazdu", exact: true }).selectOption("stopped");
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Na mapie", exact: true }).click();
  const list = page.locator(".vehicle-sidebar");
  await expect(list.getByRole("searchbox", { name: "Szukaj pojazdu" })).toHaveValue("TEST E2E");
  await expect(list.getByRole("combobox", { name: "Status pojazdu", exact: true })).toHaveValue("stopped");
  const vehicle = list.getByRole("button", { name: /Pojazd E2E/ });
  await expect(vehicle).toHaveAttribute("aria-pressed", "true");
  await expect(vehicle).not.toContainText("Prędkość");
  await expect(vehicle).toContainText("Przebieg · 1234,5 km");
  await expect(page.getByText("Mapa czeka na konfigurację", { exact: true })).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("scrum20-active-filters.png"), fullPage: true });
  await page.goto("/#settings");
  await page.getByRole("button", { name: "Ciemny", exact: true }).click();
  await page.goto("/#map");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(vehicle).toHaveAttribute("aria-pressed", "true");
  await expect.poll(() => list.locator(".vehicle-cards").evaluate(element =>
    element.clientHeight >= (element.firstElementChild?.getBoundingClientRect().height ?? 0),
  )).toBe(true);
  await page.screenshot({ path: test.info().outputPath("scrum20-active-filters-dark.png"), fullPage: true });
  await list.getByRole("button", { name: "Wyczyść filtry", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(list.getByRole("searchbox", { name: "Szukaj pojazdu" })).toHaveValue("");
  await expect(list.getByRole("searchbox", { name: "Szukaj pojazdu" })).toBeFocused();
  await expect(list.getByRole("combobox", { name: "Status pojazdu", exact: true })).toHaveValue("");
  await expect(vehicle).toHaveAttribute("aria-pressed", "false");
  await expect.poll(async () => {
    const response = await page.request.get("/api/v1/preferences/vehicles");
    const { value } = await response.json();
    return value?.filters;
  }).toEqual({ q: "", status: "" });
  await list.getByRole("combobox", { name: "Status pojazdu", exact: true }).selectOption("moving");
  await expect(list.getByRole("heading", { name: "Brak wyników", exact: true })).toBeVisible();
  await list.getByRole("button", { name: "Wyczyść filtry", exact: true }).click();
  await expect(vehicle).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("scrum20-shared-filters.png") });
});

test("SCRUM-20: a background failure keeps matching cached results with an explicit warning", async ({ page }) => {
  await page.clock.install();
  await page.clock.pauseAt(new Date());
  await login(page);
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  await page.route("**/api/v1/fleet/vehicles?**", route => route.fulfill({
    status: 503, contentType: "application/json",
    body: JSON.stringify({ error: { code: "TEMPORARY_FAILURE", message: "Niedostępność testowa." } }),
  }));
  await page.clock.fastForward(60_000);
  await expect(page.getByRole("alert")).toContainText("Wyświetlamy ostatni poprawny odczyt:");
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
});

test("SCRUM-20: changing filters offline shows an error and resumes automatically online", async ({ page }) => {
  await page.clock.install();
  await page.clock.pauseAt(new Date());
  let requests = 0;
  page.on("request", request => {
    if (new URL(request.url()).pathname === "/api/v1/fleet/vehicles") requests++;
  });
  await login(page);
  const vehicle = page.getByRole("heading", { name: "Pojazd E2E", exact: true });
  await expect(vehicle).toBeVisible();
  const beforeOffline = requests;
  await page.evaluate(() => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: false });
    window.dispatchEvent(new Event("offline"));
  });
  await expect(page.getByRole("alert")).toContainText("Wyświetlamy ostatni poprawny odczyt:");
  await expect(vehicle).toBeVisible();
  await page.screenshot({ path: test.info().outputPath("scrum20-offline-cache.png"), fullPage: true });
  await page.getByRole("searchbox", { name: "Szukaj pojazdu" }).fill("no-such-synthetic-vehicle");
  await page.clock.fastForward(1000);
  await expect(page.getByRole("alert")).toContainText("Brak połączenia z siecią");
  await expect(page.getByRole("heading", { name: "Pobieranie pojazdów…", exact: true })).toHaveCount(0);
  await expect(vehicle).toHaveCount(0);
  expect(requests).toBe(beforeOffline);
  await page.screenshot({ path: test.info().outputPath("scrum20-offline-filter.png"), fullPage: true });
  await page.evaluate(() => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
    window.dispatchEvent(new Event("online"));
  });
  await expect(page.getByRole("heading", { name: "Brak pasujących pojazdów", exact: true })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page.getByRole("button", { name: "Wyczyść filtry", exact: true }).click();
  await expect(vehicle).toBeVisible();
  await expect(page.getByRole("searchbox", { name: "Szukaj pojazdu" })).toBeFocused();
});

test("SCRUM-20: mounting the fleet while offline reports the pause instead of loading forever", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: false });
  });
  await page.reload();
  await expect(page.getByRole("alert")).toContainText("Brak połączenia z siecią");
  await expect(page.getByRole("heading", { name: "Pobieranie pojazdów…", exact: true })).toHaveCount(0);
  await page.evaluate(() => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
    window.dispatchEvent(new Event("online"));
  });
  await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
});
for (const transport of ["BroadcastChannel", "storage"]) {
  test(`password reset removes private drafts in other tabs without polling (${transport})`, async ({ page, context }) => {
    if (transport === "storage") {
      await context.addInitScript(() => {
        Object.defineProperty(window, "BroadcastChannel", { value: undefined });
      });
    }
    await login(page);
    const other = await context.newPage();
    await other.goto("/#vehicles");
    const form = await annotation(other);
    await form.getByLabel(/Cel przejazdu/).fill("Prywatny szkic przed resetem");
    // A reset must clear the view even while this hidden tab's reads are paused.
    await other.evaluate(() => {
      Object.defineProperty(document, "visibilityState", { configurable: true, value: "hidden" });
      document.dispatchEvent(new Event("visibilitychange"));
    });
    // SMTP/token handling has separate backend tests. Reproduce the successful
    // reset response and revoke the real fixture session without sending mail.
    await page.route("**/api/v1/auth/password/confirm", async route => {
      expect((await page.request.post("/api/v1/auth/logout", {
        headers: { Origin: "http://127.0.0.1:54173" },
      })).ok()).toBeTruthy();
      await route.fulfill({ status: 200, contentType: "application/json", body: '{"ok":true}' });
    });
    await page.goto("/#reset-password?token=synthetic-reset-token-without-smtp");
    await page.getByLabel("Nowe hasło", { exact: true }).fill("synthetic-new-password");
    await page.getByLabel("Powtórz hasło", { exact: true }).fill("synthetic-new-password");
    await page.getByRole("button", { name: "Zapisz nowe hasło", exact: true }).click();
    await expect(page.getByRole("status")).toContainText("Hasło zostało zmienione");
    await expect(other.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
    await expect(form).toHaveCount(0);
    await expect(other.getByLabel(/Cel przejazdu/)).toHaveCount(0);
    expect((await other.request.get("/api/v1/auth/me")).status()).toBe(401);
    await other.screenshot({ path: test.info().outputPath("reset-cleared-other-tab.png") });
  });

  test(`other tabs discard private drafts on logout and load the shared account on login (${transport})`, async ({ page, context }) => {
    if (transport === "storage") {
      await context.addInitScript(() => {
        Object.defineProperty(window, "BroadcastChannel", { value: undefined });
      });
    }
    await login(page);
    const other = await context.newPage();
    await other.goto("/#vehicles");
    const form = await annotation(other);
    await form.getByLabel(/Cel przejazdu/).fill("Prywatny szkic edytora");

    const menu = page.getByRole("button", { name: "Otwórz menu", exact: true });
    if (await menu.isVisible()) await menu.click();
    await page.getByRole("button", { name: "Wyloguj się", exact: true }).click();
    await expect(other.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
    await expect(form).toHaveCount(0);

    await login(page, "viewer");
    const reopened = await annotation(other);
    await expect(reopened.getByLabel(/Cel przejazdu/)).toHaveAttribute("readonly", "");
    await expect(reopened.getByLabel(/Cel przejazdu/)).not.toHaveValue("Prywatny szkic edytora");
    await expect(other.getByRole("button", { name: "Zapisz cel i opis", exact: true })).toHaveCount(0);
  });
}

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
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.addInitScript(value => {
      localStorage.setItem("fleet-flow.dashboard.v2", JSON.stringify({ theme: value }));
    }, theme);
    await page.goto("/#vehicles");
    await expect(page.getByLabel("Login", { exact: true })).toBeVisible();
    await accessible(page, "login");
    await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
    await page.getByLabel("Hasło", { exact: true }).fill("synthetic-wrong-password");
    await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
    await expect(page.getByRole("alert")).toBeVisible();
    await accessible(page, "login error");
    await login(page);
    await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
    await accessible(page, "vehicle list: stopped");
    for (const status of ["moving", "offline", "unknown"] as const) {
      measurementState(status);
      await page.reload();
      await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
      await accessible(page, `vehicle list: ${status}`);
    }
    measurementState("stopped");
    await page.reload();
    await expect(page.getByRole("heading", { name: "Pojazd E2E", exact: true })).toBeVisible();
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
  await page.keyboard.press("End");
  await expect(dialog.getByRole("tab", { name: "Podróże", exact: true })).toBeFocused();
  await expect(dialog.getByRole("tab", { name: "Podróże", exact: true })).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Escape");
  await expect(dialog).not.toBeVisible();
  await expect(opener).toBeFocused();
  await page.keyboard.press("Space");
  await expect(dialog).toBeVisible();
  await dialog.getByRole("tab", { name: "Pojazd", exact: true }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(dialog.getByRole("tab", { name: "Kierowca", exact: true })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(opener).toBeFocused();
});

for (const theme of ["light", "dark"]) {
  test(`planned modules and local-only data ${theme}`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.addInitScript(value => {
      localStorage.setItem("fleet-flow.dashboard.v2", JSON.stringify({ theme: value }));
    }, theme);
    await login(page);
    const openMenu = async () => {
      const menu = page.getByRole("button", { name: "Otwórz menu", exact: true });
      if (await menu.isVisible()) await menu.click();
    };
    for (const title of ["Serwis", "Ewidencja przebiegu", "Kierowcy", "Karty paliwowe", "Alerty"]) {
      await openMenu();
      const link = page.getByRole("navigation", { name: "Sekcje aplikacji" })
        .getByRole("link", { name: `${title} Planowane`, exact: true });
      await link.focus();
      await expect(link).toBeFocused();
      await page.keyboard.press("Enter");
      await expect(page.getByRole("heading", { name: new RegExp(`^${title}\\.?$`), level: 1 })).toBeVisible();
      await expect(page.locator(".planned-page").getByText("Planowane", { exact: true })).toBeVisible();
      await accessible(page, `planned ${title}`);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    }
    await openMenu();
    await page.getByRole("link", { name: "Ustawienia", exact: true }).click();
    await expect(page.getByText(/Wygląd, tło i układ Mapy zapisują się tylko w tej przeglądarce/)).toBeVisible();
    await page.getByRole("navigation", { name: "Kategorie ustawień" }).getByRole("button", { name: /^Tło(?: |$)/ }).click();
    await page.getByRole("button", { name: "Własne", exact: true }).click();
    await expect(page.getByText(/Tylko na tym urządzeniu i w tej przeglądarce\. Nie wysyłamy zdjęcia/)).toBeVisible();
    await accessible(page, "local background and settings");
    await page.screenshot({ path: test.info().outputPath(`local-settings-${theme}.png`) });
    await openMenu();
    await page.getByRole("navigation", { name: "Sekcje aplikacji" }).getByRole("link", { name: "Pojazdy", exact: true }).click();
    const opener = page.getByRole("button", { name: "Zdjęcie: Pojazd E2E", exact: true });
    await opener.focus();
    await page.keyboard.press("Enter");
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByText(/Tylko na tym urządzeniu i w tej przeglądarce, dla Twojego konta/)).toBeVisible();
    await accessible(page, "local vehicle photo");
    await page.screenshot({ path: test.info().outputPath(`local-photo-${theme}.png`) });
    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
    await expect(opener).toBeFocused();
  });
}
