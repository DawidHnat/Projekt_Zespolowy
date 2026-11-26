import type { Vehicle as ApiVehicle } from "../../../shared/api/generated/contracts";
export type { VehicleStatus, Source, VehicleList, FleetFeature, FleetMap, Summary } from "../../../shared/api/generated/contracts";
import type { VehicleStatus } from "../../../shared/api/generated/contracts";
export type Vehicle = ApiVehicle & {
  // Optional display fields await a separate agreed API increment.
  make?: string | null;
  model?: string | null;
  year?: number | null;
  vin?: string | null;
  ownership_category?: "Firmowe" | "Prywatne" | "Leasing" | null;
  purchase_date?: string | null;
  first_registration?: string | null;
  first_registration_poland?: string | null;
  fuel_type?: string | null;
  engine_capacity_cc?: number | null;
  power_kw?: number | null;
  dmc_kg?: number | null;
  curb_weight_kg?: number | null;
  payload_kg?: number | null;
  seats?: number | null;
  axles?: number | null;
  position_address?: string | null;
};
export function fleetPollInterval(value: string | undefined) {
  const milliseconds = Number(value);
  return Number.isSafeInteger(milliseconds) &&
    milliseconds >= 10000 &&
    milliseconds <= 86400000
    ? milliseconds
    : 10000;
}
export const statusLabels: Record<VehicleStatus, string> = {
  moving: "W ruchu",
  stopped: "Postój",
  offline: "Ostatni znany stan",
  unknown: "Brak pomiaru",
};
export function positionTime(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("pl-PL", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Europe/Warsaw",
      }).format(new Date(value))
    : "Brak pomiaru";
}
export function updateTime(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("pl-PL", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Europe/Warsaw",
      }).format(new Date(value))
    : "Brak udanej synchronizacji";
}
export function positionAge(value: string | null, now = Date.now()) {
  const time = value ? Date.parse(value) : NaN;
  if (!Number.isFinite(time)) return "Brak czasu pozycji";
  const age = now - time;
  if (age < 0) return "Czas pozycji w przyszłości";
  if (age < 60000) return "Pozycja przed chwilą";
  if (age < 3600000) return `Pozycja sprzed ${Math.floor(age / 60000)} min`;
  if (age < 86400000) return `Pozycja sprzed ${Math.floor(age / 3600000)} godz.`;
  return `Pozycja · ${updateTime(value)}`;
}
export function positionCoordinates(
  latitude: number | null,
  longitude: number | null,
) {
  if (
    latitude === null ||
    longitude === null ||
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude) ||
    latitude < -90 ||
    latitude > 90 ||
    longitude < -180 ||
    longitude > 180
  ) {
    return "Brak GPS";
  }
  return `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
}
export function measurementLabel(
  value: number | null,
  unit: string,
  maximumFractionDigits = 1,
) {
  if (value === null || !Number.isFinite(value) || value < 0) {
    return "Brak danych";
  }
  return `${value.toLocaleString("pl-PL", { maximumFractionDigits })} ${unit}`;
}
