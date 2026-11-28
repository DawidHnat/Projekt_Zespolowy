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

test.afterEach(() => {
  resetDatabase();
});

test.afterEach(() => {
  resetDatabase();
});

test("SCRUM-88: editor archives and restores vehicle while preserving trip history and blocking viewer", async ({ page }) => {
  await page.goto("/#vehicles");
  await page.getByLabel("Login").fill("e2e-editor");
  await page.getByLabel("Hasło").fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się" }).click();

  await expect(page.getByRole("heading", { name: "Pojazd E2E" })).toBeVisible();
  await page.getByRole("button", { name: "Szczegóły: Pojazd E2E" }).click();

  const dialog = page.getByRole("dialog", { name: "Pojazd E2E" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Archiwizuj pojazd" }).click();
  await dialog.getByLabel("Powód archiwizacji (opcjonalnie)").fill("Wycofany po zakończeniu umowy");
  await dialog.getByRole("button", { name: "Potwierdź archiwizację" }).click();

  await expect(dialog.getByText("Pojazd w archiwum")).toBeVisible();
  await expect(dialog.getByText("Powód: Wycofany po zakończeniu umowy")).toBeVisible();

  await dialog.getByRole("tab", { name: "Podróże" }).click();
  await expect(dialog.getByText("12,5 km")).toBeVisible();
  await dialog.getByRole("button", { name: "Zamknij szczegóły pojazdu" }).click();

  await expect(page.getByText("Brak pasujących pojazdów")).toBeVisible();
  await page.getByLabel("Archiwum pojazdów").selectOption("archived");
  await expect(page.getByRole("heading", { name: "Pojazd E2E" })).toBeVisible();

  await logout(page);
  await page.getByLabel("Login").fill("e2e-viewer");
  await page.getByLabel("Hasło").fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się" }).click();
  await page.goto("/#vehicles");
  await page.getByLabel("Archiwum pojazdów").selectOption("archived");
  await page.getByRole("button", { name: "Szczegóły: Pojazd E2E" }).click();
  await expect(dialog.getByText("Pojazd w archiwum")).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Przywróć pojazd" })).toHaveCount(0);
  await dialog.getByRole("button", { name: "Zamknij szczegóły pojazdu" }).click();
  await page.getByLabel("Archiwum pojazdów").selectOption("active");

  await logout(page);
  await page.getByLabel("Login").fill("e2e-editor");
  await page.getByLabel("Hasło").fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się" }).click();
  await page.goto("/#vehicles");
  await page.getByLabel("Archiwum pojazdów").selectOption("archived");
  await page.getByRole("button", { name: "Szczegóły: Pojazd E2E" }).click();
  await dialog.getByRole("button", { name: "Przywróć pojazd" }).click();
  await expect(dialog.getByText("Pojazd został przywrócony do bieżącej floty.")).toBeVisible();
  await dialog.getByRole("button", { name: "Zamknij szczegóły pojazdu" }).click();

  await page.getByLabel("Archiwum pojazdów").selectOption("active");
  await expect(page.getByRole("heading", { name: "Pojazd E2E" })).toBeVisible();
});
