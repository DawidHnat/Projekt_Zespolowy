import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";

const trip = "22222222-2222-4222-8222-222222222222";
const origin = "http://127.0.0.1:54173";

async function login(page: Page, role = "editor") {
  await page.goto("/#vehicles");
  await page.getByLabel("Login", { exact: true }).fill(`e2e-${role}`);
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.getByRole("heading", { name: /^Pojazdy\.?$/, level: 1 })).toBeVisible();
}

async function annotation(page: Page) {
  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("tab", { name: "Podróże", exact: true }).click();
  await dialog.getByRole("list", { name: "Przejazdy pojazdu", exact: true }).getByRole("button").first().click();
  return dialog.getByRole("form", { name: "Cel i opis przejazdu", exact: true });
}

test.beforeEach(async ({ context }) => {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" }, stdio: "pipe",
  });
  await context.route("**/*", route => new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
});

test("restored pages hide private data until session revalidation settles", async ({ page }) => {
  await login(page);
  const form = await annotation(page);
  await form.getByLabel(/Cel przejazdu/).fill("Private restored page fixture");
  expect((await page.request.post("/api/v1/auth/logout", { headers: { Origin: origin } })).ok()).toBeTruthy();
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/v1/auth/me", async route => {
    await pending;
    await route.fulfill({ status: 401, contentType: "application/json", body: '{"error":{"code":"UNAUTHENTICATED"}}' });
  });
  try {
    const revalidation = page.waitForRequest("**/api/v1/auth/me");
    await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true })));
    await revalidation;
    await expect(form).toHaveCount(0);
    await expect(page.getByRole("status")).toHaveText("Sprawdzanie sesji…");
    await page.screenshot({ path: test.info().outputPath("private-view-cleared.png") });
  } finally {
    release();
  }
  await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
});

test("a late 401 from the old account cannot clear a newer login", async ({ page }) => {
  await login(page);
  const form = await annotation(page);
  await form.getByLabel(/Cel przejazdu/).fill("Delayed old-account request");
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  await page.route(`**/api/v1/trips/${trip}/annotation`, async route => {
    await pending;
    await route.fulfill({ status: 401, contentType: "application/json", body: '{"error":{"code":"UNAUTHENTICATED"}}' });
  });
  try {
    const saved = page.waitForRequest(request => request.method() === "PATCH");
    await form.getByRole("button", { name: "Zapisz cel i opis", exact: true }).click();
    await saved;
    page.once("dialog", dialog => dialog.accept());
    await page.getByRole("button", { name: "Zamknij szczegóły pojazdu" }).click();
    const menu = page.getByRole("button", { name: "Otwórz menu", exact: true });
    if (await menu.isVisible()) await menu.click();
    await page.getByRole("button", { name: "Wyloguj się", exact: true }).click();
    await login(page, "viewer");
    const oldResponse = page.waitForResponse(response => response.status() === 401 && response.url().includes(`/trips/${trip}/annotation`));
    release();
    await oldResponse;
    // The server still accepts the new shared cookie. The UI must keep that account.
    const current = await page.request.get("/api/v1/auth/me");
    expect(current.status()).toBe(200);
    expect((await current.json()).user.role).toBe("viewer");
    await expect(page.getByRole("heading", { name: /^Pojazdy\.?$/, level: 1 })).toBeVisible();
    await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toHaveCount(0);
    const currentForm = await annotation(page);
    await expect(currentForm.getByLabel(/Cel przejazdu/)).toHaveAttribute("readonly", "");
    await expect(currentForm.getByRole("button", { name: "Zapisz cel i opis", exact: true })).toHaveCount(0);
    await page.screenshot({ path: test.info().outputPath("current-account-preserved.png") });
  } finally {
    release();
  }
});
