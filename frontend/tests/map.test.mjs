import { test } from "node:test";
import assert from "node:assert/strict";
import {
  validFeatures,
  boundsForFeatures,
  mapEmptyState,
} from "../src/features/fleet/model/map-model.ts";
const feature = (id, lng, lat) => ({
  type: "Feature",
  properties: { id },
  geometry: { type: "Point", coordinates: [lng, lat] },
});
test("map distinguishes an unavailable source from missing GPS and preserves cached positions", () => {
  const error = "Oczekiwanie na pierwszy odczyt WEBFLEET.";
  assert.equal(mapEmptyState(null, false, error, false)?.title, "Dane floty niedostępne");
  assert.equal(mapEmptyState(null, false, error, false)?.action, "retry");
  assert.equal(mapEmptyState(null, true, null, false)?.title, "Pobieranie pojazdów…");
  assert.equal(mapEmptyState(null, false, null, false)?.title, "Oczekiwanie na dane floty");
  assert.equal(mapEmptyState({ total: 2, features: [] }, false, null, false)?.title, "Brak pozycji GPS");
  assert.equal(mapEmptyState({ total: 0, features: [] }, false, null, false)?.title, "Flota jest pusta");
  assert.equal(mapEmptyState({ total: 0, features: [] }, false, null, true)?.action, "clear");
  assert.equal(mapEmptyState({ total: 1, features: [feature("cached", 21, 52)] }, false, error, false), null);
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
