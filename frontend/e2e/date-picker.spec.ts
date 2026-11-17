import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";

test.beforeEach(async ({ context }) => {
  await context.route("**/*", route =>
    new URL(route.request().url()).hostname === "127.0.0.1"
      ? route.continue() : route.abort()
  );
});

async function login(page: Page) {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
    cwd: "../backend",
    env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" },
    stdio: "pipe",
  });
  await page.goto("/#vehicles");
  await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.getByRole("heading", { name: /^Pojazdy\.?$/, level: 1 })).toBeVisible();
}

test("SCRUM-77: Enter otwiera kalendarz, Escape zamyka i oddaje fokus", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2026-10-18T10:00:00.000Z"));
  await login(page);
  await page.goto("/#dashboard");

  const trigger = page.getByRole("button", { name: "Dzień ostatnich przejazdów" });
  await expect(trigger).toBeVisible();
  await trigger.focus();
  await trigger.press("Enter");

  await expect(trigger).toHaveAttribute("aria-expanded", "true");
  await trigger.press("Escape");

  await expect(trigger).toHaveAttribute("aria-expanded", "false");
  await expect(trigger).toBeFocused();
});

test("SCRUM-77: Spacja i skróty dat działają, wpisywanie jest zablokowane", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2026-10-18T10:00:00.000Z"));
  await login(page);
  await page.goto("/#dashboard");

  const group = page.getByRole("group", { name: "Dzień ostatnich przejazdów" });
  const trigger = group.getByRole("button", { name: "Dzień ostatnich przejazdów" });

  await trigger.focus();
  await trigger.press("Space");
  await expect(trigger).toHaveAttribute("aria-expanded", "true");

  await trigger.press("Escape");
  await group.getByRole("button", { name: "Wczoraj" }).click();
  await expect(group.getByRole("button", { name: "Wczoraj" })).toHaveAttribute("aria-pressed", "true");

  const before = await trigger.innerText();
  await trigger.press("Backspace");
  await trigger.press("a");
  await trigger.evaluate(button => {
    const clipboard = new DataTransfer();
    clipboard.setData("text/plain", "2026-01-01");
    button.dispatchEvent(new ClipboardEvent("paste", {
      bubbles: true,
      cancelable: true,
      clipboardData: clipboard,
    }));
  });
  expect(await trigger.innerText()).toBe(before);

  await group.getByRole("button", { name: "Dzisiaj" }).click();
  await expect(group.getByRole("button", { name: "Dzisiaj" })).toHaveAttribute("aria-pressed", "true");
});

test("SCRUM-77: Escape kalendarza nie zamyka okna pojazdu", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2026-10-18T10:00:00.000Z"));
  await login(page);

  await page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("tab", { name: "Podróże", exact: true }).click();

  const trigger = dialog.getByRole("button", { name: "Dzień podróży pojazdu" });
  await expect(trigger).toBeVisible();

  await trigger.focus();
  await trigger.press("Enter");
  await expect(trigger).toHaveAttribute("aria-expanded", "true");

  await trigger.press("Escape");
  await expect(trigger).toHaveAttribute("aria-expanded", "false");
  await expect(dialog).toBeVisible();
  await expect(trigger).toBeFocused();
});

test("SCRUM-77: min/max i wybór daty wywołują onChange", async ({ page }) => {
  await page.goto("http://127.0.0.1:54174/e2e/fixtures/date-picker.html");

  const trigger = page.getByRole("button", { name: "Data testowa" });
  await trigger.click();

  const calendar = page.locator(".ff-calendar");
  await expect(calendar).toBeVisible();

  const day = (number: number) =>
    calendar.locator(".flatpickr-day:not(.prevMonthDay):not(.nextMonthDay)")
      .filter({ hasText: new RegExp(`^${number}$`) });

  await expect(day(14)).toHaveClass(/flatpickr-disabled/);
  await expect(day(21)).toHaveClass(/flatpickr-disabled/);
  await expect(day(18)).not.toHaveClass(/flatpickr-disabled/);

  await day(18).click();
  await expect(page.getByTestId("value")).toHaveText("2026-10-18");
  await expect(page.getByTestId("changes")).toHaveText("2026-10-18");
  await expect(trigger).toContainText("18.10.2026");
});

test("SCRUM-77: zewnętrzna zmiana wartości nie wywołuje onChange", async ({ page }) => {
  await page.goto("http://127.0.0.1:54174/e2e/fixtures/date-picker.html");

  await page.getByRole("button", { name: "Ustaw z zewnątrz" }).click();

  await expect(page.getByTestId("value")).toHaveText("2026-10-19");
  await expect(page.getByTestId("changes")).toBeEmpty();

  const trigger = page.getByRole("button", { name: "Data testowa" });
  await expect(trigger).toContainText("19.10.2026");

  await trigger.click();
  await expect(page.locator(".ff-calendar .flatpickr-day.selected")).toContainText("19");
});

test("SCRUM-77: disabled blokuje otwieranie i zachowuje datę", async ({ page }) => {
  await page.goto("http://127.0.0.1:54174/e2e/fixtures/date-picker.html");

  const trigger = page.getByRole("button", { name: "Data testowa" });
  await trigger.click();
  await expect(trigger).toHaveAttribute("aria-expanded", "true");

  await page.getByRole("button", { name: "Przełącz blokadę" }).evaluate((button: HTMLButtonElement) => button.click());
  await expect(trigger).toBeDisabled();
  await expect(trigger).toHaveAttribute("aria-expanded", "false");

  await expect(page.getByTestId("value")).toHaveText("2026-10-17");
  await expect(page.getByTestId("changes")).toBeEmpty();

  await page.getByRole("button", { name: "Przełącz blokadę" }).evaluate((button: HTMLButtonElement) => button.click());
  await expect(trigger).toBeEnabled();
  await trigger.click();
  await expect(trigger).toHaveAttribute("aria-expanded", "true");
});
