import { test } from "node:test";
import assert from "node:assert/strict";
import { parsePreferences, defaultPreferences } from "../src/app/preference-model.ts";
import { defaultBackground, normalizeBackground, validateImageFile, fitImage, MAX_IMAGE_BYTES } from "../src/features/dashboard/model/background-model.ts";

test("older preferences gain a default background without changing the saved view", () => {
  const previous = defaultPreferences();
  delete previous.background;
  previous.theme = "dark";
  previous.material = "solid";
  previous.visibleWidgets = ["map", "vehicles"];
  const restored = parsePreferences(JSON.stringify(previous));
  assert.deepEqual(restored.background, defaultBackground());
  delete restored.background;
  assert.deepEqual(restored, previous);
});
test("background preferences round-trip and reject URLs or unbounded effects", () => {
  const background = { kind: "custom", preset: "mountains", veil: 41, blur: 6, customId: "88935421-6728-4cda-873a-d038a3e88e40" };
  assert.deepEqual(parsePreferences(JSON.stringify({ background })).background, background);
  assert.deepEqual(normalizeBackground({ kind: "url(https://foreign.example/image)", preset: "foreign", veil: 900, blur: -50, customId: "https://foreign.example/secret", image: "injected" }), {
    ...defaultBackground(), veil: 70, blur: 0,
  });
  assert.deepEqual(normalizeBackground({ veil: "50", blur: Infinity }), defaultBackground());
  assert.deepEqual(normalizeBackground(null), defaultBackground());
});
test("uploads reject unsupported, empty, and oversized files before decoding", () => {
  for (const type of ["image/svg+xml", "image/gif", "text/html", ""])
    assert.throws(() => validateImageFile({ type, size: 1234 }), /JPG, PNG lub WebP/);
  assert.throws(() => validateImageFile({ type: "image/jpeg", size: 0 }), /10 MB/);
  assert.throws(() => validateImageFile({ type: "image/png", size: MAX_IMAGE_BYTES + 1 }), /10 MB/);
  for (const type of ["image/jpeg", "image/png", "image/webp"])
    assert.doesNotThrow(() => validateImageFile({ type, size: MAX_IMAGE_BYTES }));
});
test("image preparation bounds memory and preserves portrait and landscape proportions", () => {
  assert.deepEqual(fitImage(6000, 4000), { width: 2560, height: 1707 });
  assert.deepEqual(fitImage(4000, 6000), { width: 1707, height: 2560 });
  assert.deepEqual(fitImage(960, 640), { width: 960, height: 640 });
  for (const [width, height] of [[10000, 10000], [0, 100], [NaN, 100], [100, Infinity]])
    assert.throws(() => fitImage(width, height), /40 megapikseli/);
});
