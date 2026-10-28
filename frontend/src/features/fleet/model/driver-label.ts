import type { Vehicle } from "./types";

export function driverLabel(vehicle: Vehicle): string {
  if ((vehicle.driver_count ?? 0) > 1) return `${vehicle.driver_count} kierowców`;
  return vehicle.driver?.display_name || "Nieprzypisany";
}

export function driverNames(vehicle: Vehicle): string | undefined {
  const preview = vehicle.driver_preview;
  if (!preview?.length) return vehicle.driver?.display_name;
  const names = preview.map(driver => driver.display_name).join(", ");
  return (vehicle.driver_count ?? 0) > preview.length ? `${names} i inni` : names;
}
