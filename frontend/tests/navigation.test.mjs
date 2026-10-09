import { test } from "node:test";
import assert from "node:assert/strict";
import { sectionFromHash } from "../src/app/navigation.ts";

test("page navigation supports direct links and safely falls back for unknown hashes", () => {
  assert.equal(sectionFromHash("#map"), "map");
  assert.equal(sectionFromHash("#vehicles"), "vehicles");
  assert.equal(sectionFromHash("#settings"), "settings");
  assert.equal(sectionFromHash("#fuel-cards"), "fuel-cards");
  for (const hash of [
    "",
    "#",
    "#main-content",
    "#missing",
    "#toString",
    "#__proto__",
  ])
    assert.equal(sectionFromHash(hash), "dashboard");
});

test("saved links to removed navigation sections still open the corresponding workspace", () => {
  assert.equal(sectionFromHash("#fleet"), "map");
  assert.equal(sectionFromHash("#trips"), "mileage");
  assert.equal(sectionFromHash("#analytics"), "dashboard");
  assert.equal(sectionFromHash("#dashboard"), "dashboard");
});
