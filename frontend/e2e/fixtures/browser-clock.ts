import type { Page } from "@playwright/test";

export async function pauseBrowserClock(page: Page, target = new Date()) {
  // Leave room for real time between installation and freezing the clock.
  await page.clock.install({ time: new Date(target.getTime() - 60_000) });
  await page.clock.pauseAt(target);
}
