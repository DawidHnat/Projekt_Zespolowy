import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";

function fixture(...args: string[]) {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", ...args], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" }, stdio: "pipe",
  });
}
async function login(page: Page, role = "editor") {
  await page.goto("/#alerts");
  await page.getByLabel("Login", { exact: true }).fill(`e2e-${role}`);
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.getByRole("heading", { name: /^Alerty\.?$/, level: 1 })).toBeVisible();
}
const rows = (page: Page) => page.getByRole("list", { name: "Alerty dziennego dystansu", exact: true });
test.beforeEach(async ({ page }) => {
  fixture("reset-case");
  await page.route("**/*", route => new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
});

test("alerts persist private viewer receipts and filter unread results", async ({ page }) => {
  fixture("alerts-case", "single");
  await login(page, "viewer");
  await expect(rows(page).getByText("Pojazd E2E · TEST E2E", { exact: true })).toBeVisible();
  await expect(rows(page).getByText("125,5 km", { exact: true })).toBeVisible();
  await expect(rows(page).getByText(/Niepełne dane/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Dodaj regułę", exact: true })).toHaveCount(0);
  await page.getByLabel("Stan odczytu alertów", { exact: true }).selectOption("unread");
  await rows(page).getByRole("button", { name: "Oznacz jako przeczytany", exact: true }).click();
  await expect(page.getByText("Oznaczono jako przeczytany.", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Brak alertów w tym widoku", exact: true })).toBeVisible();
  await page.reload();
  await expect(rows(page).getByText("Przeczytany", { exact: true })).toBeVisible();
  expect((await (await page.request.get("/api/v1/analytics/alerts")).json()).items[0].read_at).toBeTruthy();
  await page.context().clearCookies();
  await page.reload();
  await login(page);
  await expect(rows(page).getByText("Nieprzeczytany", { exact: true })).toBeVisible();
  expect((await (await page.request.get("/api/v1/analytics/alerts")).json()).items[0].read_at).toBeNull();
});

test("alerts paginate on the server and retain receipt errors until retry", async ({ page }) => {
  fixture("alerts-case", "pages");
  await login(page);
  await expect(rows(page).getByRole("listitem")).toHaveCount(25);
  await page.getByRole("button", { name: "Następna strona: Alerty", exact: true }).click();
  await expect(rows(page).getByRole("listitem")).toHaveCount(1);
  await expect(page.getByRole("navigation", { name: "Strony: Alerty", exact: true })).toContainText("26–26 z 26");
  const pattern = "**/api/v1/analytics/alerts/*/receipt";
  await page.route(pattern, route => route.fulfill({ status: 503, contentType: "application/json", body: "{}" }));
  await rows(page).getByRole("button", { name: "Oznacz jako przeczytany", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Nie udało się potwierdzić zapisu" })).toBeVisible();
  await expect(rows(page).getByText("Nieprzeczytany", { exact: true })).toBeVisible();
  await page.unroute(pattern);
  await rows(page).getByRole("button", { name: "Oznacz jako przeczytany", exact: true }).click();
  await expect(rows(page).getByText("Przeczytany", { exact: true })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await page.getByLabel("Stan odczytu alertów", { exact: true }).selectOption("read");
  await expect(rows(page).getByRole("listitem")).toHaveCount(1);
});

test("alerts empty state and rule forms save scoped rules and retain failed drafts", async ({ page }) => {
  await login(page);
  await expect(page.getByRole("heading", { name: "Brak alertów w tym widoku", exact: true })).toBeVisible();
  const add = page.getByRole("button", { name: "Dodaj regułę", exact: true });
  await add.focus(); await page.keyboard.press("Enter");
  const form = page.getByRole("form", { name: "Nowa reguła dystansu", exact: true });
  await expect(form.getByLabel("Próg dziennego dystansu (km)", { exact: true })).toBeFocused();
  await form.getByLabel("Próg dziennego dystansu (km)", { exact: true }).fill("12.5");
  await form.getByRole("combobox", { name: "Zakres reguły", exact: true }).selectOption("vehicle");
  await form.getByLabel("Szukaj pojazdu", { exact: true }).fill("TEST E2E");
  await form.getByRole("radio", { name: "Pojazd E2E · TEST E2E", exact: true }).check();
  const pattern = "**/api/v1/analytics/rules";
  await page.route(pattern, route => route.request().method() === "POST" ? route.fulfill({ status: 503, contentType: "application/json", body: "{}" }) : route.continue());
  await form.getByRole("button", { name: "Zapisz regułę", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("Nie zapisano reguły");
  await expect(form.getByLabel("Próg dziennego dystansu (km)", { exact: true })).toHaveValue("12.5");
  await page.unroute(pattern);
  await form.getByRole("button", { name: "Zapisz regułę", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Reguła została zapisana" })).toBeVisible();
  await expect(add).toBeFocused();
  let rules = (await (await page.request.get("/api/v1/analytics/rules")).json()).items;
  expect(rules[0].vehicle_id).toBe("11111111-1111-4111-8111-111111111111");
  expect(rules[0].threshold_km).toBe(12.5);
  await page.getByRole("button", { name: "Edytuj regułę", exact: true }).click();
  const edit = page.getByRole("form", { name: "Edycja reguły dystansu", exact: true });
  await edit.getByLabel("Reguła włączona", { exact: true }).uncheck();
  await edit.getByRole("button", { name: "Zapisz regułę", exact: true }).click();
  await expect(edit).toHaveCount(0);
  expect((await (await page.request.get("/api/v1/analytics/rules")).json()).items[0].active).toBe(false);
  await add.click();
  await page.getByLabel("Próg dziennego dystansu (km)", { exact: true }).fill("250");
  await page.getByRole("button", { name: "Zapisz regułę", exact: true }).click();
  await expect(page.getByRole("form")).toHaveCount(0);
  rules = (await (await page.request.get("/api/v1/analytics/rules")).json()).items;
  expect(rules.some((rule: { vehicle_id: string | null; threshold_km: number }) => rule.vehicle_id === null && rule.threshold_km === 250)).toBe(true);
});

for (const theme of ["light", "dark"]) {
  test(`axe alerts and rule editor ${theme}`, async ({ page }) => {
    fixture("alerts-case", "single");
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.addInitScript(value => localStorage.setItem("fleet-flow.dashboard.v2", JSON.stringify({ theme: value })), theme);
    await login(page);
    await expect(rows(page).getByRole("listitem")).toHaveCount(1);
    const accessible = async () => expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze()).violations).toEqual([]);
    await accessible();
    await page.getByRole("button", { name: "Dodaj regułę", exact: true }).click();
    await page.getByRole("combobox", { name: "Zakres reguły", exact: true }).selectOption("vehicle");
    await expect(page.getByRole("radio", { name: "Pojazd E2E · TEST E2E", exact: true })).toBeVisible();
    await accessible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`alerts-${theme}.png`), fullPage: true });
    await page.getByRole("button", { name: "Anuluj regułę", exact: true }).click();
    await expect(page.getByRole("button", { name: "Dodaj regułę", exact: true })).toBeFocused();
  });
}
