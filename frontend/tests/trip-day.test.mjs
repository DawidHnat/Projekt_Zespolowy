import test from "node:test";
import assert from "node:assert/strict";
import { warsawDay, previousDay, validTripDay, tripDayLabel } from "../src/features/trips/model/trip-day.ts";

test("trip days use Polish midnight and seasonal UTC offsets", () => {
  assert.equal(warsawDay(new Date("2026-10-08T22:30:00Z")), "2026-10-09");
  assert.equal(warsawDay(new Date("2026-01-08T22:30:00Z")), "2026-01-08");
  assert.equal(warsawDay(new Date("2026-01-08T23:30:00Z")), "2026-01-09");
});

test("previous calendar day crosses DST, leap days and years without a 24-hour assumption", () => {
  assert.equal(previousDay("2026-03-30"), "2026-03-29");
  assert.equal(previousDay("2026-10-26"), "2026-10-25");
  assert.equal(previousDay("2024-03-01"), "2024-02-29");
  assert.equal(previousDay("2026-01-01"), "2025-12-31");
});

test("impossible and malformed dates cannot become a history filter", () => {
  for (const day of ["", "2026-02-29", "2026-02-31", "2026-13-01", "2026-1-1", "invalid"]) {
    assert.equal(validTripDay(day), false);
  }
  assert.equal(validTripDay("2024-02-29"), true);
  assert.equal(tripDayLabel("2026-10-09", "2026-10-09"), "Dzisiaj");
  assert.equal(tripDayLabel("2026-10-08", "2026-10-09"), "Wczoraj");
});
