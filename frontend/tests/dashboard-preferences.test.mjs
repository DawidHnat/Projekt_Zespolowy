import { test } from "node:test";
import assert from "node:assert/strict";
import { collides } from "react-grid-layout/core";
import {
  parsePreferences,
  defaultPreferences,
} from "../src/app/preference-model.ts";
import {
  changeWidget,
  defaultLayout,
  mergeLayout,
  normalizeLayout,
  visibleLayout,
  columns,
  fitLayout,
  toGridLayout,
  fromGridLayout,
  SECTION_IDS,
  PROFILES,
  SECTION_WIDGETS,
} from "../src/features/dashboard/model/widget-layout.ts";

import { GRID, heightPixels, minimumHeight, minimumWidth, widthPixels } from "../src/features/dashboard/model/widget-sizing.ts";

function assertSafe(layout, profile) {
  for (const item of layout) {
    assert.ok(Number.isInteger(item.x * 2) && Number.isInteger(item.y * 2));
    assert.ok(
      item.x >= 0 && item.y >= 0 && item.x + item.w <= columns(profile),
    );
    assert.ok(
      item.w >= item.minW && item.h >= item.minH && item.h <= item.maxH,
    );
    for (const other of layout)
      if (other.i !== item.i) assert.equal(collides(item, other), false);
  }
}

test("v1 migration preserves theme, accent and an intentionally empty dashboard", () => {
  const result = parsePreferences(
    JSON.stringify({ theme: "dark", accent: "#aa33cc", visibleWidgets: [] }),
  );
  assert.equal(result.theme, "dark");
  assert.equal(result.accent, "#aa33cc");
  assert.deepEqual(result.visibleWidgets, []);
  assert.equal(result.material, "glass");
  assert.deepEqual(result.layouts, defaultPreferences().layouts);
});
test("corrupt preferences recover and unknown or duplicate widget IDs are discarded", () => {
  assert.deepEqual(parsePreferences("{broken"), defaultPreferences());
  const result = parsePreferences(
    JSON.stringify({
      theme: "invalid",
      accent: "url(secret)",
      visibleWidgets: ["map", "map", "foreign"],
      material: "solid",
    }),
  );
  assert.equal(result.theme, "light");
  assert.equal(result.accent, "#1479e8");
  assert.equal(result.material, "solid");
  assert.deepEqual(result.visibleWidgets, ["map"]);
});
test("all default views fit both screen profiles without overlaps", () => {
  for (const section of SECTION_IDS)
    for (const profile of PROFILES)
      assertSafe(
        visibleLayout(
          defaultLayout(section, profile),
          SECTION_WIDGETS[section],
          profile,
        ),
        profile,
      );
});
test("stored layouts cannot bypass constraints or inject unknown grid items", () => {
  for (const profile of PROFILES) {
    const normalized = normalizeLayout("dashboard", profile, [
      { i: "map", x: -100, y: -12, w: 10000, h: 0, static: true, minW: 99 },
      { i: "map", x: 1, y: 1, w: 1, h: 1 },
      { i: "metrics", x: "bad", y: null, w: -10, h: 300 },
      { i: "foreign", x: 0, y: 0, w: 12, h: 500 },
    ]);
    assert.deepEqual(
      normalized.map((item) => item.i),
      [...SECTION_WIDGETS.dashboard],
    );
    assert.equal(normalized.find((item) => item.i === "map").static, undefined);
    assertSafe(
      visibleLayout(normalized, SECTION_WIDGETS.dashboard, profile),
      profile,
    );
  }
});
test("reordering and resizing resolve collisions and preserve the input", () => {
  for (const profile of PROFILES) {
    const original = defaultLayout("dashboard", profile);
    const snapshot = JSON.stringify(original);
    const moved = changeWidget(original, "activity", profile, { x: 0, y: 0 });
    const resized = changeWidget(moved, "map", profile, { w: 12, h: 20 });
    assertSafe(resized, profile);
    assert.equal(JSON.stringify(original), snapshot);
    assert.equal(resized.find((item) => item.i === "map").w, columns(profile));
    assert.equal(resized.find((item) => item.i === "map").h, 20);
  }
});
test("a hidden widget keeps its size and cannot displace the saved view on reload", () => {
  const original = defaultPreferences();
  original.visibleWidgets = ["map"];
  const displayed = visibleLayout(
    original.layouts.dashboard.desktop,
    original.visibleWidgets,
    "desktop",
  );
  const changed = changeWidget(displayed, "map", "desktop", { w: 12, h: 17 });
  const merged = mergeLayout(
    original.layouts.dashboard.desktop,
    changed,
    "desktop",
  );
  assert.deepEqual(
    merged.find((item) => item.i === "activity"),
    original.layouts.dashboard.desktop.find((item) => item.i === "activity"),
  );
  const saved = {
    ...original,
    layouts: {
      ...original.layouts,
      dashboard: { ...original.layouts.dashboard, desktop: merged },
    },
  };
  const loaded = parsePreferences(JSON.stringify(saved));
  assert.deepEqual(
    visibleLayout(
      loaded.layouts.dashboard.desktop,
      loaded.visibleWidgets,
      "desktop",
    ),
    changed,
  );
  assert.deepEqual(
    loaded.layouts.dashboard.compact,
    original.layouts.dashboard.compact,
  );
  assert.deepEqual(loaded.layouts.fleet, original.layouts.fleet);
  assertSafe(
    visibleLayout(
      loaded.layouts.dashboard.desktop,
      SECTION_WIDGETS.dashboard,
      "desktop",
    ),
    "desktop",
  );
});
test("narrow metrics gain enough height and compact widgets stay full width", () => {
  const desktop = changeWidget(
    defaultLayout("dashboard", "desktop"),
    "metrics",
    "desktop",
    { w: 6, h: 1 },
  );
  assert.equal(desktop.find((item) => item.i === "metrics").h, 8);
  const compact = changeWidget(
    defaultLayout("dashboard", "compact"),
    "map",
    "compact",
    { w: 12, x: 9 },
  );
  assert.equal(compact.find((item) => item.i === "map").w, 1);
  assert.equal(compact.find((item) => item.i === "map").x, 0);
});


