import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";

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
async function login(page: Page, role = "editor") {
  await page.goto("/#drivers");
  await page.getByLabel("Login", { exact: true }).fill(`e2e-${role}`);
  await page
    .getByLabel("Hasło", { exact: true })
    .fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Kartoteka kierowców", exact: true }),
  ).toBeVisible();
}
async function createPerson(page: Page, identifier = "SYN-CREATE") {
  await page
    .getByRole("button", { name: "Dodaj kierowcę", exact: true })
    .click();
  const form = page.getByRole("form", { name: "Nowy kierowca", exact: true });
  await expect(form.getByLabel("Imię", { exact: true })).toBeFocused();
  await form.getByLabel("Imię", { exact: true }).fill("Zofia");
  await form.getByLabel("Nazwisko", { exact: true }).fill("Żółć");
  await form
    .getByLabel("Identyfikator kierowcy", { exact: true })
    .fill(identifier);
  return form;
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

test("drivers: create, inline validation, failed save retry, duplicate identifier and durable profile", async ({
  page,
}) => {
  await login(page);
  await expect(
    page.getByText("Brak kierowców w tym widoku", { exact: true }),
  ).toBeVisible();
  const form = await createPerson(page);
  await form.getByLabel(/Telefon/).fill("++48 123456789");
  await form
    .getByRole("button", { name: "Zapisz kierowcę", exact: true })
    .click();
  await expect(form.getByLabel(/Telefon/)).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  await expect(form.getByLabel(/Telefon/)).toBeFocused();
  await form.getByLabel(/Telefon/).fill("+48 123 456 789");
  await form.getByLabel(/E-mail/).fill("zofia@example.com");
  await form.getByRole("checkbox", { name: "B", exact: true }).check();
  await page.route("**/api/v1/drivers", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ error: { code: "UNAVAILABLE" } }),
    }),
  );
  await form
    .getByRole("button", { name: "Zapisz kierowcę", exact: true })
    .click();
  await expect(form.getByRole("alert")).toBeVisible();
  await expect(form.getByLabel("Nazwisko", { exact: true })).toHaveValue(
    "Żółć",
  );
  await page.unroute("**/api/v1/drivers");
  await form
    .getByRole("button", { name: "Zapisz kierowcę", exact: true })
    .click();
  const dialog = page.getByRole("dialog");
  await expect(
    dialog.getByText("Dane kierowcy zostały zapisane.", { exact: true }),
  ).toBeVisible();
  await expect(
    dialog.getByRole("heading", { name: "Zofia Żółć", exact: true }),
  ).toBeFocused();
  await dialog
    .getByRole("button", { name: "Zamknij panel kierowcy", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Dodaj kierowcę", exact: true }),
  ).toBeFocused();
  const duplicate = await createPerson(page);
  await duplicate
    .getByRole("button", { name: "Zapisz kierowcę", exact: true })
    .click();
  await expect(
    duplicate.getByLabel("Identyfikator kierowcy", { exact: true }),
  ).toHaveAttribute("aria-invalid", "true");
  await expect(duplicate.getByLabel("Imię", { exact: true })).toHaveValue(
    "Zofia",
  );
  await duplicate
    .getByRole("button", { name: "Anuluj dane kierowcy", exact: true })
    .click();
  await page.reload();
  await page.getByRole("button", { name: "Zofia Żółć", exact: true }).click();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("link", { name: "zofia@example.com", exact: true }),
  ).toBeVisible();
});

