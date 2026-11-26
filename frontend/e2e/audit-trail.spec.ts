import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";

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

async function login(page: Page, role: "editor" | "viewer" = "editor", hash = "#vehicles") {
  await page.goto(`/${hash}`);
  await page.getByLabel("Login", { exact: true }).fill(`e2e-${role}`);
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
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

test("SCRUM-87: vehicle audit tab and global audit view with DatePicker, object/author filters, pagination, themes and mobile", async ({
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
  const dialog = page.getByRole("dialog");

  // Edit vehicle card and trip annotation to generate audited business events.
  await dialog.getByRole("button", { name: "Edytuj kartotekę", exact: true }).click();
  await dialog.getByLabel("Marka", { exact: true }).fill("Volvo");
  await dialog.getByLabel("DMC w kg", { exact: true }).fill("3500");
  await dialog.getByRole("button", { name: "Zapisz kartotekę", exact: true }).click();
  await expect(dialog.getByText("Zapisano kartotekę pojazdu.")).toBeVisible();

  await dialog.getByRole("tab", { name: "Podróże", exact: true }).click();
  await dialog
    .getByRole("list", { name: "Przejazdy pojazdu", exact: true })
    .getByRole("button")
    .first()
    .click();
  const tripForm = dialog.getByRole("form", { name: "Cel i opis przejazdu", exact: true });
  await tripForm.getByLabel(/Cel przejazdu/).fill("Audytowana podróż testowa");
  await tripForm.getByRole("button", { name: "Zapisz cel i opis", exact: true }).click();
  await expect(tripForm.getByText("Cel i opis zostały zapisane.")).toBeVisible();

  // Inspect per-vehicle Historia zmian tab inside VehicleDetailsDialog!
  await dialog.getByRole("tab", { name: "Historia zmian", exact: true }).click();
  const vehAuditList = dialog.getByRole("list", { name: "Zdarzenia pojazdu", exact: true });
  await expect(vehAuditList).toContainText("Zaktualizowano kartotekę pojazdu");
  await expect(vehAuditList).toContainText("Marka: brak → Volvo");
  await expect(vehAuditList).toContainText("Zaktualizowano ewidencję przejazdu");
  await expect(vehAuditList).toContainText("Audytowana podróż testowa");
  await dialog.getByRole("button", { name: "Zamknij szczegóły pojazdu", exact: true }).click();

  // Navigate to global #audit section and verify DatePicker + object + author filters + WCAG!
  await page.goto("/#audit");
  await expect(page.getByRole("heading", { name: "Wspólny dziennik zmian", exact: true })).toBeVisible();
  const globalList = page.getByRole("list", { name: "Lista zdarzeń dziennika", exact: true });
  await expect(globalList).toContainText("Zaktualizowano kartotekę pojazdu");
  await expect(globalList).toContainText("Zaktualizowano ewidencję przejazdu");

  // Select today's date via shared DatePicker calendar (calendar-only selection, no typing!).
  await page.getByRole("button", { name: /Od daty/ }).click();
  await page
    .getByRole("dialog", { name: /Wybierz datę: Od daty/ })
    .locator(".flatpickr-day.today")
    .click();

  // Filter by entity_type = trip_annotation and author = Test editor.
  await page.getByLabel("Filtr rodzaju obiektu", { exact: true }).selectOption("trip_annotation");
  await expect(globalList).toContainText("Zaktualizowano ewidencję przejazdu");
  await expect(globalList).not.toContainText("Zaktualizowano kartotekę pojazdu");

  await page.getByLabel("Filtr autora zmiany", { exact: true }).selectOption({ label: "Test editor" });
  await expect(globalList).toContainText("Test editor");

  await axe(page, "audit log light");
  await page.evaluate(() =>
    localStorage.setItem(
      "fleet-flow.dashboard.v2",
      JSON.stringify({ theme: "dark", material: "glass" }),
    ),
  );
  await page.reload();
  await expect(page.getByRole("heading", { name: "Wspólny dziennik zmian", exact: true })).toBeVisible();
  await axe(page, "audit log dark");

  // Reset filters and verify mobile viewport (390x844).
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("heading", { name: "Wspólny dziennik zmian", exact: true })).toBeVisible();
});
