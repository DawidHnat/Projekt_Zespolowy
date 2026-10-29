export const WIDGET_IDS = [
  "metrics",
  "map",
  "activity",
  "vehicles",
  "utilization",
  "trips",
] as const;
export const DRIVER_WIDGET_IDS = ["driver-active", "driver-unassigned", "driver-missing", "driver-checks"] as const;
export type WidgetId = (typeof WIDGET_IDS)[number] | (typeof DRIVER_WIDGET_IDS)[number];
export type SectionId = "dashboard" | "map" | "fleet" | "trips" | "analytics" | "drivers";
