import { execFileSync } from "node:child_process";
import { test, expect, type Page } from "@playwright/test";

async function login(page: Page, role = "editor") {
  await page.goto("/#vehicles");
  await page.getByLabel("Login", { exact: true }).fill(`e2e-${role}`);
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.getByRole("article", { name: "Kafelek Pojazd E2E", exact: true })).toBeVisible();
}

async function logout(page: Page) {
  const menu = page.getByRole("button", { name: "Otwórz menu", exact: true });
  if (await menu.isVisible()) await menu.click();
  await page.getByRole("button", { name: "Wyloguj się", exact: true }).click();
  await expect(page.getByRole("button", { name: "Zaloguj się", exact: true })).toBeVisible();
}

async function image(page: Page, color = "#1479e8", mimeType = "image/png") {
  const encoded = await page.evaluate(({ color, mimeType }) => {
    const canvas = document.createElement("canvas");
    canvas.width = 1200;
    canvas.height = 600;
    const context = canvas.getContext("2d")!;
    context.fillStyle = color;
    context.fillRect(0, 0, canvas.width, canvas.height);
    return canvas.toDataURL(mimeType).split(",")[1];
  }, { color, mimeType });
  const extension = mimeType.split("/")[1];
  return { name: `synthetic-photo.${extension}`, mimeType, buffer: Buffer.concat([Buffer.from(encoded, "base64"), Buffer.from("synthetic-private-metadata")]) };
}

const tile = (page: Page) => page.getByRole("article", { name: "Kafelek Pojazd E2E", exact: true });
const photo = (page: Page) => tile(page).getByRole("img", { name: "Zdjęcie: Pojazd E2E", exact: true });

test.beforeEach(async ({ page }) => {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" }, stdio: "pipe",
  });
  await page.route("**/*", route => new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
});

