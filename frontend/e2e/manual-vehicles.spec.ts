import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";

function resetDatabase() {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
    cwd: "../backend",
    env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true", SYNC_ENABLED: "false" },
  });
}

async function logout(page: Page) {
  const openMenu = page.getByRole("button", { name: "Otwórz menu" });
  if (await openMenu.isVisible()) await openMenu.click();
  await page.getByRole("button", { name: "Wyloguj się" }).click();
}

test.beforeEach(() => {
  resetDatabase();
});

test("SCRUM-85: editor adds manual vehicle without WEBFLEET GPS, validates fields, preserves card on reopen, and viewer is read-only", async ({ page }) => {
  await page.goto("/#vehicles");
  await page.getByLabel("Login").fill("e2e-editor");
  await page.getByLabel("Hasło").fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się" }).click();

  await page.getByRole("button", { name: "Dodaj pojazd ręcznie" }).click();
  const dialog = page.getByRole("dialog", { name: "Dodaj pojazd bez lokalizatora" });
  await expect(dialog).toBeVisible();

  // Trigger inline field validation errors.
  await dialog.getByRole("button", { name: "Utwórz pojazd" }).click();
  await expect(dialog.getByText("Podaj nazwę pojazdu.")).toBeVisible();
  await expect(dialog.getByText("Podaj numer rejestracyjny.")).toBeVisible();

  await dialog.getByLabel("Nazwa pojazdu").fill("Toyota Corolla Ręczna");
  await dialog.getByLabel("Numer rejestracyjny").fill("GD 850MN");
  await dialog.getByLabel("Marka").fill("Toyota");
  await dialog.getByLabel("Model").fill("Corolla");
  await dialog.getByLabel("Paliwo").fill("hybryda");
  await dialog.getByLabel("Firma leasingowa").fill("EFL Leasing");
  await dialog.getByLabel("Przebieg ręczny w km (opcjonalnie)").fill("34500");

  // Pick odometer date via shared DatePicker calendar (no manual typing in date trigger).
  await dialog.getByRole("button", { name: /Data odczytu przebiegu/ }).click();
  await dialog
    .getByRole("dialog", { name: /Wybierz datę: Data odczytu/ })
    .locator(".flatpickr-day.today")
    .click();

  await dialog.getByRole("button", { name: "Utwórz pojazd" }).click();

  // Details dialog opens automatically with saved manual card data and no fake GPS.
  const details = page.getByRole("dialog", { name: "Toyota Corolla Ręczna" });
  await expect(details).toBeVisible();
  await expect(details.getByText("Ręczny (bez lokalizatora WEBFLEET)")).toBeVisible();
  await expect(details.getByText("EFL Leasing")).toBeVisible();
  await expect(details.getByText("hybryda")).toBeVisible();
  await details.getByRole("button", { name: "Zamknij szczegóły pojazdu" }).click();

  // Reopen from tile to verify persistence and absence of fake GPS.
  const tile = page.getByLabel("Kafelek Toyota Corolla Ręczna");
  await expect(tile).toContainText("GD 850MN · Ręczny");
  await expect(tile).toContainText("34 500 km");
  await expect(tile).toContainText("Brak GPS");
  await page.getByRole("button", { name: "Szczegóły: Toyota Corolla Ręczna" }).click();
  await expect(details.getByText("EFL Leasing")).toBeVisible();
  await details.getByRole("button", { name: "Zamknij szczegóły pojazdu" }).click();

  // Viewer sees manual vehicle in read-only mode without creation button.
  await logout(page);
  await page.getByLabel("Login").fill("e2e-viewer");
  await page.getByLabel("Hasło").fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się" }).click();
  await page.goto("/#vehicles");
  await expect(page.getByRole("button", { name: "Dodaj pojazd ręcznie" })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Toyota Corolla Ręczna" })).toBeVisible();
});
