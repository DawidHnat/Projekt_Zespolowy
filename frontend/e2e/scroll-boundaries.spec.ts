import { execFileSync } from "node:child_process";
import { expect, test, type Page } from "@playwright/test";

// SCRUM-149: scroll boundaries keep the shell and backdrop still.
// Headless Chromium has no elastic overscroll, so the test covers what it can
// observe: the declared overscroll policy and real wheel/touch scroll chaining.

async function login(page: Page, hash: string) {
  await page.goto(`/#${hash}`);
  await page.getByLabel("Login", { exact: true }).fill("e2e-editor");
  await page.getByLabel("Hasło", { exact: true }).fill("synthetic-e2e-password");
  await page.getByRole("button", { name: "Zaloguj się", exact: true }).click();
  await expect(page.locator(".main-shell")).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
}

/** Makes the document scrollable and parks it mid-way so chaining is observable. */
async function parkDocumentMidway(page: Page) {
  await page.evaluate(() => {
    const spacer = document.createElement("div");
    spacer.dataset.testSpacer = "true";
    spacer.style.height = `${innerHeight * 2}px`;
    document.querySelector(".main-shell")!.append(spacer);
    scrollTo(0, Math.round(innerHeight / 2));
  });
  return page.evaluate(() => scrollY);
}

/** Makes bounded lists short, so even the single synthetic fixture vehicle overflows. */
async function shortenBoundedLists(page: Page) {
  await page.addStyleTag({
    content: ".fleet-list-content > .table-scroll, .vehicle-cards { max-height: 44px !important; }",
  });
}

/** Marks visible bounded lists (overscroll contain) that really overflow vertically. */
async function overflowingContainers(page: Page) {
  return page.evaluate(() => {
    const found: string[] = [];
    document.querySelectorAll<HTMLElement>("body *").forEach((node, index) => {
      const style = getComputedStyle(node);
      const box = node.getBoundingClientRect();
      if (!/(auto|scroll)/.test(style.overflowY) || node.scrollHeight <= node.clientHeight + 2) return;
      if (style.overscrollBehaviorY !== "contain") return;
      if (box.width === 0 || box.height === 0) return;
      node.dataset.scrollProbe = String(index);
      found.push(`${node.className || node.tagName} [${index}]`);
    });
    return found;
  });
}

/** A visible point whose scroll chain reaches the document directly. */
async function pageGrip(page: Page) {
  return page.evaluate(() => {
    const scrollsLocally = (node: Element | null) => {
      for (let el = node; el && el !== document.body; el = el.parentElement) {
        const style = getComputedStyle(el);
        if (/(auto|scroll)/.test(style.overflowY) && el.scrollHeight > el.clientHeight + 2) return true;
      }
      return false;
    };
    for (let y = 80; y < innerHeight - 20; y += 40)
      for (const x of [innerWidth - 30, innerWidth / 2, 30]) {
        const node = document.elementFromPoint(x, y);
        if (node && node !== document.documentElement && !scrollsLocally(node)) return { x, y };
      }
    throw new Error("no page grip found");
  });
}

