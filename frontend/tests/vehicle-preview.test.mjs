import test from "node:test";
import assert from "node:assert/strict";
import { vehiclePreview } from "../src/features/fleet/model/vehicle-preview.ts";

const vehicle = {
  name: "Pojazd testowy", license_plate: "TEST 001", number: null,
  latitude: 0, longitude: 0, status: "moving", is_stale: false, speed_kmh: null,
};

test("preview accepts future identity and address without inventing missing data", () => {
  const empty = vehiclePreview(vehicle);
  assert.equal(empty.title, "Pojazd testowy");
  assert.equal(empty.subtitle, "Marka i model: brak danych");
  assert.equal(empty.address, "Adres niedostępny");
  assert.equal(empty.speed, null);
  const complete = vehiclePreview({ ...vehicle, make: " Marka ", model: " Model ", position_address: " Adres testowy ", speed_kmh: 42.4 });
  assert.equal(complete.title, "Marka Model");
  assert.equal(complete.subtitle, "TEST 001");
  assert.equal(complete.address, "Adres testowy");
  assert.equal(complete.speed, "42");
});

test("stopped, stale or invalid telemetry never appears as current driving speed", () => {
  for (const change of [{ status: "stopped" }, { status: "offline" }, { is_stale: true }, { speed_kmh: -1 }, { speed_kmh: NaN }, { speed_kmh: Infinity }]) {
    assert.equal(vehiclePreview({ ...vehicle, speed_kmh: 50, ...change }).speed, null);
  }
  assert.equal(vehiclePreview({ ...vehicle, speed_kmh: 0 }).speed, "0");
  assert.equal(vehiclePreview({ ...vehicle, is_stale: true }).locationLabel, "Ostatnia lokalizacja");
});

test("an address without a valid GPS position is not presented as the vehicle location", () => {
  for (const change of [{ latitude: null }, { longitude: null }, { latitude: 91 }, { longitude: 181 }, { latitude: NaN }]) {
    assert.equal(vehiclePreview({ ...vehicle, position_address: "Adres testowy", ...change }).address, "Brak pozycji GPS");
  }
});
