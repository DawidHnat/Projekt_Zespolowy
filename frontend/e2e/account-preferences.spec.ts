import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";
import { defaultLayout } from "../src/features/dashboard/model/widget-layout";

async function login(page: Page) {
  await page.goto("/#vehicles");
  await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.getByRole("heading", { name: /^Pojazdy\.?$/, level: 1 })).toBeVisible();
}

test.beforeEach(async ({ context }) => {
  execFileSync(
    process.env.E2E_PYTHON || "python3",
    ["tests/e2e_server.py", "reset-case"],
    {
      cwd: "../backend",
      env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
      stdio: "pipe",
    },
  );
  await context.route("**/*", (route) =>
    new URL(route.request().url()).hostname === "127.0.0.1"
      ? route.continue()
      : route.abort(),
  );
});

test("map layout changes are saved on the account and restored in a second browser", async ({
  page,
  browser,
}) => {
  await login(page);
  await page.goto("/#map");
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  await page.locator('[data-widget="map"]')
    .getByRole("button", { name: "Przesuń: Mapa floty", exact: true })
    .press("Shift+ArrowDown");
  await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
  await expect.poll(async () => {
    const response = await page.request.get("/api/v1/preferences/dashboard");
    const { value } = await response.json();
    return value?.layouts?.map;
  }).toBeTruthy();
  const response = await page.request.get("/api/v1/preferences/dashboard");
  const savedMapLayout = (await response.json()).value.layouts.map;
  expect(savedMapLayout.desktop).toHaveLength(2);
  expect(savedMapLayout.compact).toHaveLength(2);
  expect(
    JSON.stringify(savedMapLayout.desktop) !==
      JSON.stringify(defaultLayout("map", "desktop")) ||
      JSON.stringify(savedMapLayout.compact) !==
        JSON.stringify(defaultLayout("map", "compact")),
  ).toBe(true);

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
    await secondContext.route("**/*", (route) =>
      new URL(route.request().url()).hostname === "127.0.0.1"
        ? route.continue()
        : route.abort(),
    );
    const secondPage = await secondContext.newPage();
    await login(secondPage);
    await secondPage.goto("/#map");
    const restored = await secondPage.request.get("/api/v1/preferences/dashboard");
    expect((await restored.json()).value.layouts.map).toEqual(savedMapLayout);
  } finally {
    await secondContext.close();
  }
});

test("custom background is stored for the account and restored in a second browser", async ({
  page,
  browser,
}) => {
  await login(page);
  await page.goto("/#settings");
  await page.getByRole("navigation", { name: "Kategorie ustawień" })
    .getByRole("button", { name: /^Tło(?: |$)/ }).click();
  await page.getByRole("button", { name: "Własne", exact: true }).click();
  await page.getByLabel("Plik własnego tła").setInputFiles({
    name: "synthetic-wallpaper.png",
    mimeType: "image/png",
    buffer: Buffer.from(
      // Valid 1×1 RGB PNG (correct chunk CRCs); Chromium rejects a corrupted IDAT.
      "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGPQyVsBAAIMAUNPmq6sAAAAAElFTkSuQmCC",
      "base64",
    ),
  });
  await expect(page.getByRole("img", { name: "Podgląd własnego tła" })).toBeVisible();
  await expect.poll(async () => {
    const response = await page.request.get("/api/v1/preferences/dashboard");
    const { value } = await response.json();
    return value?.background?.customId;
  }).toMatch(/[0-9a-f-]{36}/i);
  const preference = await page.request.get("/api/v1/preferences/dashboard");
  const selectedId = (await preference.json()).value.background.customId as string;
  const storedImage = await page.request.get(`/api/v1/preferences/background/${selectedId}`);
  expect(storedImage.ok()).toBeTruthy();
  expect(storedImage.headers()["content-type"]).toBe("image/webp");

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
    await secondContext.route("**/*", (route) =>
      new URL(route.request().url()).hostname === "127.0.0.1"
        ? route.continue()
        : route.abort(),
    );
    const secondPage = await secondContext.newPage();
    await login(secondPage);
    await secondPage.goto("/#settings");
    await secondPage.getByRole("navigation", { name: "Kategorie ustawień" })
      .getByRole("button", { name: /^Tło(?: |$)/ }).click();
    await expect(secondPage.getByRole("img", { name: "Podgląd własnego tła" })).toBeVisible();
    const restored = await secondPage.request.get("/api/v1/preferences/dashboard");
    expect((await restored.json()).value.background.customId).toBe(selectedId);

    // A different account in the same browser does not see or reuse this background.
    const menu = secondPage.getByRole("button", { name: "Otwórz menu", exact: true });
    if (await menu.isVisible()) await menu.click();
    await secondPage.getByRole("button", { name: "Wyloguj się" }).click();
    await secondPage.getByLabel("Login", { exact: true }).fill("e2e-viewer");
    await secondPage.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
    await secondPage.getByRole("button", { name: "Zaloguj się", exact: true }).click();
    await expect(secondPage.locator(".main-shell")).toBeVisible();
    expect((await secondPage.request.get(`/api/v1/preferences/background/${selectedId}`)).status()).toBe(404);
    const viewerPreferences = await (await secondPage.request.get("/api/v1/preferences/dashboard")).json();
    expect(viewerPreferences.value?.background?.customId ?? null).not.toBe(selectedId);
  } finally {
    await secondContext.close();
  }
});
