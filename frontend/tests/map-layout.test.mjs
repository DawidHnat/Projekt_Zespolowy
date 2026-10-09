import { test } from "node:test";
import assert from "node:assert/strict";
import { defaultPreferences, parsePreferences } from "../src/app/preference-model.ts";
import { createLayoutDraft, commitLayoutDraft } from "../src/app/layout-draft.ts";
import { changeWidget, defaultLayout, normalizeLayout } from "../src/features/dashboard/model/widget-layout.ts";

const geometry = layout => layout.map(({ i, x, y, w, h }) => ({ i, x, y, w, h }));

test("older saved layouts gain a separate Map without resetting existing views", () => {
  const saved = defaultPreferences();
  delete saved.layouts.map;
  saved.layouts.dashboard.desktop = changeWidget(saved.layouts.dashboard.desktop, "map", "desktop", { w: 10 });
  const loaded = parsePreferences(JSON.stringify(saved));
  assert.deepEqual(loaded.layouts.map.desktop, defaultLayout("map", "desktop"));
  assert.deepEqual(geometry(loaded.layouts.dashboard.desktop), geometry(saved.layouts.dashboard.desktop));
  assert.deepEqual(loaded.layouts.fleet, saved.layouts.fleet);
});

test("a narrow vehicle sidebar survives saving without relaxing the Pulpit table minimum", () => {
  const saved = defaultPreferences();
  saved.layouts.map.desktop = changeWidget(saved.layouts.map.desktop, "vehicles", "desktop", { w: 3.5, h: 10.5 }, "map");
  const loaded = parsePreferences(JSON.stringify(saved));
  assert.deepEqual(geometry(loaded.layouts.map.desktop), geometry(saved.layouts.map.desktop));
  assert.deepEqual(loaded.layouts.map.compact, saved.layouts.map.compact);
  assert.equal(loaded.layouts.map.desktop.find(item => item.i === "vehicles").w, 3.5);
  const invalid = [{ i: "vehicles", x: -9, y: -1, w: 0, h: 0, static: true }];
  assert.equal(normalizeLayout("dashboard", "desktop", invalid).find(item => item.i === "vehicles").minW, 6);
  assert.equal(normalizeLayout("map", "desktop", invalid).find(item => item.i === "vehicles").minW, 3);
});

test("saving one view cannot commit or overwrite the other view's pending draft", () => {
  const original = defaultPreferences();
  const before = structuredClone(original);
  const pulpit = createLayoutDraft(original, "dashboard");
  const map = createLayoutDraft(original, "map");
  pulpit.visibleWidgets = ["metrics"];
  pulpit.layouts.desktop = changeWidget(pulpit.layouts.desktop, "metrics", "desktop", { w: 6 });
  map.layouts.desktop = changeWidget(map.layouts.desktop, "vehicles", "desktop", { w: 3.5 }, "map");
  const first = commitLayoutDraft({ ...original, theme: "dark" }, "map", map);
  assert.deepEqual(first.visibleWidgets, original.visibleWidgets);
  assert.deepEqual(first.layouts.dashboard, original.layouts.dashboard);
  const second = commitLayoutDraft(first, "dashboard", pulpit);
  assert.deepEqual(second.layouts.map, first.layouts.map);
  assert.deepEqual(second.visibleWidgets, ["metrics"]);
  assert.equal(second.theme, "dark");
  assert.deepEqual(original, before);
});
