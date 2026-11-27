import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";
import { expect, test, type Locator, type Page } from "@playwright/test";

// SCRUM-68: full vehicle card on the shared SCRUM-85/SCRUM-70 fields, synthetic data only.

function fixture(command: string) {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", command], {
    cwd: "../backend",
    env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
    stdio: "pipe",
  });
}

async function openCard(page: Page) {
  await page.getByRole("button", { name: "Szczegóły: Pojazd E2E", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading", { name: "Szczegóły pojazdu" })).toBeVisible();
  return dialog;
}

async function pickToday(dialog: Locator, label: string) {
  await dialog.getByRole("button", { name: new RegExp(`^${label}:`) }).click();
  await dialog.page()
    .getByRole("dialog", { name: new RegExp(`Wybierz datę: ${label}`) })
    .locator(".flatpickr-day.today")
    .click();
}

async function axe(page: Page, state: string) {
  const result = await new AxeBuilder({ page })
    .include("dialog[open]")
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(result.violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) })), state).toEqual([]);
}

test.beforeEach(async ({ page }) => {
  fixture("reset-case");
  await page.route("**/*", route =>
    new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#vehicles");
  await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
});

test("SCRUM-68: category, leasing buyout, technical data, validation and persistence", async ({ page }) => {
  let dialog = await openCard(page);
  await expect(dialog.getByText("Kategoria pojazdu", { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Edytuj kartotekę", exact: true }).click();

  // Leasing fields appear only for the leasing category.
  await expect(dialog.getByLabel("Firma leasingowa")).toHaveCount(0);
  await dialog.getByLabel("Kategoria pojazdu").selectOption("Leasing");
  await expect(dialog.getByLabel("Firma leasingowa")).toBeVisible();
  await expect(dialog.getByRole("button", { name: /^Data wykupu:/ })).toBeVisible();

  // Each date has one caption and no nested <label> around the shared DatePicker.
  await expect(dialog.locator("label label")).toHaveCount(0);
  await expect(dialog.getByText("Data wykupu", { exact: true })).toHaveCount(1);
  await axe(page, "edit form");

  await dialog.getByLabel("Firma leasingowa").fill("Syntetyczny Leasing");
  await pickToday(dialog, "Data wykupu");
  await dialog.getByLabel("Pojemność silnika (cm³)").fill("1997");
  await dialog.getByLabel("Moc (kW)").fill("110");
  const grossWeight = dialog.getByLabel("DMC w kg", { exact: true });
  for (const invalid of ["0", "120001"]) {
    await grossWeight.fill(invalid);
    await dialog.getByRole("button", { name: "Zapisz kartotekę", exact: true }).click();
    await expect(grossWeight).toHaveAttribute("aria-invalid", "true");
  }
  await grossWeight.fill("3500");

  await dialog.getByLabel("Masa własna (kg)").fill("4000");
  await dialog.getByLabel("Ładowność (kg)").fill("1300");
  await dialog.getByLabel("Miejsca pasażerskie (bez kierowcy)").fill("2");
  await dialog.getByLabel("Liczba osi").fill("2");

  // The form rejects curb weight above DMC; the draft stays in the form.
  await dialog.getByRole("button", { name: "Zapisz kartotekę", exact: true }).click();
  await expect(dialog.getByText("Masa własna nie może przekraczać DMC.")).toBeVisible();
  await expect(dialog.getByLabel("Masa własna (kg)")).toHaveAttribute("aria-invalid", "true");
  await dialog.getByLabel("Masa własna (kg)").fill("2200");
  await dialog.getByRole("button", { name: "Zapisz kartotekę", exact: true }).click();
  await expect(dialog.getByRole("status").filter({ hasText: "Zapisano kartotekę" })).toBeVisible();

  const card = dialog.locator("dl.vehicle-card-fields");
  await expect(card).toContainText("Leasing");
  await expect(card).toContainText("Syntetyczny Leasing");
  await expect(card).toContainText("110 kW");
  await expect(card).toContainText("Kat. B (DMC)");

  // Changing the category hides, but keeps, the leasing data.
  await dialog.getByRole("button", { name: "Edytuj kartotekę", exact: true }).click();
  await dialog.getByLabel("Kategoria pojazdu").selectOption("Firmowe");
  await expect(dialog.getByLabel("Firma leasingowa")).toHaveCount(0);
  await expect(dialog.getByText(/Dane leasingu pozostają zapisane/)).toBeVisible();
  await dialog.getByRole("button", { name: "Zapisz kartotekę", exact: true }).click();
  await expect(dialog.getByRole("status").filter({ hasText: "Zapisano kartotekę" })).toBeVisible();
  await expect(card).not.toContainText("Syntetyczny Leasing");

  // After a reload the card is read back from the server.
  await page.reload();
  dialog = await openCard(page);
  await expect(dialog.locator("dl.vehicle-card-fields")).toContainText("Firmowe");
  await dialog.getByRole("button", { name: "Edytuj kartotekę", exact: true }).click();
  await dialog.getByLabel("Kategoria pojazdu").selectOption("Leasing");
  await expect(dialog.getByLabel("Firma leasingowa")).toHaveValue("Syntetyczny Leasing");
  await expect(dialog.getByRole("button", { name: /^Data wykupu: \d{2}\.\d{2}\.\d{4}$/ })).toBeVisible();
});
