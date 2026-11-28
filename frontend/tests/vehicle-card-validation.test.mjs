import test from "node:test";
import assert from "node:assert/strict";
import { validateVehicleCardFields as validate } from "../src/features/fleet/model/vehicle-card-validation.ts";

test("vehicle card limits match the API", () => {
  for (const [field, min, max] of [
    ["year", 1900, 2100], ["engine_capacity_cc", 1, 100000], ["power_kw", 1, 10000],
    ["gross_weight_kg", 1, 120000], ["curb_weight_kg", 1, 120000], ["payload_kg", 1, 120000],
    ["passenger_seats", 0, 120], ["axles", 1, 20],
  ]) {
    for (const value of [String(min), String(max), "", null]) assert.deepEqual(validate({ [field]: value }), {});
    for (const value of [min - 1, max + 1]) assert.deepEqual(validate({ [field]: value }), { [field]: "range" });
    for (const value of ["1e3", "1.5"]) assert.deepEqual(validate({ [field]: value }), { [field]: "integer" });
  }
});

test("calendar dates preserve leap days and DST and compare registration order", () => {
  assert.deepEqual(validate({ leasing_buyout_on: "2024-02-29", first_registration_on: "2026-03-29", first_registration_pl_on: "2026-10-25" }), {});
  assert.deepEqual(validate({ first_registration_on: "2026-03-29", first_registration_pl_on: "2026-03-29" }), {});
  assert.deepEqual(validate({ first_registration_on: "2026-10-25", first_registration_pl_on: "2026-03-29" }), { first_registration_pl_on: "registration_order" });
  assert.deepEqual(validate({ leasing_buyout_on: "2026-02-29", first_registration_on: null, first_registration_pl_on: "2026-03-29" }), { leasing_buyout_on: "calendar_date" });
});

test("curb weight and payload may not exceed known gross weight", () => {
  assert.deepEqual(validate({ gross_weight_kg: 4000, curb_weight_kg: 4000, payload_kg: 4001 }), { payload_kg: "exceeds_gross_weight" });
  assert.deepEqual(validate({ gross_weight_kg: null, curb_weight_kg: 4000 }), {});
});
