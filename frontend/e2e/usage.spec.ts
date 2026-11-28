import { execFileSync } from "node:child_process";
import { expect, test } from "@playwright/test";

function fixture(name: string) {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", name], {
    cwd: "../backend",
    env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
    stdio: "pipe",
  });
}

test("usage compares known and missing history for selected vehicles and sorts rows", async ({ page }) => {
  fixture("reset-case");
  fixture("drivers-case");
  fixture("clear-history-case");
  fixture("import-history-case");
  try {
    await page.goto("/#analytics");
    await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
    await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
    await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
    await expect(page.getByRole("heading", { name: /^Analityka\.?$/, level: 1 })).toBeVisible();
    await page.getByRole("button", { name: "Wczoraj", exact: true }).click();
    const search = page.getByRole("searchbox", { name: "Szukaj pojazdu" });
    const add = page.getByRole("button", { name: "Dodaj do porównania", exact: true });
    await search.fill("Pojazd E2E");
    await page.getByRole("radio", { name: /Pojazd E2E/ }).check();
    await add.click();
    await search.fill("Auto kierowcy 01");
    await page.getByRole("radio", { name: /Auto kierowcy 01/ }).check();
    await add.click();

    const usage = page.getByRole("region", { name: "Tabela wykorzystania" });
    await expect(usage.getByRole("row", { name: /Pojazd E2E/ })).toContainText("12,345 km");
    await expect(usage.getByRole("row", { name: /Auto kierowcy 01/ })).toContainText("Brak raportów");
    await expect(usage.getByRole("row").nth(1)).toContainText("Pojazd E2E");
    await page.getByRole("combobox", { name: "Sortuj porównanie" }).selectOption("name");
    await expect(usage.getByRole("row").nth(1)).toContainText("Auto kierowcy 01");
    await page.getByRole("button", { name: "Usuń z porównania: Auto kierowcy 01" }).click();
    await expect(usage.getByRole("row")).toHaveCount(2);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  } finally {
    fixture("clear-history-case");
    fixture("reset-case");
  }
});
