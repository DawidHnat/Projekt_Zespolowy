import test from "node:test";
import assert from "node:assert/strict";
import { validateVehicleCardFields as validate } from "../src/features/fleet/model/vehicle-card-validation.ts";

test("nullable fields and zeros follow the API contract", () => {
  assert.deepEqual(validate({ year: "", axles: null, seats: "  ", power_kw: "0", payload_kg: 0 }), {});
  assert.deepEqual(validate({ seats: 0, axles: "0", dmc_kg: 0 }), { seats: "range", axles: "range", dmc_kg: "range" });
});

test("numeric fields reject malformed, fractional and out-of-range values", () => {
  for (const [values, expected] of [
    [{ year: "1900", seats: 100, axles: "20", engine_capacity_cc: "100000" }, {}],
    [{ year: "1899", seats: 101, axles: "21" }, { year: "range", seats: "range", axles: "range" }],
    [{ year: "2101", power_kw: Number.NaN, curb_weight_kg: -1 }, { year: "range", power_kw: "integer", curb_weight_kg: "range" }],
    [{ seats: "2.5", axles: 1.5, payload_kg: "1e3" }, { seats: "integer", axles: "integer", payload_kg: "integer" }],
  ]) assert.deepEqual(validate(values), expected);
});

test("calendar dates preserve leap days and DST and compare registration order", () => {
  assert.deepEqual(validate({ purchase_date: "2024-02-29", first_registration: "2026-03-29", first_registration_poland: "2026-10-25" }), {});
  assert.deepEqual(validate({ first_registration: "2026-03-29", first_registration_poland: "2026-03-29" }), {});
  assert.deepEqual(validate({ first_registration: "2026-10-25", first_registration_poland: "2026-03-29" }), { first_registration_poland: "registration_order" });
  assert.deepEqual(validate({ purchase_date: "2026-02-29", first_registration: null, first_registration_poland: "2026-03-29" }), { purchase_date: "calendar_date" });
});
