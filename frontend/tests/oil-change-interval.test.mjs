import assert from "node:assert/strict";
import test from "node:test";
import { calculateOilChangeInterval as calculate } from "../src/features/maintenance/model/oil-change-interval.ts";

const baseline = {
  lastChangeOdometerKm: 100_000,
  currentOdometerKm: 100_000,
  lastChangeDay: "2025-01-01",
  currentDay: "2025-01-01",
};
const boundaries = [[-1, "in_time"], [0, "due"], [1, "overdue"]];

test("fractional odometer values distinguish both sides of the exact threshold", () => {
  for (const [currentOdometerKm, remainingKm, status] of [
    [0.2, 0.1, "in_time"],
    [0.3, 0, "due"],
    [0.4, -0.1, "overdue"],
  ]) {
    const result = calculate({ ...baseline, lastChangeOdometerKm: 0.1, currentOdometerKm, intervalKm: 0.2 });
    assert.deepEqual(result, { remainingKm, remainingDays: 365, status, warnings: [] });
  }
  assert.equal(calculate({ lastChangeOdometerKm: 0.1, currentOdometerKm: 0.3, intervalKm: 0.2 }).status, "due");
});

test("kilometres beyond odometer precision or safe integer units produce warnings", () => {
  for (const currentOdometerKm of [100_000.01, Number.MAX_SAFE_INTEGER, Infinity]) {
    assert.deepEqual(calculate({ ...baseline, currentOdometerKm }).warnings, ["invalid_odometer"]);
  }
  assert.deepEqual(calculate({ ...baseline, intervalKm: 0.01 }).warnings, ["invalid_interval_km"]);
});

test("default distance threshold preserves signed remaining kilometres", () => {
  for (const [offset, status] of boundaries) {
    const result = calculate({ ...baseline, currentOdometerKm: 110_000 + offset });
    assert.deepEqual(result, { remainingKm: 0 - offset, remainingDays: 365, status, warnings: [] });
  }
});

test("default calendar threshold preserves signed remaining days", () => {
  for (const [index, currentDay] of ["2025-12-31", "2026-01-01", "2026-01-02"].entries()) {
    const result = calculate({ ...baseline, currentDay });
    assert.equal(result.remainingDays, 1 - index);
    assert.equal(result.status, boundaries[index][1]);
  }
});

test("custom intervals prioritize the first reached threshold or an overdue threshold", () => {
  const input = { ...baseline, intervalKm: 500, intervalDays: 10, currentOdometerKm: 100_500 };
  assert.equal(calculate(input).status, "due");
  assert.deepEqual(calculate({ ...input, currentDay: "2025-01-12" }), {
    remainingKm: 0, remainingDays: -1, status: "overdue", warnings: [],
  });
});

test("missing data stays unknown, but a known due date or distance still applies", () => {
  assert.deepEqual(calculate({}), {
    remainingKm: null, remainingDays: null, status: "insufficient_data", warnings: [],
  });
  assert.equal(calculate({ ...baseline, currentDay: null }).status, "insufficient_data");
  assert.equal(calculate({ ...baseline, currentOdometerKm: 110_000, currentDay: null }).status, "due");
  assert.equal(calculate({ ...baseline, currentOdometerKm: null, currentDay: "2026-01-02" }).status, "overdue");
  assert.equal(calculate({ lastChangeOdometerKm: 0, currentOdometerKm: 0 }).remainingKm, 10_000);
});

test("invalid data reports a warning without suppressing the valid dimension", () => {
  assert.deepEqual(calculate({ ...baseline, intervalKm: 0, intervalDays: 1.5 }).warnings, [
    "invalid_interval_km", "invalid_interval_days",
  ]);
  assert.deepEqual(calculate({ ...baseline, currentOdometerKm: 99_999, currentDay: "2026-01-01" }), {
    remainingKm: null, remainingDays: 0, status: "due", warnings: ["odometer_before_last_change"],
  });
  assert.deepEqual(calculate({ ...baseline, currentOdometerKm: NaN, currentDay: "2025-02-29" }).warnings, [
    "invalid_odometer", "invalid_calendar_day",
  ]);
  assert.deepEqual(calculate({ ...baseline, currentDay: "2024-12-31" }).warnings, ["day_before_last_change"]);
});

test("leap day and both Warsaw DST transitions count calendar days", () => {
  for (const [lastChangeDay, currentDay] of [
    ["2024-02-28", "2024-03-01"],
    ["2026-03-28", "2026-03-30"],
    ["2026-10-24", "2026-10-26"],
  ]) {
    const result = calculate({ ...baseline, lastChangeDay, currentDay, intervalDays: 2 });
    assert.equal(result.remainingDays, 0);
    assert.equal(result.status, "due");
  }
});
