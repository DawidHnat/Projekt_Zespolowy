import { execFileSync } from "node:child_process";
import { expect, test } from "@playwright/test";

function fixture(action: "import" | "clear" | "reset") {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", action === "reset" ? "reset-case" : `${action}-history-case`], {
    cwd: "../backend",
    env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
    stdio: "pipe",
  });
}
test("persistent history displays imported trips and stops and retains annotations across reimport", async ({ page }) => {
  fixture("reset");
  fixture("clear");
  fixture("import");
  try {
    await page.goto("/#vehicles");
    await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
    await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
    await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
    const findHistory = async () => {
      await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
      const dialog = page.getByRole("dialog");
      await dialog.getByRole("tab", { name: "Podróże", exact: true }).click();
      await dialog.getByRole("button", { name: "Wczoraj", exact: true }).click();
      await dialog.getByRole("list", { name: "Przejazdy pojazdu", exact: true }).getByRole("button").first().click();
      return dialog;
    };
    let history = await findHistory();
    await expect(history.getByText(/1 z 1 dni/)).toBeVisible();
    await expect(history.getByText(/Początek E2E/)).toBeVisible();
    await expect(history.getByText(/Brak zapisanego śladu/)).toBeVisible();
    await expect(history.getByRole("list", { name: "Postoje pojazdu", exact: true })).toContainText("8 min · Postój E2E");
    await history.getByLabel(/Cel przejazdu/).fill("Serwis E2E");
    await history.getByLabel(/Opis przejazdu/).fill("Opis syntetyczny");
    await history.getByRole("button", { name: "Zapisz cel i opis" }).click();
    await expect(history.getByText(/Cel i opis zostały zapisane/)).toBeVisible();

    fixture("import");
    await page.reload();
    history = await findHistory();
    const trips = history.getByRole("list", { name: "Przejazdy pojazdu", exact: true });
    await expect(trips.getByRole("button")).toHaveCount(1);
    await expect(history.getByLabel(/Cel przejazdu/)).toHaveValue("Serwis E2E");
    await expect(history.getByLabel(/Opis przejazdu/)).toHaveValue("Opis syntetyczny");
    await expect(history.getByText(/Test editor/)).toBeVisible();
  } finally {
    fixture("clear");
  }
});
