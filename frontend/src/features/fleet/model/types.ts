export type VehicleStatus = "moving" | "stopped" | "offline" | "unknown";
export type Vehicle = {
  id: string;
  name: string;
  number: string | null;
  license_plate: string | null;
  vehicle_type: string | null;
  // Optional display fields for the next API increment; absent values stay unknown.
  make?: string | null;
  model?: string | null;
  year?: number | null;
  vin?: string | null;
  position_address?: string | null;
  status: VehicleStatus;
  driver: { id: string; display_name: string } | null;
  latitude: number | null;
  longitude: number | null;
  position_at: string | null;
  received_at: string | null;
  is_stale: boolean;
  odometer_km: number | null;
  speed_kmh: number | null;
  ignition_on: boolean | null;
  standing_still: boolean | null;
};
export type Source = {
  status: "ok" | "degraded";
  last_success_at: string | null;
  error_code: string | null;
};
export type VehicleList = {
  items: Vehicle[];
  total: number;
  page: number;
  page_size: number;
  source: Source;
};
export type FleetFeature = {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: {
    id: string;
    name: string;
    status: VehicleStatus;
    is_stale: boolean;
    position_at: string | null;
  };
};
export type FleetMap = {
  type: "FeatureCollection";
  features: FleetFeature[];
  located: number;
  total: number;
  source: Source;
};
export type Summary = {
  total: number;
  moving: number;
  stopped: number;
  offline: number;
  unknown: number;
  source: Source;
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
  offline: "Dane nieaktualne",
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
