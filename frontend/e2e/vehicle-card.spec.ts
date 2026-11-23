import { expect, test, type Page } from "@playwright/test";

const origin = { Origin: "http://127.0.0.1:54173" };
const vehiclePath = "/api/v1/fleet/vehicles/11111111-1111-4111-8111-111111111111";

async function vehicleCard(page: Page, role: "editor" | "viewer") {
  await page.goto("/#vehicles");
  await page.getByLabel("Login", { exact: true }).fill(`e2e-${role}`);
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading", { name: "Szczegóły pojazdu" })).toBeVisible();
  return dialog;
}

test("vehicle card keeps a dirty field on conflict and reloads the other fields", async ({ page }) => {
  const dialog = await vehicleCard(page, "editor");
  const before = await (await page.request.get(vehiclePath)).json();
  try {
    await dialog.getByRole("button", { name: "Edytuj kartotekę" }).click();
    await dialog.getByLabel("Marka", { exact: true }).fill("Marka ze szkicu");
    const concurrent = await page.request.patch(vehiclePath, {
      headers: origin,
      data: { card_version: before.card_version, model: "Model z drugiej sesji" },
    });
    expect(concurrent.status()).toBe(200);
    await dialog.getByRole("button", { name: "Zapisz kartotekę" }).click();
    await expect(dialog.getByRole("alert")).toHaveText(/szkic pozostał/);
    await expect(dialog.getByLabel("Marka", { exact: true })).toHaveValue("Marka ze szkicu");
    await dialog.getByRole("button", { name: "Wczytaj bieżącą wersję" }).click();
    await expect(dialog.getByLabel("Model", { exact: true })).toHaveValue("Model z drugiej sesji");
    await expect(dialog.getByLabel("Marka", { exact: true })).toHaveValue("Marka ze szkicu");
    await dialog.getByRole("button", { name: "Zapisz kartotekę" }).click();
    await expect(dialog.getByRole("status").filter({ hasText: /Zapisano kartotekę/ })).toBeVisible();
    const after = await (await page.request.get(vehiclePath)).json();
    expect(after.card_version).toBe(before.card_version + 2);
    expect(after.make).toBe("Marka ze szkicu");
    expect(after.model).toBe("Model z drugiej sesji");
  } finally {
    const current = await (await page.request.get(vehiclePath)).json();
    const reset = await page.request.patch(vehiclePath, {
      headers: origin,
      data: { card_version: current.card_version, make: before.make, model: before.model },
    });
    expect(reset.status()).toBe(200);
  }
});

test("viewer sees the vehicle card without editing controls", async ({ page }) => {
  const dialog = await vehicleCard(page, "viewer");
  await expect(dialog.getByText("Numer rejestracyjny", { exact: true })).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Edytuj kartotekę" })).toHaveCount(0);
});
