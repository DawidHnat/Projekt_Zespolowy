import { test } from "node:test";
import assert from "node:assert/strict";
import {
  cardSize,
  normalizeLayoutConfig,
  resizeCards,
  targetSizes,
  CARD_DEFAULT,
  CARD_MIN,
  CARD_MAX,
} from "../src/features/fleet/model/vehicle-layout.ts";
import {
  normalizePageSize,
  pageWindow,
} from "../src/shared/components/pagination-model.ts";
const a = "00000000-0000-4000-8000-000000000001";
const b = "00000000-0000-4000-8000-000000000002";
const c = "00000000-0000-4000-8000-000000000003";

test("migration preserves independent v1 sizes and supports new fleet defaults", () => {
  const legacy = { [a]: { width: 400, height: 500 } };
  const migrated = normalizeLayoutConfig(legacy);
  assert.deepEqual(cardSize(migrated, a), legacy[a]);
  assert.deepEqual(cardSize(migrated, b), CARD_DEFAULT);
  const saved = resizeCards(migrated, "all", { width: 480, height: 500 });
  assert.deepEqual(
    normalizeLayoutConfig(JSON.parse(JSON.stringify(saved))),
    saved,
  );
  assert.deepEqual(cardSize(saved, c), { width: 480, height: 500 });
  assert.deepEqual(
    normalizeLayoutConfig({
      version: 2,
      defaultSize: { width: Infinity },
      sizes: [],
    }).defaultSize,
    CARD_DEFAULT,
  );
});
test("selected resizing preserves unselected cards and the other axis, including IDs from other pages", () => {
  const saved = normalizeLayoutConfig({
    [a]: { width: 400, height: 500 },
    [b]: { width: 320, height: 600 },
  });
  const draft = resizeCards(saved, [a, b, a, "__proto__"], { width: 480 });
  assert.deepEqual(cardSize(draft, a), { width: 480, height: 500 });
  assert.deepEqual(cardSize(draft, b), { width: 480, height: 600 });
  assert.deepEqual(cardSize(draft, c), CARD_DEFAULT);
  assert.deepEqual(cardSize(saved, a), { width: 400, height: 500 });
  assert.deepEqual(resizeCards(saved, [], { height: 720 }), saved);
  assert.deepEqual(Object.keys(draft.sizes), [a, b]);
});
test("all scope covers unloaded cards, preserves heights for one-axis edits and removes obsolete overrides for equal sizes", () => {
  const saved = normalizeLayoutConfig({ [a]: { width: 400, height: 500 } });
  const draft = resizeCards(saved, "all", { width: 360 });
  assert.deepEqual(cardSize(draft, a), { width: 360, height: 500 });
  assert.deepEqual(cardSize(draft, c), { width: 360, height: 440 });
  const equal = resizeCards(draft, "all", { width: 9000, height: -10 });
  assert.deepEqual(equal.sizes, {});
  assert.deepEqual(cardSize(equal, c), {
    width: CARD_MAX.width,
    height: CARD_MIN.height,
  });
  assert.deepEqual(cardSize(saved, c), CARD_DEFAULT);
});
test("mixed dimensions are detected without silently choosing one card's height", () => {
  const layout = normalizeLayoutConfig({
    [a]: { width: 400, height: 500 },
    [b]: { width: 400, height: 600 },
  });
  assert.equal(targetSizes(layout, [a, b]).mixedWidth, false);
  assert.equal(targetSizes(layout, [a, b]).mixedHeight, true);
  assert.equal(targetSizes(layout, "all").mixedWidth, true);
  const equal = resizeCards(layout, [a, b], { width: 480, height: 500 });
  assert.equal(targetSizes(equal, [a, b]).mixedHeight, false);
});
test("page sizes stay within the API limit and the last page never overstates results", () => {
  for (const value of [0, -10, 1000, NaN, "50", null])
    assert.equal(normalizePageSize(value), 25);
  for (const size of [10, 25, 50, 100])
    assert.equal(normalizePageSize(size), size);
  assert.deepEqual(pageWindow(3, 25, 57), {
    page: 3,
    pages: 3,
    from: 51,
    to: 57,
    total: 57,
  });
  assert.deepEqual(pageWindow(3, 100, 57), {
    page: 1,
    pages: 1,
    from: 1,
    to: 57,
    total: 57,
  });
  assert.deepEqual(pageWindow(3, 10, 0), {
    page: 1,
    pages: 1,
    from: 0,
    to: 0,
    total: 0,
  });
  assert.deepEqual(pageWindow(NaN, 50, Infinity), {
    page: 1,
    pages: 1,
    from: 0,
    to: 0,
    total: 0,
  });
});
