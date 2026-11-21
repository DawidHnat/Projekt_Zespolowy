import { test, expect, type Page } from "@playwright/test";

const origin = "http://127.0.0.1:54173";
const password = "synthetic-e2e-password";

async function login(page: Page, identifier: string) {
  await page.getByLabel("Login", { exact: true }).fill(identifier);
  await page.getByLabel("Hasło", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
}

test("a new address becomes visible and usable only after the authenticated mailbox confirmation", async ({
  page,
  browser,
  context,
  request,
}, testInfo) => {
  const username = `e2e-profile-${testInfo.project.name}`;
  const oldEmail = `${username}-old@example.com`;
  const newEmail = `${username}@example.com`;
  const secondDevice = await browser.newContext({
    baseURL: origin,
    viewport: page.viewportSize() ?? undefined,
    isMobile: testInfo.project.name === "mobile",
    locale: "pl-PL",
  });
  for (const isolatedContext of [context, secondDevice]) {
    await isolatedContext.route("**/*", (route) =>
      new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort(),
    );
  }
  try {
    await page.goto("/#profile");
    await login(page, oldEmail);
    await expect(page.getByText(oldEmail, { exact: true })).toBeVisible();
    await expect(page.getByText("Anna", { exact: true })).toBeVisible();
    await expect(page.getByText("Próba", { exact: true })).toBeVisible();
    await expect(page.getByText("Użytkownik", { exact: true })).toBeVisible();

    const opener = page.getByRole("button", { name: "Zmień adres e-mail", exact: true });
    await opener.click();
    const form = page.getByRole("form", { name: "Zmiana adresu e-mail", exact: true });
    const address = form.getByLabel("Nowy adres e-mail", { exact: true });
    const current = form.getByLabel("Aktualne hasło", { exact: true });
    const submit = form.getByRole("button", { name: "Wyślij link potwierdzający", exact: true });
    await expect(address).toBeFocused();
    await form.getByRole("button", { name: "Anuluj", exact: true }).click();
    await expect(opener).toBeFocused();
    await opener.click();
    await address.fill(newEmail);
    await current.fill("wrong-synthetic-password");
    await submit.click();
    await expect(form.getByRole("alert")).toHaveText("Aktualne hasło jest niepoprawne.");
    await expect(current).toHaveValue("");

    await current.fill(password);
    let releaseDelivery: () => void = () => {};
    const delivery = new Promise<void>((resolve) => { releaseDelivery = resolve; });
    await page.route("**/api/v1/auth/email/change/request", async (route) => {
      await delivery;
      await route.continue();
    }, { times: 1 });
    await submit.click();
    try {
      await expect(form.getByRole("button", { name: "Wysyłanie…", exact: true })).toBeDisabled();
    } finally {
      releaseDelivery();
    }
    await expect(page.getByRole("status").filter({ hasText: "Link potwierdzający został wysłany" }))
      .toContainText(newEmail);
    await expect(page.getByText(oldEmail, { exact: true })).toBeVisible();

    const mailbox = await request.get(`http://127.0.0.1:58000/__e2e/email-changes/${username}`);
    const { url } = await mailbox.json();
    expect(url).toMatch(/^http:\/\/127\.0\.0\.1:54173\/#confirm-email\?token=/);
    const confirmation = await secondDevice.newPage();
    await confirmation.goto(url);
    await expect(confirmation.getByRole("heading", { name: "Zaloguj się, aby potwierdzić e-mail" })).toBeVisible();
    await login(confirmation, oldEmail);
    await expect(confirmation.getByRole("heading", { name: "Potwierdź zmianę e-maila", exact: true })).toBeVisible();
    expect((await confirmation.request.get("/api/v1/auth/profile").then((response) => response.json())).email)
      .toBe(oldEmail);

    await confirmation.getByRole("button", { name: "Potwierdź zmianę adresu", exact: true }).click();
    await expect(confirmation.getByRole("heading", { name: "Adres e-mail został zmieniony" })).toBeVisible();
    await expect(confirmation).toHaveURL(origin + "/#profile");
    await confirmation.getByRole("button", { name: "Wróć do profilu", exact: true }).click();
    await expect(confirmation.getByText(newEmail, { exact: true })).toBeVisible();
    expect((await page.request.get("/api/v1/auth/me")).status()).toBe(401);
    await page.reload();
    await login(page, newEmail);
    await expect(page.getByText(newEmail, { exact: true })).toBeVisible();

    await confirmation.goto(url);
    await confirmation.getByRole("button", { name: "Potwierdź zmianę adresu", exact: true }).click();
    await expect(confirmation.getByRole("alert")).toContainText("Link jest niepoprawny lub wygasł.");
    await confirmation.getByRole("button", { name: "Wróć do profilu", exact: true }).click();
    await expect(confirmation.getByText(newEmail, { exact: true })).toBeVisible();
  } finally {
    await secondDevice.close();
  }
});
