import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";

const origin = "http://127.0.0.1:54173";
const password = "synthetic-e2e-password";
const replacement = "synthetic-profile-replacement";

async function login(page: Page) {
  await page.goto("/#vehicles");
  await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
  await page.getByLabel("Hasło", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.getByRole("heading", { name: /^Pojazdy\.?$/, level: 1 })).toBeVisible();
}

async function privateDraft(page: Page) {
  await page.goto("/#vehicles");
  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("tab", { name: "Podróże", exact: true }).click();
  await dialog.getByRole("list", { name: "Przejazdy pojazdu", exact: true }).getByRole("button").first().click();
  const form = dialog.getByRole("form", { name: "Cel i opis przejazdu", exact: true });
  await form.getByLabel(/Cel przejazdu/).fill("Private profile session fixture");
  // Suspend polling: the operation itself must invalidate the other tab's view.
  await page.clock.install();
  await page.clock.pauseAt(new Date());
  return form;
}

test.beforeEach(async ({ context }) => {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" }, stdio: "pipe",
  });
  await context.route("**/*", route => new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
});

for (const transport of ["BroadcastChannel", "storage"]) {
  test(`logout-all removes private drafts from other tabs without polling (${transport})`, async ({ page, context }) => {
    if (transport === "storage") {
      await context.addInitScript(() => Object.defineProperty(window, "BroadcastChannel", { value: undefined }));
    }
    await login(page);
    const other = await context.newPage();
    const draft = await privateDraft(other);
    await page.goto("/#profile");
    await page.getByRole("button", { name: "Wyloguj wszystkie urządzenia", exact: true }).click();
    await page.getByRole("button", { name: "Anuluj", exact: true }).click();
    expect((await page.request.get("/api/v1/auth/me")).status()).toBe(200);
    await expect(draft).toBeVisible();
    await page.getByRole("button", { name: "Wyloguj wszystkie urządzenia", exact: true }).click();
    await page.getByRole("button", { name: "Potwierdź wylogowanie wszystkich sesji", exact: true }).click();
    await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
    expect((await page.request.get("/api/v1/auth/me")).status()).toBe(401);
    await expect(draft).toHaveCount(0);
    await expect(other.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
    await other.screenshot({ path: test.info().outputPath("logout-all-cleared-other-tab.png") });
  });

  test(`password change clears old drafts while keeping the rotated shared session (${transport})`, async ({ page, context }) => {
    if (transport === "storage") {
      await context.addInitScript(() => Object.defineProperty(window, "BroadcastChannel", { value: undefined }));
    }
    await login(page);
    const other = await context.newPage();
    const draft = await privateDraft(other);
    await page.goto("/#profile");
    const form = page.getByRole("form", { name: "Zmiana hasła", exact: true });
    await form.getByLabel("Aktualne hasło", { exact: true }).fill(password);
    await form.getByLabel("Nowe hasło", { exact: true }).fill(replacement);
    await form.getByLabel("Powtórz nowe hasło", { exact: true }).fill(replacement);
    await form.getByRole("button", { name: "Zmień hasło", exact: true }).click();
    await expect(form.getByRole("status")).toContainText("Hasło zostało zmienione.");
    for (const field of ["Aktualne hasło", "Nowe hasło", "Powtórz nowe hasło"]) {
      await expect(form.getByLabel(field, { exact: true })).toHaveValue("");
    }
    expect((await page.request.get("/api/v1/auth/me")).status()).toBe(200);
    try {
      await expect(draft).toHaveCount(0);
      await expect(other.getByRole("heading", { name: /^Pojazdy\.?$/, level: 1 })).toBeVisible();
      expect((await other.request.get("/api/v1/auth/me")).status()).toBe(200);
      await other.screenshot({ path: test.info().outputPath("password-change-cleared-old-draft.png") });
    } finally {
      const restored = await page.request.post("/api/v1/auth/password/change", {
        headers: { Origin: origin }, data: { current_password: replacement, new_password: password },
      });
      expect(restored.status()).toBe(200);
    }
  });
}
