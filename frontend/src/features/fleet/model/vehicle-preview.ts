import type { Vehicle } from "./types.ts";

type PreviewVehicle = Pick<
  Vehicle,
  "name" | "make" | "model" | "license_plate" | "number" |
  "position_address" | "latitude" | "longitude" | "status" | "is_stale" | "speed_kmh"
>;
const text = (value: string | null | undefined) => value?.trim() || "";

export function vehiclePreview(vehicle: PreviewVehicle) {
  const makeModel = [text(vehicle.make), text(vehicle.model)].filter(Boolean).join(" ");
  const located = Number.isFinite(vehicle.latitude) && Number.isFinite(vehicle.longitude)
    && Math.abs(vehicle.latitude!) <= 90 && Math.abs(vehicle.longitude!) <= 180;
  const moving = vehicle.status === "moving" && !vehicle.is_stale;
  return {
    title: makeModel || vehicle.name,
    subtitle: makeModel
      ? text(vehicle.license_plate) || text(vehicle.number) || vehicle.name
      : "Marka i model: brak danych",
    address: located
      ? text(vehicle.position_address) || "Adres niedostępny"
      : "Brak pozycji GPS",
    locationLabel: vehicle.is_stale ? "Ostatnia lokalizacja" : "Lokalizacja",
    moving,
    speed: moving && typeof vehicle.speed_kmh === "number"
      && Number.isFinite(vehicle.speed_kmh) && vehicle.speed_kmh >= 0
      ? new Intl.NumberFormat("pl-PL", { maximumFractionDigits: 0 }).format(vehicle.speed_kmh)
      : null,
  };
}
