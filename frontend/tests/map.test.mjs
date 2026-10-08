import { test } from "node:test";
import assert from "node:assert/strict";
import {
  validFeatures,
  boundsForFeatures,
} from "../src/features/fleet/model/map-model.ts";
const feature = (id, lng, lat) => ({
  type: "Feature",
  properties: { id },
  geometry: { type: "Point", coordinates: [lng, lat] },
});
test("map excludes invalid GPS but accepts the valid zero coordinate", () => {
  const data = {
    features: [
      feature("zero", 0, 0),
      feature("bad", 181, 52),
      feature("nan", 21, NaN),
      feature("ok", 21, 52),
    ],
  };
  assert.deepEqual(
    validFeatures(data).map((f) => f.properties.id),
    ["zero", "ok"],
  );
  assert.deepEqual(boundsForFeatures(validFeatures(data)), [
    [0, 0],
    [21, 52],
  ]);
  assert.equal(boundsForFeatures([]), null);
});
test("filter changes recompute bounds from the matching fleet only", () => {
  const all = [feature("one", 20, 50), feature("two", 22, 54)];
  assert.deepEqual(boundsForFeatures(all), [
    [20, 50],
    [22, 54],
  ]);
  assert.deepEqual(
    boundsForFeatures(all.filter((f) => f.properties.id === "two")),
    [
      [22, 54],
      [22, 54],
    ],
  );
});
