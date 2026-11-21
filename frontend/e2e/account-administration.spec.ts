import { expect, test, type Page } from "@playwright/test";

const initialPassword = "synthetic-e2e-password";
const recipientPassword = "synthetic-first-account-password";

async function login(page: Page, identity: string, password: string) {
  await page.getByLabel("Login", { exact: true }).fill(identity);
  await page.getByLabel("Hasło", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
}

test("administrator invites a new user, who activates and signs in by email", async ({
  page, browser, request,
}, info) => {
  const username = `e2e-invite-${info.project.name}`;
  const email = `${username}@example.com`;
  await page.goto("/#users");
  await login(page, "e2e-admin", initialPassword);
  await expect(page.getByRole("heading", { name: "Konta użytkowników" })).toBeVisible();
  await page.getByRole("button", { name: "Dodaj konto" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading", { name: "Dodaj konto" })).toBeVisible();
  await dialog.getByLabel("Imię", { exact: true }).fill("Anna");
  await dialog.getByLabel("Nazwisko", { exact: true }).fill("Testowa");
  await dialog.getByLabel("Login", { exact: true }).fill(username);
  await dialog.getByLabel("E-mail", { exact: true }).fill(email);
  await dialog.getByRole("button", { name: "Utwórz konto" }).click();
  await expect(dialog.getByRole("status")).toContainText("Konto utworzone");
  await dialog.getByRole("button", { name: "Wyślij zaproszenie" }).click();
  await expect(dialog.getByRole("status")).toContainText("Serwer pocztowy przyjął zaproszenie");
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(page.locator(".account-list")).toContainText("Oczekujące");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
    page.viewportSize()!.width,
  );

  const captured = await request.get(`http://127.0.0.1:58000/__e2e/invitations/${username}`);
  const { url } = await captured.json() as { url: string };
  expect(url).toContain("/#activate-account?token=");
  const recipient = await browser.newPage({
    viewport: page.viewportSize(),
    locale: "pl-PL",
    isMobile: info.project.name === "mobile",
    hasTouch: info.project.name === "mobile",
  });
  try {
    await recipient.goto(url);
    await expect(recipient.getByRole("heading", { name: "Aktywuj konto" })).toBeVisible();
    await recipient.getByLabel("Nowe hasło", { exact: true }).fill(recipientPassword);
    await recipient.getByLabel("Powtórz hasło", { exact: true }).fill(recipientPassword);
    await recipient.getByRole("button", { name: "Aktywuj konto" }).click();
    await expect(recipient.getByRole("status")).toContainText("Konto zostało aktywowane");
    expect(recipient.url()).not.toContain("token=");
    await login(recipient, email, recipientPassword);
    await expect(recipient.getByRole("heading", { name: /^Pulpit\.?$/ })).toBeVisible();
    await recipient.goto("/#users");
    await expect(recipient.getByRole("heading", { name: "Panel administratora" })).toBeVisible();
    const denied = await recipient.request.get(new URL("/api/v1/admin/users", url).toString());
    expect(denied.status()).toBe(403);
  } finally {
    await recipient.context().close();
  }
});