test("drivers: conflict preserves draft, unsaved Escape and focus return", async ({
  page,
}) => {
  fixture("drivers-case");
  await login(page);
  await page.getByRole("button", { name: "Anna Test00", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog
    .getByRole("button", { name: "Edytuj kierowcę", exact: true })
    .click();
  const form = dialog.getByRole("form", {
    name: "Edycja kierowcy",
    exact: true,
  });
  await form.getByLabel("Nazwisko", { exact: true }).fill("Mój szkic");
  const list = await (
    await page.request.post("/api/v1/drivers/search", {
      headers: origin,
      data: { q: "SYN-DIR-00" },
    })
  ).json();
  const person = list.items[0];
  expect(
    (
      await page.request.patch(`/api/v1/drivers/${person.id}`, {
        headers: origin,
        data: { version: person.version, last_name: "Równolegle" },
      })
    ).ok(),
  ).toBeTruthy();
  await form
    .getByRole("button", { name: "Zapisz kierowcę", exact: true })
    .click();
  await expect(
    form.getByRole("region", { name: "Konflikt danych kierowcy" }),
  ).toBeVisible();
  await expect(form.getByLabel("Nazwisko", { exact: true })).toHaveValue(
    "Mój szkic",
  );
  page.once("dialog", (prompt) => prompt.dismiss());
  await page.keyboard.press("Escape");
  await expect(form.getByLabel("Nazwisko", { exact: true })).toHaveValue(
    "Mój szkic",
  );
  await form
    .getByRole("button", { name: "Sprawdź bieżące dane kierowcy", exact: true })
    .click();
  await expect(
    form.getByText("Anna Równolegle", { exact: false }).first(),
  ).toBeVisible();
  await form
    .getByRole("button", { name: "Kontynuuj z moim formularzem", exact: true })
    .click();
  await form
    .getByRole("button", { name: "Zapisz kierowcę", exact: true })
    .click();
  await expect(
    dialog.getByRole("heading", { name: "Anna Mój szkic", exact: true }),
  ).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Anna Mój szkic", exact: true }),
  ).toBeFocused();
});

test("drivers: full many-vehicle count, assignment pages, close history, add and deactivate", async ({
  page,
}) => {
  fixture("drivers-case");
  await login(page);
  await page
    .getByRole("button", {
      name: "+19 poj. — pozostałe pojazdy: Anna Test00",
      exact: true,
    })
    .click();
  const dialog = page.getByRole("dialog");
  await expect(
    dialog.getByText("Bieżące przypisania: 20.", { exact: false }),
  ).toBeVisible();
  await expect(dialog.locator(".driver-assignment-list li")).toHaveCount(10);
  await dialog
    .getByRole("button", {
      name: "Następna strona: Przypisania kierowcy",
      exact: true,
    })
    .click();
  await expect(
    dialog.getByRole("navigation", { name: "Strony: Przypisania kierowcy" }),
  ).toContainText("11–20 z 20");
  await dialog
    .getByRole("button", { name: "Zakończ przypisanie", exact: true })
    .first()
    .click();
  await expect(
    dialog.getByText("Zakończono przypisanie. Historia została zachowana.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    dialog.getByText("Bieżące przypisania: 19.", { exact: false }),
  ).toBeVisible();
  await dialog
    .getByRole("combobox", { name: "Stan przypisań", exact: true })
    .selectOption("history");
  await expect(dialog.locator(".driver-assignment-list li")).toHaveCount(1);
  const closedName = await dialog
    .locator(".driver-assignment-list li strong")
    .textContent();
  await dialog
    .getByRole("button", { name: "Przypisz pojazd", exact: true })
    .click();
  await dialog.getByRole("radio", { name: closedName!, exact: true }).check();
  await dialog
    .getByRole("button", { name: "Zapisz przypisanie", exact: true })
    .click();
  await expect(
    dialog.getByText("Pojazd został przypisany.", { exact: true }),
  ).toBeVisible();
  await expect(
    dialog.getByText("Bieżące przypisania: 20.", { exact: false }),
  ).toBeVisible();
  await dialog
    .getByRole("button", { name: "Edytuj kierowcę", exact: true })
    .click();
  await dialog
    .getByRole("checkbox", { name: "Kierowca aktywny", exact: true })
    .uncheck();
  await dialog
    .getByRole("button", { name: "Zapisz kierowcę", exact: true })
    .click();
  await expect(
    dialog.getByText("Bieżące przypisania: 0.", { exact: false }),
  ).toBeVisible();
  await dialog
    .getByRole("combobox", { name: "Stan przypisań", exact: true })
    .selectOption("history");
  await expect(
    dialog.getByRole("navigation", { name: "Strony: Przypisania kierowcy" }),
  ).toContainText("z 21");
});

test("drivers: contact and vehicle searches, summary scope, pagination and viewer policy", async ({
  page,
}) => {
  fixture("drivers-case");
  await login(page, "viewer");
  await expect(
    page.getByRole("button", { name: "Dodaj kierowcę", exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("navigation", { name: "Strony: Kierowcy" }),
  ).toContainText("1–25 z 26");
  await page
    .getByRole("button", { name: "Następna strona: Kierowcy", exact: true })
    .click();
  await expect(
    page.getByRole("navigation", { name: "Strony: Kierowcy" }),
  ).toContainText("26–26 z 26");
  await page
    .getByRole("searchbox", { name: "Szukaj kierowcy", exact: true })
    .fill("synthetic-dir-00@example.com");
  await expect(
    page.getByRole("navigation", { name: "Strony: Kierowcy" }),
  ).toContainText("1–1 z 1");
  await expect(
    page.getByRole("button", { name: "Anna Test00", exact: true }),
  ).toBeVisible();
  expect(page.url()).not.toContain("example.com");
  await page
    .getByRole("searchbox", { name: "Szukaj kierowcy", exact: true })
    .fill("Pojazd E2E");
  await expect(
    page.getByRole("navigation", { name: "Strony: Kierowcy" }),
  ).toContainText("1–2 z 2");
  await page.getByRole("button", { name: "Anna Test00", exact: true }).click();
  await expect(
    page
      .getByRole("dialog")
      .getByRole("button", { name: "Edytuj kierowcę", exact: true }),
  ).toHaveCount(0);
  await expect(
    page
      .getByRole("dialog")
      .getByRole("button", { name: "Przypisz pojazd", exact: true }),
  ).toHaveCount(0);
  expect(
    (
      await page.request.post("/api/v1/drivers", {
        headers: origin,
        data: {
          first_name: "Nie",
          last_name: "Wolno",
          identifier: "forbidden",
        },
      })
    ).status(),
  ).toBe(403);
  await page.keyboard.press("Escape");
  await page
    .getByRole("searchbox", { name: "Szukaj kierowcy", exact: true })
    .fill("");
  await page
    .getByRole("combobox", { name: "Filtr kategorii kierowców", exact: true })
    .selectOption("missing");
  await page
    .getByRole("combobox", { name: "Aktywność kierowców", exact: true })
    .selectOption("active");
  await expect(
    page.getByRole("navigation", { name: "Strony: Kierowcy" }),
  ).toContainText("1–23 z 23");
  await expect(
    page.getByText("Ocena kategorii nie jest jeszcze dostępna.", {
      exact: false,
    }),
  ).toBeVisible();
  const stored = await page.evaluate(() => JSON.stringify(localStorage));
  expect(stored).not.toContain("synthetic-dir-");
});

for (const theme of ["light", "dark"]) {
  test(`drivers: axe, keyboard, list/cards and layout draft isolation ${theme}`, async ({
    page,
  }) => {
    fixture("drivers-case");
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.addInitScript(
      (value) =>
        localStorage.setItem(
          "fleet-flow.dashboard.v2",
          JSON.stringify({
            theme: value,
            material: value === "light" ? "solid" : "glass",
          }),
        ),
      theme,
    );
    await login(page);
    await expect(
      page.getByRole("button", { name: "Anna Test00", exact: true }),
    ).toBeVisible();
    await axe(page, "driver list");
    const otherPrefs = await page.evaluate(() =>
      localStorage.getItem("fleet-flow.dashboard.v2"),
    );
    await page.getByRole("button", { name: "Kafelki", exact: true }).click();
    const first = page.getByRole("article", {
      name: "Kierowca: Anna Test00",
      exact: true,
    });
    await expect(first).toBeVisible();
    await axe(page, "driver cards");
    await page
      .getByRole("button", { name: "Edytuj układ", exact: true })
      .click();
    await first
      .getByRole("button", {
        name: "Zmień rozmiar kierowcy: Anna Test00",
        exact: true,
      })
      .press("ArrowRight");
    await first.getByRole("button", { name: "Niżej", exact: true }).click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await page.getByRole("button", { name: "Anuluj", exact: true }).click();
    await expect(page.getByRole("article").first()).toHaveAccessibleName(
      "Kierowca: Anna Test00",
    );
    await page
      .getByRole("button", { name: "Edytuj układ", exact: true })
      .click();
    await page
      .getByRole("checkbox", { name: "Aktywni kierowcy", exact: true })
      .uncheck();
    await first.getByRole("button", { name: "Niżej", exact: true }).click();
    await page
      .getByRole("button", { name: "Zapisz układ", exact: true })
      .click();
    await expect(page.getByRole("article").first()).toHaveAccessibleName(
      "Kierowca: Bartosz Test01",
    );
    await page.reload();
    await page
      .getByRole("combobox", { name: "Kolejność kierowców", exact: true })
      .selectOption("custom");
    await expect(page.getByRole("article").first()).toHaveAccessibleName(
      "Kierowca: Bartosz Test01",
    );
    expect(
      await page.evaluate(() =>
        localStorage.getItem("fleet-flow.dashboard.v2"),
      ),
    ).toBe(otherPrefs);
    const open = page.getByRole("button", { name: "Anna Test00", exact: true });
    await open.focus();
    await open.press("Enter");
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await axe(page, "driver profile");
    await dialog
      .getByRole("button", { name: "Zamknij panel kierowcy", exact: true })
      .focus();
    await page.keyboard.press("Shift+Tab");
    expect(
      await page.evaluate(() =>
        Boolean(
          document
            .querySelector("dialog[open]")
            ?.contains(document.activeElement),
        ),
      ),
    ).toBeTruthy();
    await page.keyboard.press("Escape");
    await expect(open).toBeFocused();
    await page.screenshot({
      path: test.info().outputPath(`drivers-${theme}.png`),
    });
  });
}

test("drivers: selected resize, hide-all recovery and account/session isolation", async ({
  page,
}) => {
  fixture("drivers-case");
  await login(page);
  await page.getByRole("button", { name: "Kafelki", exact: true }).click();
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  const first = page.getByRole("article", {
    name: "Kierowca: Anna Test00",
    exact: true,
  });
  const other = page.getByRole("article", {
    name: "Kierowca: Bartosz Test01",
    exact: true,
  });
  await first
    .getByRole("button", {
      name: "Rozmiar kafelka kierowcy: Anna Test00",
      exact: true,
    })
    .click();
  const width = page.getByRole("slider", {
    name: "Szerokość kafelka kierowcy",
    exact: true,
  });
  await expect(width).toBeFocused();
  await width.press("ArrowRight");
  await expect(first).toHaveAttribute("style", /width: 330px/);
  await expect(other).toHaveAttribute("style", /width: 320px/);
  if (test.info().project.name === "desktop") {
    const handle = first.getByRole("button", {
      name: "Zmień rozmiar kierowcy: Anna Test00",
      exact: true,
    });
    await handle.scrollIntoViewIfNeeded();
    const box = await handle.boundingBox();
    if (!box) throw new Error("Missing driver resize handle");
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width / 2 + 40, box.y + box.height / 2, {
      steps: 4,
    });
    await page.mouse.up();
    await expect(first).toHaveAttribute("style", /width: 370px/);
  }
  await expect(page.getByRole("dialog")).toHaveCount(0);
  for (const name of [
    "Aktywni kierowcy",
    "Bez pojazdu",
    "Brak wpisanych kategorii",
    "Przypisania do sprawdzenia",
  ])
    await page.getByRole("checkbox", { name, exact: true }).uncheck();
  await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
  await expect(
    page.getByText("Moduły przeglądu są ukryte.", { exact: false }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByText("Moduły przeglądu są ukryte.", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  await page
    .getByRole("button", { name: "Przywróć układ tego widoku", exact: true })
    .click();
  await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Aktywni kierowcy", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Kafelki", exact: true }).click();
  await page.getByRole("button", { name: "Anna Test00", exact: true }).click();
  await page
    .getByRole("button", { name: "Edytuj kierowcę", exact: true })
    .click();
  await page
    .getByRole("form", { name: "Edycja kierowcy", exact: true })
    .getByLabel("Nazwisko", { exact: true })
    .fill("Prywatny szkic");
  expect(
    (await page.request.post("/api/v1/auth/logout", { headers: origin })).ok(),
  ).toBeTruthy();
  await page
    .getByRole("button", { name: "Zapisz kierowcę", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Zaloguj się", exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await login(page, "viewer");
  await expect(
    page.getByRole("button", { name: "Lista", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  expect(await page.evaluate(() => JSON.stringify(localStorage))).not.toContain(
    "Prywatny szkic",
  );
});