test("SCRUM-45: photo is re-encoded, persists, is isolated by account and can be replaced/deleted", async ({ page }) => {
  const writes: string[] = [];
  page.on("request", request => {
    const path = new URL(request.url()).pathname;
    if (["POST", "PUT", "PATCH"].includes(request.method()) && !path.includes("/auth/")) writes.push(path);
  });
  await login(page);
  await page.getByRole("button", { name: "Zdjęcie: Pojazd E2E", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Zdjęcie pojazdu", { exact: true }).setInputFiles(await image(page));
  await expect(dialog.getByRole("button", { name: "Usuń zdjęcie", exact: true })).toBeEnabled();
  await dialog.getByRole("button", { name: "Gotowe", exact: true }).click();
  await expect(photo(page)).toBeVisible();
  const uploaded = await photo(page).getAttribute("src");
  await page.getByRole("button", { name: "Szczegóły: Pojazd E2E", exact: true }).click();
  await expect(dialog.getByRole("img", { name: "Zdjęcie: Pojazd E2E", exact: true })).toHaveAttribute("src", uploaded!);
  await page.getByRole("button", { name: "Zamknij szczegóły pojazdu", exact: true }).click();
  const stored = await page.evaluate(async () => {
    const db = await new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open("fleet-flow.vehicle-photos.v1", 1);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    try {
      const rows = await new Promise<any[]>((resolve, reject) => {
        const request = db.transaction("photos").objectStore("photos").getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
      const item = rows[0].image;
      return { width: item.width, height: item.height, type: item.blob.type,
        originalMetadata: (await item.blob.text()).includes("synthetic-private-metadata") };
    } finally { db.close(); }
  });
  expect(stored).toEqual({ width: 1024, height: 512, type: "image/webp", originalMetadata: false });
  await page.reload();
  await expect(photo(page)).toBeVisible();
  await logout(page);
  await login(page, "viewer");
  await expect(photo(page)).toHaveCount(0);
  await logout(page);
  await login(page);
  await expect(photo(page)).toBeVisible();
  const beforeReplacement = await photo(page).getAttribute("src");
  await page.getByRole("button", { name: "Zdjęcie: Pojazd E2E", exact: true }).click();
  await dialog.getByLabel("Zdjęcie pojazdu", { exact: true }).setInputFiles(await image(page, "#138c76", "image/jpeg"));
  await dialog.getByRole("button", { name: "Gotowe", exact: true }).click();
  await expect(photo(page)).not.toHaveAttribute("src", beforeReplacement!);
  await page.getByRole("button", { name: "Zdjęcie: Pojazd E2E", exact: true }).click();
  await dialog.getByRole("button", { name: "Usuń zdjęcie", exact: true }).click();
  await expect(dialog.getByRole("button", { name: "Usuń zdjęcie", exact: true })).toHaveCount(0);
  await dialog.getByRole("button", { name: "Gotowe", exact: true }).click();
  await page.reload();
  await expect(tile(page)).toBeVisible();
  await expect(photo(page)).toHaveCount(0);
  expect(writes).toEqual([]);
});

test("SCRUM-45: invalid images keep the previous photo and report readable errors", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: "Zdjęcie: Pojazd E2E", exact: true }).click();
  const dialog = page.getByRole("dialog");
  const input = dialog.getByLabel("Zdjęcie pojazdu", { exact: true });
  await input.setInputFiles(await image(page, "#1479e8", "image/webp"));
  await expect(dialog.getByRole("button", { name: "Usuń zdjęcie", exact: true })).toBeEnabled();
  const existing = await dialog.getByRole("img", { name: "Zdjęcie: Pojazd E2E", exact: true }).getAttribute("src");
  await input.setInputFiles({ name: "not-a-photo.svg", mimeType: "image/svg+xml", buffer: Buffer.from("<svg/>") });
  await expect(dialog.getByRole("alert")).toContainText("JPG, PNG lub WebP");
  await input.setInputFiles({ name: "corrupt.png", mimeType: "image/png", buffer: Buffer.from("not a valid PNG") });
  await expect(dialog.getByRole("alert")).toContainText("Nie udało się odczytać obrazu");
  await input.setInputFiles({ name: "large.png", mimeType: "image/png", buffer: Buffer.alloc(10 * 1024 * 1024 + 1) });
  await expect(dialog.getByRole("alert")).toContainText("do 10 MB");
  await expect(dialog.getByRole("img", { name: "Zdjęcie: Pojazd E2E", exact: true })).toHaveAttribute("src", existing!);
  await page.screenshot({ path: test.info().outputPath("photo-error.png"), fullPage: true });
  await page.keyboard.press("Escape");
  await page.reload();
  await expect(photo(page)).toBeVisible();
});

test("SCRUM-45: unavailable photo storage allows a session photo and recovery", async ({ page }) => {
  await page.addInitScript(() => {
    const open = indexedDB.open.bind(indexedDB);
    Object.assign(window, { restorePhotoStorage: () => { indexedDB.open = open; } });
    indexedDB.open = () => { throw new DOMException("Synthetic storage failure", "SecurityError"); };
  });
  await login(page);
  await page.getByRole("button", { name: "Zdjęcie: Pojazd E2E", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("alert")).toContainText("Zapisane zdjęcia są chwilowo niedostępne");
  await dialog.getByLabel("Zdjęcie pojazdu", { exact: true }).setInputFiles(await image(page));
  await expect(dialog.getByRole("alert")).toContainText("Zdjęcie działa w tej sesji");
  await expect(dialog.getByRole("img", { name: "Zdjęcie: Pojazd E2E", exact: true })).toBeVisible();
  await page.evaluate(() => (window as unknown as { restorePhotoStorage(): void }).restorePhotoStorage());
  await dialog.getByRole("button", { name: "Usuń zdjęcie", exact: true }).click();
  await expect(dialog.getByRole("button", { name: "Usuń zdjęcie", exact: true })).toHaveCount(0);
  await expect(dialog.getByRole("alert")).toHaveCount(0);
});

test("SCRUM-45: minimum card, cancel and settings preserve the layout draft", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await login(page);
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  await page.getByRole("button", { name: "Rozmiar: Pojazd E2E", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Małe", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Gotowe", exact: true }).click();
  await expect(tile(page)).toHaveCSS("width", "280px");
  await expect(tile(page)).toHaveCSS("height", "420px");
  await page.goto("/#settings");
  await page.getByRole("button", { name: "Ciemny", exact: true }).click();
  await page.getByRole("button", { name: "Klasyczny", exact: true }).click();
  await page.goto("/#vehicles");
  await expect(page.getByRole("button", { name: "Zapisz układ", exact: true })).toBeVisible();
  await expect(tile(page)).toHaveCSS("width", "280px");
  await page.setViewportSize({ width: 320, height: 568 });
  await expect(page.locator(".sidebar")).toBeHidden();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  const card = (await tile(page).boundingBox())!;
  const footer = (await tile(page).locator("footer").boundingBox())!;
  expect(footer.y + footer.height).toBeLessThanOrEqual(card.y + card.height);
  await page.screenshot({ path: test.info().outputPath("minimum-card-dark.png"), fullPage: true });
  await page.getByRole("button", { name: "Anuluj", exact: true }).click();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect(tile(page)).toHaveCSS("width", "320px");
  await expect(tile(page)).toHaveCSS("height", "440px");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.locator("html")).toHaveAttribute("data-material", "solid");
});

test("SCRUM-45: a vertical mobile resize preserves the saved desktop width", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await login(page);
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  await page.getByRole("button", { name: "Rozmiar: Pojazd E2E", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Duże", exact: true }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Gotowe", exact: true }).click();
  await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
  await expect(tile(page)).toHaveCSS("width", "480px");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  const handle = page.getByRole("button", { name: "Zmień rozmiar: Pojazd E2E", exact: true });
  await handle.scrollIntoViewIfNeeded();
  const box = (await handle.boundingBox())!;
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + 2, y + 50, { steps: 5 });
  await page.mouse.up();
  await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect(tile(page)).toHaveCSS("width", "480px");
  await expect(tile(page)).toHaveCSS("height", "550px");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Edytuj układ", exact: true }).click();
  const visibleWidth = (await tile(page).boundingBox())!.width;
  await handle.scrollIntoViewIfNeeded();
  const nextBox = (await handle.boundingBox())!;
  const nextX = nextBox.x + nextBox.width / 2;
  const nextY = nextBox.y + nextBox.height / 2;
  await page.mouse.move(nextX, nextY);
  await page.mouse.down();
  await page.mouse.move(nextX - 50, nextY, { steps: 5 });
  await page.mouse.up();
  await page.getByRole("button", { name: "Zapisz układ", exact: true }).click();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect(tile(page)).toHaveCSS("width", `${Math.max(280, visibleWidth - 50)}px`);
  await expect(tile(page)).toHaveCSS("height", "550px");
});
