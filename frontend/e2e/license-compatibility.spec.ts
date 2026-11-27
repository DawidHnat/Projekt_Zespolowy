import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";

const origin = { Origin: "http://127.0.0.1:54173" };

function fixture(command: string) {
  execFileSync(
    process.env.E2E_PYTHON || "python3",
    ["tests/e2e_server.py", command],
    {
      cwd: "../backend",
      env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
      stdio: "pipe",
    },
  );
}

async function login(page: Page, role: "editor" | "viewer" = "editor", hash = "#drivers") {
  await page.goto(`/${hash}`);
  await page.getByLabel("Login", { exact: true }).fill(`e2e-${role}`);
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
}

async function logout(page: Page) {
  const openMenu = page.getByRole("button", { name: "Otwórz menu" });
  if (await openMenu.isVisible()) await openMenu.click();
  await page.getByRole("button", { name: "Wyloguj się" }).click();
}

async function axe(page: Page, state: string) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(
    result.violations.map((v) => ({
      id: v.id,
      targets: v.nodes.map((n) => n.target),
    })),
    state,
  ).toEqual([]);
}

test.beforeEach(async ({ page }) => {
  fixture("reset-case");
  await page.route("**/*", (route) =>
    new URL(route.request().url()).hostname === "127.0.0.1"
      ? route.continue()
      : route.abort(),
  );
});

