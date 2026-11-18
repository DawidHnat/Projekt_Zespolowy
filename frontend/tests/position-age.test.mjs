import test from "node:test";
import assert from "node:assert/strict";
import { positionAge } from "../src/features/fleet/model/types.ts";

const now = Date.parse("2026-11-18T12:00:00Z");
const at = age => new Date(now - age).toISOString();

test("position age follows the GPS measurement even after a recent cache sync", () => {
  assert.equal(positionAge(at(59_999), now), "Pozycja przed chwilą");
  assert.equal(positionAge(at(60_000), now), "Pozycja sprzed 1 min");
  assert.equal(positionAge(at(15 * 60_000), now), "Pozycja sprzed 15 min");
  assert.equal(positionAge(at(3_600_000), now), "Pozycja sprzed 1 godz.");
  assert.match(positionAge(at(86_400_000), now), /17\.11\.2026.*13:00/);
});

test("missing, invalid and future timestamps do not appear as a fresh position", () => {
  assert.equal(positionAge(null, now), "Brak czasu pozycji");
  assert.equal(positionAge("invalid", now), "Brak czasu pozycji");
  assert.equal(positionAge(at(-60_000), now), "Czas pozycji w przyszłości");
});
