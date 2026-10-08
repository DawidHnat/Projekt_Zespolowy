import type { WidgetId } from "./widget-types.ts";

export const GRID = { columns: 12, rowHeight: 18, gap: 16, precision: 2 } as const;
const rowStep = GRID.rowHeight + GRID.gap;
const roundUp = (value: number) => Math.ceil(value * GRID.precision) / GRID.precision;

export const heightPixels = (h: number) => h * rowStep - GRID.gap;
export const heightUnits = (pixels: number) => roundUp((pixels + GRID.gap) / rowStep);
export const widthPixels = (w: number, container: number) =>
  (container + GRID.gap) / GRID.columns * w - GRID.gap;
export const widthUnits = (pixels: number, container: number) =>
  roundUp((pixels + GRID.gap) / (container + GRID.gap) * GRID.columns);

// Budgets include the heading, static information, and room for at least one
// record. Intrinsic DOM measurements can raise these minima when content wraps.
export const minimumWidth: Record<WidgetId, number> = {
  metrics: 320,
  map: 280,
  activity: 260,
  vehicles: 360,
  utilization: 260,
  trips: 280,
};
export function minimumHeight(id: WidgetId, width: number): number {
  switch (id) {
    case "metrics":
      // RGL rounds rendered pixels; match the inclusive CSS container breakpoint.
      return Math.round(width) <= 650 ? 248 : 148;
    case "map":
      return 310;
    case "activity":
      return 340;
    case "vehicles":
      return 280;
    case "utilization":
      return width < 280 ? 310 : 250;
    case "trips":
      return width < 600 ? 230 : 170;
  }
}