test("SCRUM-70: license compatibility states, UI assignment & trip block, widget breakdown, history warning, themes and mobile", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.addInitScript(() => {
    if (!localStorage.getItem("fleet-flow.dashboard.v2")) {
      localStorage.setItem(
        "fleet-flow.dashboard.v2",
        JSON.stringify({ theme: "light", material: "solid" }),
      );
    }
  });
  await login(page, "editor", "#vehicles");
  await page.getByRole("button", { name: "Szczegóły: Pojazd E2E", exact: true }).click();
  const vehicleDialog = page.getByRole("dialog");
  await expect(vehicleDialog.getByText("Niezweryfikowane (brak DMC w kg)")).toBeVisible();
  await vehicleDialog.getByRole("button", { name: "Edytuj kartotekę", exact: true }).click();
  await vehicleDialog.getByLabel("DMC w kg", { exact: true }).fill("12000");
  await vehicleDialog.getByRole("button", { name: "Zapisz kartotekę", exact: true }).click();
  await expect(vehicleDialog.getByText("Kat. C (DMC)", { exact: true })).toBeVisible();
  await vehicleDialog.getByRole("button", { name: "Zamknij szczegóły pojazdu", exact: true }).click();

  // Create a second manual vehicle without DMC to verify unverified ("brak DMC") handling.
  const noDmcRes = await page.request.post("/api/v1/fleet/vehicles", {
    headers: origin,
    data: {
      name: "Auto bez DMC",
      license_plate: "SYN NODMC",
      vehicle_type: "ciężarowy",
    },
  });
  expect(noDmcRes.status()).toBe(201);
  const noDmcVehicle = await noDmcRes.json();

  // Create two drivers via API: Marek (only B) and Piotr (B + C).
  const marekRes = await page.request.post("/api/v1/drivers", {
    headers: origin,
    data: {
      first_name: "Marek",
      last_name: "KategoriaB",
      identifier: "SYN-MAREK-B",
      categories: ["B"],
    },
  });
  expect(marekRes.status()).toBe(201);
  const marek = await marekRes.json();

  const piotrRes = await page.request.post("/api/v1/drivers", {
    headers: origin,
    data: {
      first_name: "Piotr",
      last_name: "KategoriaC",
      identifier: "SYN-PIOTR-C",
      categories: ["B", "C"],
    },
  });
  expect(piotrRes.status()).toBe(201);

  // Assign Auto bez DMC to Marek so Przypisania do sprawdzenia shows 1 unverified (brak DMC).
  const unvAssign = await page.request.post(`/api/v1/drivers/${marek.id}/assignments`, {
    headers: origin,
    data: { version: marek.version, vehicle_id: noDmcVehicle.id },
  });
  expect(unvAssign.status()).toBe(201);

  // Navigate to Kierowcy and inspect Przypisania do sprawdzenia widget + WCAG in light & dark themes.
  await page.goto("/#drivers");
  await expect(page.getByRole("heading", { name: "Kartoteka kierowców", exact: true })).toBeVisible();
  const checksWidget = page.getByRole("region", { name: "Przypisania do sprawdzenia", exact: true });
  await expect(checksWidget).toContainText("1");
  await expect(checksWidget).toContainText("brak DMC: 1");

  await axe(page, "drivers compatibility light");
  await page.evaluate(() =>
    localStorage.setItem(
      "fleet-flow.dashboard.v2",
      JSON.stringify({ theme: "dark", material: "glass" }),
    ),
  );
  await page.reload();
  await expect(page.getByRole("heading", { name: "Kartoteka kierowców", exact: true })).toBeVisible();
  await axe(page, "drivers compatibility dark");

  // Filter via widget button "Pokaż osoby" -> shows only Marek with attention status.
  await checksWidget.getByRole("button", { name: "Pokaż osoby", exact: true }).click();
  await expect(page.getByRole("button", { name: "Marek KategoriaB", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Piotr KategoriaC", exact: true })).toHaveCount(0);

  // Open Marek's details and attempt to assign 12 000 kg Pojazd E2E -> UI blocks with LICENSE_INCOMPATIBLE!
  await page.getByRole("button", { name: "Marek KategoriaB", exact: true }).click();
  const driverDialog = page.getByRole("dialog");
  await driverDialog.getByRole("button", { name: "Przypisz pojazd", exact: true }).click();
  await driverDialog.getByRole("radio", { name: /Pojazd E2E/ }).check();
  await driverDialog.getByRole("button", { name: "Zapisz przypisanie", exact: true }).click();
  await expect(driverDialog.getByRole("alert")).toContainText(
    "Przypisanie z potwierdzoną niezgodnością kategorii jest zablokowane.",
  );
  await driverDialog.getByRole("button", { name: "Anuluj przypisanie", exact: true }).click();
  await driverDialog.getByRole("button", { name: "Zamknij panel kierowcy", exact: true }).click();

  // Reset compatibility filter, open Piotr (B, C), assign Pojazd E2E (Zgodne), close assignment, remove C -> check historical warning!
  await page
    .getByRole("combobox", { name: "Filtr zgodności uprawnień", exact: true })
    .selectOption("");
  await page.getByRole("button", { name: "Piotr KategoriaC", exact: true }).click();
  await driverDialog.getByRole("button", { name: "Przypisz pojazd", exact: true }).click();
  await driverDialog.getByRole("radio", { name: /Pojazd E2E/ }).check();
  await driverDialog.getByRole("button", { name: "Zapisz przypisanie", exact: true }).click();
  await expect(driverDialog.getByText(/Zgodne \(wymagana kat\. C\)/)).toBeVisible();

  await driverDialog.getByRole("button", { name: "Zakończ przypisanie", exact: true }).click();
  await expect(
    driverDialog.getByText("Zakończono przypisanie. Historia została zachowana.", { exact: true }),
  ).toBeVisible();

  // Remove C from Piotr's categories -> closed historical assignment stays intact with explicit warning.
  await driverDialog.getByRole("button", { name: "Edytuj kierowcę", exact: true }).click();
  await driverDialog.getByRole("checkbox", { name: "C", exact: true }).uncheck();
  await driverDialog.getByRole("button", { name: "Zapisz kierowcę", exact: true }).click();
  await driverDialog.getByLabel("Stan przypisań", { exact: true }).selectOption("history");
  await expect(driverDialog.getByText(/Niezgodne \(wymagana kat\. C\)/)).toBeVisible();
  await expect(
    driverDialog.getByText(
      "Aktualne prawo jazdy i kartoteka pojazdu nie potwierdzają uprawnień w dacie historycznego przypisania.",
    ),
  ).toBeVisible();
  await driverDialog.getByRole("button", { name: "Zamknij panel kierowcy", exact: true }).click();

  // Trip logbook (VehicleDetailsDialog -> Podróże): selecting Marek (B) on 12t Pojazd E2E trip is blocked!
  await page.goto("/#vehicles");
  await page.getByRole("button", { name: "Szczegóły: Pojazd E2E", exact: true }).click();
  await vehicleDialog.getByRole("tab", { name: "Podróże", exact: true }).click();
  await vehicleDialog
    .getByRole("list", { name: "Przejazdy pojazdu", exact: true })
    .getByRole("button")
    .first()
    .click();
  const tripForm = vehicleDialog.getByRole("form", { name: "Cel i opis przejazdu", exact: true });
  await tripForm.getByLabel(/Kierowca w ewidencji/).selectOption({ label: "Marek KategoriaB" });
  await tripForm.getByRole("button", { name: "Zapisz cel i opis", exact: true }).click();
  await expect(tripForm.getByRole("alert")).toContainText(
    "Wybrany kierowca nie posiada wymaganej kategorii prawa jazdy dla tego pojazdu.",
  );
  await tripForm.getByRole("button", { name: "Anuluj zmiany", exact: true }).click();
  await vehicleDialog.getByRole("button", { name: "Zamknij szczegóły pojazdu", exact: true }).click();

  // Mobile viewport (390x844) + viewer read-only verification.
  await page.setViewportSize({ width: 390, height: 844 });
  await logout(page);
  await page.getByLabel("Login", { exact: true }).fill("e2e-viewer");
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await page.goto("/#drivers");
  await expect(page.getByRole("heading", { name: "Kartoteka kierowców", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Dodaj kierowcę", exact: true })).toHaveCount(0);
});
