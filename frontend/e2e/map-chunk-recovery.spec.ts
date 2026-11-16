import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";

const trip = "22222222-2222-4222-8222-222222222222";
const isVehicleMapChunk = (url: string) =>
  /\/assets\/VehicleMap-[^/]+\.js(?:\?.*)?$/.test(url);

async function login(page: Page) {
  await page.goto("/#vehicles");
  await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /^Pojazdy\.?$/, level: 1 }),
  ).toBeVisible();
}

async function annotation(page: Page) {
  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("tab", { name: "Podróże", exact: true }).click();
  await dialog
    .getByRole("list", { name: "Przejazdy pojazdu", exact: true })
    .getByRole("button")
    .first()
    .click();
  return dialog.getByRole("form", { name: "Cel i opis przejazdu", exact: true });
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

for (const failure of ["404", "abort"] as const) {
  test(`recovers from a ${failure} map chunk without losing an edited trip`, async ({
    page,
  }) => {
    await login(page);
    const form = await annotation(page);
    const caseId = `${test.info().project.name} ${failure} ${Date.now()}`;
    const purpose = `Niezapisany cel ${caseId}`;
    const description = `Niezapisany opis ${caseId}`;
    await form.getByLabel(/Cel przejazdu/).fill(purpose);
    await form.getByLabel(/Opis przejazdu/).fill(description);

    let allowChunkLoad = false;
    await page.route("**/assets/VehicleMap-*.js", async (route) => {
      if (allowChunkLoad) {
        await route.continue();
        return;
      }
      if (failure === "404") {
        await route.fulfill({
          status: 404,
          contentType: "text/javascript",
          body: "",
        });
      } else {
        await route.abort();
      }
    });
    const chunkFailure =
      failure === "404"
        ? page.waitForResponse(
            (response) =>
              isVehicleMapChunk(response.url()) && response.status() === 404,
          )
        : page.waitForEvent("requestfailed", (request) =>
            isVehicleMapChunk(request.url()),
          );
    await page.evaluate(() => {
      window.location.hash = "#map";
    });
    await chunkFailure;

    await expect(page.locator("#root .app-shell")).toBeAttached();
    await expect(page.locator(".fleet-map-page .vehicle-card")).toContainText(
      "Pojazd E2E",
    );
    await expect(form.getByLabel(/Cel przejazdu/)).toHaveValue(purpose);
    await expect(form.getByLabel(/Opis przejazdu/)).toHaveValue(description);
    await expect(page.locator(".map-load-fallback")).toBeAttached();

    await form.getByRole("button", { name: "Zapisz cel i opis", exact: true }).click();
    await expect(form.getByRole("status")).toHaveText(
      "Cel i opis zostały zapisane.",
    );
    await page.getByRole("button", { name: "Zamknij szczegóły pojazdu" }).click();

    const mapError = page
      .getByRole("alert")
      .filter({ hasText: "Nie udało się załadować mapy" });
    await expect(mapError).toBeVisible();
    await expect(page.locator(".fleet-map-page .vehicle-card")).toContainText(
      "Pojazd E2E",
    );
    if (test.info().project.name === "mobile") {
      await page.getByRole("button", { name: "Otwórz menu" }).click();
      await expect(page.getByRole("link", { name: "Pojazdy" })).toBeAttached();
      await page
        .locator(".sidebar")
        .getByRole("button", { name: "Zamknij menu" })
        .click();
    } else {
      await expect(page.getByRole("link", { name: "Pojazdy" })).toBeAttached();
    }
    allowChunkLoad = true;
    await Promise.all([
      page.waitForNavigation({ waitUntil: "load" }),
      mapError.getByRole("button", { name: "Odśwież stronę" }).click(),
    ]);
    await expect(
      page.getByRole("heading", { name: /^Mapa\.?$/, level: 1 }),
    ).toBeVisible();
    await expect(page.getByText("Mapa czeka na konfigurację")).toBeVisible();
    await expect(mapError).toHaveCount(0);

    const saved = await page.request.get(`/api/v1/trips/${trip}`);
    expect(saved.ok()).toBeTruthy();
    expect((await saved.json()).annotation).toMatchObject({
      purpose,
      description,
    });
  });
}