test("a finer interaction grid preserves geometry and half-unit sizes survive a reload", () => {
  const original = defaultLayout("dashboard", "desktop");
  const changed = changeWidget(original, "map", "desktop", { w: 8.5, h: 11.5 });
  const rendered = toGridLayout(changed);
  assert.deepEqual(fromGridLayout(rendered), changed);
  for (const item of rendered) {
    assert.equal(item.h * ((GRID.rowHeight + GRID.gap) / GRID.precision) - GRID.gap, heightPixels(item.h / GRID.precision));
    assert.equal((971 + GRID.gap) / (GRID.columns * GRID.precision) * item.w - GRID.gap, widthPixels(item.w / GRID.precision, 971));
  }
  const prefs = defaultPreferences();
  prefs.layouts.dashboard.desktop = changed;
  const loaded = parsePreferences(JSON.stringify(prefs));
  assert.deepEqual(loaded.layouts.dashboard.desktop, normalizeLayout("dashboard", "desktop", changed));
  assertSafe(changed, "desktop");
});
test("every widget fits its content budget at narrow and wide viewport sizes", () => {
  for (const width of [288, 343, 491, 720, 971, 1360]) {
    const profile = width < 720 ? "compact" : "desktop";
    const original = defaultLayout("dashboard", profile);
    const snapshot = JSON.stringify(original);
    // Ask for the smallest possible size, as a corner dragged past its bounds would.
    let small = original;
    for (const id of SECTION_WIDGETS.dashboard)
      small = changeWidget(small, id, profile, { w: 0, h: 0 });
    const fitted = fitLayout(small, profile, width);
    assertSafe(fitted, profile);
    assert.equal(JSON.stringify(original), snapshot);
    for (const item of fitted) {
      const pixels = profile === "compact" ? width : widthPixels(item.w, width);
      assert.ok(heightPixels(item.h) >= minimumHeight(item.i, pixels), `${item.i} at ${width}px`);
      if (profile === "desktop") assert.ok(pixels >= minimumWidth[item.i]);
    }
  }
});
test("wrapped content or a tall first record raises only the affected widget minimum", () => {
  const original = defaultLayout("dashboard", "desktop");
  const baseline = fitLayout(original, "desktop", 971);
  const fitted = fitLayout(original, "desktop", 971, { vehicles: 900 });
  const vehicles = fitted.find(item => item.i === "vehicles");
  assert.ok(heightPixels(vehicles.minH) >= 900);
  for (const item of fitted) {
    if (item.i !== "vehicles") assert.equal(item.minH, baseline.find(other => other.i === item.i).minH);
  }
  assertSafe(fitted, "desktop");
});
test("metrics and trip minima follow wrapping at their width breakpoints", () => {
  assert.ok(minimumHeight("metrics", 649) > minimumHeight("metrics", 651));
  assert.equal(minimumHeight("metrics", 650.4), minimumHeight("metrics", 649));
  assert.ok(minimumHeight("trips", 599) > minimumHeight("trips", 601));
});
