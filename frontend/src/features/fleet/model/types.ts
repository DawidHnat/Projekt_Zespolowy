import type { Vehicle as ApiVehicle } from "../../../shared/api/generated/contracts";
export type { VehicleStatus, Source, VehicleList, FleetFeature, FleetMap, Summary } from "../../../shared/api/generated/contracts";
import type { VehicleStatus } from "../../../shared/api/generated/contracts";
export type Vehicle = ApiVehicle & {
  // Optional display fields await a separate agreed API increment.
  make?: string | null;
  model?: string | null;
  position_address?: string | null;
};
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