test.beforeEach(async ({ page }) => {
  execFileSync(process.env.E2E_PYTHON || "python3", ["tests/e2e_server.py", "reset-case"], {
    cwd: "../backend", env: { ...process.env, PYTHONPATH: ".", FLEET_FLOW_E2E: "true" }, stdio: "pipe",
  });
  await page.route("**/*", route => new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
});

test("document and app shell do not rubber-band at the scroll edges", async ({ page }) => {
  await login(page, "dashboard");
  for (const material of ["classic", "glass"]) {
    await page.evaluate(value => { document.documentElement.dataset.material = value; }, material);
    const policy = await page.evaluate(() => {
      const root = getComputedStyle(document.documentElement);
      const body = getComputedStyle(document.body);
      return { root: root.overscrollBehaviorY, body: body.backgroundAttachment, rootBackground: root.backgroundColor };
    });
    expect(policy.root, material).toBe("none");
    // The backdrop lives on a fixed layer; the canvas has an explicit colour behind it.
    expect(policy.body, material).not.toContain("fixed");
    expect(policy.rootBackground, material).not.toBe("rgba(0, 0, 0, 0)");
  }
});

for (const hash of ["dashboard", "map"])
test(`bounded lists on the ${hash} page keep scrolling local at their edges`, async ({ page, isMobile }) => {
  await login(page, hash);
  await shortenBoundedLists(page);
  const start = await parkDocumentMidway(page);
  await expect.poll(() => overflowingContainers(page).then(found => found.length), "expected an overflowing list").toBeGreaterThan(0);
  for (const probe of await page.locator("[data-scroll-probe]").all()) {
    await probe.evaluate(node => { node.scrollTop = node.scrollHeight; });
    await probe.scrollIntoViewIfNeeded();
    const before = await page.evaluate(() => scrollY);
    const box = (await probe.boundingBox())!;
    const x = box.x + box.width / 2;
    const y = box.y + Math.min(box.height / 2, 40);
    if (isMobile) {
      const session = await page.context().newCDPSession(page);
      await session.send("Input.synthesizeScrollGesture", { x, y, yDistance: -300, speed: 1200, gestureSourceType: "touch" });
    } else {
      await page.mouse.move(x, y);
      await page.mouse.wheel(0, 400);
    }
    await page.waitForTimeout(150);
    const contained = await probe.evaluate(node => Math.abs(node.scrollTop + node.clientHeight - node.scrollHeight) <= 2);
    expect(contained, "container stays at its bottom edge").toBe(true);
    expect(await page.evaluate(() => scrollY), "document did not move").toBe(before);
  }
  expect(start).toBeGreaterThan(0);
});

for (const hash of ["dashboard", "vehicles", "drivers"])
  test(`wheel over tiles, cards and tables still scrolls the ${hash} page`, async ({ page }) => {
    await login(page, hash);
    await parkDocumentMidway(page);
    await page.evaluate(() => scrollTo(0, 0));
    // Outside bounded lists the wheel moves the document to its real end,
    // including over tile frames and tables that fit their content.
    for (let step = 0, last = -1; step < 80; step += 1) {
      const position = await page.evaluate(() => scrollY);
      if (position === last) break;
      last = position;
      const grip = await pageGrip(page);
      await page.mouse.move(grip.x, grip.y);
      await page.mouse.wheel(0, 900);
      await page.waitForTimeout(60);
    }
    await expect.poll(() => page.evaluate(() => Math.ceil(scrollY + innerHeight) >= document.documentElement.scrollHeight - 1)).toBe(true);
  });

test("keyboard scrolling and list ends still work", async ({ page }) => {
  await login(page, "dashboard");
  await parkDocumentMidway(page);
  await page.keyboard.press("Home");
  await expect.poll(() => page.evaluate(() => scrollY)).toBe(0);
  await page.keyboard.press("End");
  await expect.poll(() => page.evaluate(() => scrollY)).toBeGreaterThan(0);
  // The tile's vehicle list remains reachable to its last row.
  await page.evaluate(() => scrollTo(0, 0));
  await shortenBoundedLists(page);
  await expect.poll(() => overflowingContainers(page).then(found => found.length)).toBeGreaterThan(0);
  const probe = page.locator("[data-scroll-probe]").first();
  await probe.hover();
  for (let step = 0; step < 15; step += 1) await page.mouse.wheel(0, 300);
  await expect.poll(() => probe.evaluate(node => node.scrollTop + node.clientHeight >= node.scrollHeight - 2)).toBe(true);
});

test("modal dialog locks the page without shifting the shell", async ({ page }) => {
  await login(page, "vehicles");
  await parkDocumentMidway(page);
  const opener = page.getByRole("button", { name: /Szczegóły.*Pojazd E2E/ });
  // Bring the opener into view first, so only the dialog could move the page.
  await opener.scrollIntoViewIfNeeded();
  const start = await page.evaluate(() => scrollY);
  const shell = page.locator(".main-shell");
  const before = await shell.boundingBox();
  await opener.click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading", { name: "Szczegóły pojazdu" })).toBeVisible();
  expect(await shell.boundingBox(), "opening the dialog does not move the shell").toEqual(before);
  // Wheel over the backdrop and over the dialog after reaching its end.
  await page.mouse.move(4, 500);
  await page.mouse.wheel(0, 500);
  const box = (await dialog.boundingBox())!;
  await dialog.evaluate(node => { node.scrollTop = node.scrollHeight; });
  await page.mouse.move(box.x + box.width / 2, box.y + 40);
  await page.mouse.wheel(0, 500);
  await page.waitForTimeout(150);
  expect(await page.evaluate(() => scrollY), "document stays put under the dialog").toBe(start);
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  expect(await page.evaluate(() => scrollY), "closing keeps the reading position").toBe(start);
  expect(await shell.boundingBox()).toEqual(before);
});
