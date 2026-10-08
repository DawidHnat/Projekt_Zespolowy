export const WIDGET_IDS = [
  "metrics",
  "map",
  "activity",
  "vehicles",
  "utilization",
  "trips",
] as const;
export type WidgetId = (typeof WIDGET_IDS)[number];
export type SectionId = "dashboard" | "map" | "fleet" | "trips" | "analytics";
