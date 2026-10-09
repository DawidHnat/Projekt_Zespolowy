import { test } from "node:test";
import assert from "node:assert/strict";
import {
  normalizeVehicleLayout,
  resizeCard,
  CARD_MIN,
  CARD_MAX,
} from "../src/features/fleet/model/vehicle-layout.ts";
import { vehiclesAtPoint } from "../src/features/fleet/model/marker-model.ts";
import { fitImage } from "../src/shared/media/image-model.ts";

const a = "00000000-0000-4000-8000-000000000001";
const b = "00000000-0000-4000-8000-000000000002";
test("saved card sizes are bounded and reject unknown keys or malformed storage", () => {
  assert.deepEqual(normalizeVehicleLayout(null), {});
  assert.deepEqual(normalizeVehicleLayout([]), {});
  const layout = normalizeVehicleLayout({
    [a]: { width: -1, height: 9000 },
    [b]: { width: NaN, height: "500" },
    unknown: { width: 600, height: 500 },
    constructor: {},
  });
  assert.deepEqual(layout[a], {
    width: CARD_MIN.width,
    height: CARD_MAX.height,
  });
  assert.deepEqual(Object.keys(layout), [a, b]);
  assert.deepEqual(
    normalizeVehicleLayout(JSON.parse(JSON.stringify(layout))),
    layout,
  );
});
test("resizing one vehicle never changes another or mutates the saved layout", () => {
  const saved = {
    [a]: { width: 320, height: 440 },
    [b]: { width: 280, height: 420 },
  };
  const draft = resizeCard(saved, a, { width: 500, height: 600 });
  assert.deepEqual(draft[b], saved[b]);
  assert.deepEqual(saved[a], { width: 320, height: 440 });
  assert.deepEqual(
    resizeCard(draft, "__proto__", { width: 500, height: 600 }),
    draft,
  );
});
test("overlapping marker hit areas offer individual IDs without merging distant vehicles", () => {
  const points = [
    { id: a, x: 100, y: 100 },
    { id: b, x: 103, y: 101 },
    { id: "far", x: 160, y: 100 },
  ];
  assert.deepEqual(vehiclesAtPoint(points, { x: 100, y: 100 }), [a, b]);
  assert.equal(points.length, 3);
  assert.deepEqual(vehiclesAtPoint(points, { x: 160, y: 100 }), ["far"]);
});
test("vehicle photo preparation uses a smaller image budget without changing wallpaper proportions", () => {
  assert.deepEqual(fitImage(6000, 4000, 1024), { width: 1024, height: 683 });
  assert.deepEqual(fitImage(6000, 4000), { width: 2560, height: 1707 });
});
