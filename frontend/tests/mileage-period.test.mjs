import test from "node:test";
import assert from "node:assert/strict";
import { MAX_PERIOD_DAYS, initialPeriod, periodDays, periodError } from "../src/features/trips/model/mileage-period.ts";

test("initial period uses the Warsaw calendar day, not the UTC or locale layout", () => {
  // 23:30 UTC on 30 Nov is already 1 Dec in Warsaw.
  assert.deepEqual(initialPeriod(new Date("2026-11-30T23:30:00Z")), { from: "2026-12-01", through: "2026-12-01" });
  assert.deepEqual(initialPeriod(new Date("2026-11-27T10:00:00Z")), { from: "2026-11-01", through: "2026-11-27" });
  // Summer time: 22:30 UTC on 31 Mar is 00:30 on 1 Apr in Warsaw.
  assert.deepEqual(initialPeriod(new Date("2026-03-31T22:30:00Z")), { from: "2026-04-01", through: "2026-04-01" });
});

test("period length is inclusive and the backend limit is 93 days", () => {
  assert.equal(MAX_PERIOD_DAYS, 93);
  assert.equal(periodDays("2026-11-01", "2026-11-01"), 1);
  assert.equal(periodDays("2026-03-28", "2026-03-30"), 3); // across the DST change
  assert.equal(periodDays("2026-01-01", "2026-04-03"), 93);
  assert.equal(periodError("2026-01-01", "2026-04-03"), "");
  assert.equal(periodDays("2026-01-01", "2026-04-04"), 94);
  assert.match(periodError("2026-01-01", "2026-04-04"), /najwyżej 93 dni \(wybrano 94\)/);
});

test("invalid or reversed periods get a readable message", () => {
  assert.match(periodError("2026-11-10", "2026-11-09"), /nie może być późniejsza/);
  assert.match(periodError("2026-02-30", "2026-03-01"), /prawidłowe daty/);
  assert.equal(periodDays("", "2026-03-01"), null);
});
