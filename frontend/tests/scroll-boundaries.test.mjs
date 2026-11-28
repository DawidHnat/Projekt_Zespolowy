import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";

// SCRUM-149: every scroll container states its overscroll policy. Bounded lists,
// dialogs and popovers use contain; frames that usually fit their content stay
// auto, because Chromium applies contain even when nothing overflows and the
// page would stop scrolling under them. Rules are scanned in our stylesheets.
const sheets = [
  ...readdirSync(new URL("../src/app/", import.meta.url)).filter(name => name.endsWith(".css")).map(name => `../src/app/${name}`),
  ...readdirSync(new URL("../src/shared/components/", import.meta.url)).filter(name => name.endsWith(".css")).map(name => `../src/shared/components/${name}`),
];
const rules = sheets.flatMap(sheet => {
  const css = readFileSync(new URL(sheet, import.meta.url), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  return [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map(([, selector, body]) => ({ sheet, selector: selector.trim(), body }));
});

test("every scroll container declares its overscroll policy", () => {
  const scrollers = rules.filter(rule => /(^|;|\s)overflow(-[xy])?\s*:\s*(auto|scroll)/.test(rule.body));
  assert.ok(scrollers.length > 5, "expected the known scroll containers");
  const missing = scrollers.filter(rule => !/overscroll-behavior(-[xy])?\s*:\s*(contain|none|auto)/.test(rule.body));
  assert.deepEqual(missing.map(rule => `${rule.sheet}: ${rule.selector}`), []);
  const frames = [".widget-content", ".sidebar"];
  for (const frame of frames)
    assert.match(rules.find(rule => rule.selector === frame && /overflow/.test(rule.body)).body, /overscroll-behavior:\s*auto/, frame);
});

test("the document root does not rubber-band and modals keep the page still", () => {
  const root = rules.find(rule => rule.selector === "html");
  assert.match(root.body, /overscroll-behavior-y:\s*none/);
  assert.match(root.body, /scrollbar-gutter:\s*stable/);
  assert.match(root.body, /background:\s*var\(--background\)/);
  assert.ok(rules.some(rule => rule.selector === "html:has(dialog:modal)" && /overflow:\s*hidden/.test(rule.body)));
  assert.ok(rules.every(rule => !/background-attachment:\s*fixed/.test(rule.body)), "use a fixed layer instead");
});
