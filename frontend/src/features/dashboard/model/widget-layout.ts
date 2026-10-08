import {
  moveElement,
  verticalCompactor,
  type Layout,
  type LayoutItem,
} from "react-grid-layout/core";
import {
  GRID,
  heightUnits,
  widthUnits,
  widthPixels,
  minimumWidth,
  minimumHeight,
} from "./widget-sizing.ts";
import { WIDGET_IDS, type SectionId, type WidgetId } from "./widget-types.ts";

export const SECTION_IDS = [
  "dashboard",
  "fleet",
  "trips",
  "analytics",
] as const;
export const PROFILES = ["desktop", "compact"] as const;
export type LayoutProfile = (typeof PROFILES)[number];
export type SavedLayouts = Record<SectionId, Record<LayoutProfile, Layout>>;
export const SECTION_WIDGETS: Record<SectionId, readonly WidgetId[]> = {
  dashboard: WIDGET_IDS,
  fleet: ["metrics", "map", "vehicles"],
  trips: ["trips"],
  analytics: ["metrics", "activity", "utilization"],
};
export const columns = (profile: LayoutProfile) =>
  profile === "desktop" ? 12 : 1;
const sizes: Record<
  WidgetId,
  { w: number; h: number; minW: number; minH: number }
> = {
  metrics: { w: 12, h: 5, minW: 6, minH: 5 },
  map: { w: 8, h: 11, minW: 4, minH: 10 },
  activity: { w: 4, h: 11, minW: 4, minH: 10.5 },
  vehicles: { w: 8, h: 9, minW: 6, minH: 9 },
  utilization: { w: 4, h: 9, minW: 4, minH: 8 },
  trips: { w: 12, h: 5.5, minW: 4, minH: 5.5 },
};
const record = (value: unknown): Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
const dimension = (value: unknown, fallback: number, min: number, max: number) =>
  typeof value === "number" && Number.isFinite(value)
    ? Math.max(min, Math.min(max, Math.round(value * GRID.precision) / GRID.precision))
    : fallback;

function safeItem(
  id: WidgetId,
  profile: LayoutProfile,
  source: unknown,
  fallback: LayoutItem,
): LayoutItem {
  const value = record(source);
  const cols = columns(profile);
  const size = sizes[id];
  const minW = profile === "compact" ? 1 : size.minW;
  const w = dimension(value.w, fallback.w, minW, cols);
  const minH =
    id === "metrics" && (profile === "compact" || w < 10) ? 8 : size.minH;
  return {
    i: id,
    x: dimension(value.x, fallback.x, 0, cols - w),
    y: dimension(value.y, fallback.y, 0, 200),
    w,
    h: dimension(value.h, fallback.h, minH, 24),
    minW,
    maxW: cols,
    minH,
    maxH: 24,
  };
}

export function defaultLayout(
  section: SectionId,
  profile: LayoutProfile,
): Layout {
  let x = 0;
  let y = 0;
  let rowH = 0;
  const cols = columns(profile);
  return SECTION_WIDGETS[section].map((id) => {
    const size = sizes[id];
    const w = profile === "compact" ? 1 : size.w;
    const h = id === "metrics" && profile === "compact" ? 8 : size.h;
    if (x + w > cols) {
      x = 0;
      y += rowH;
      rowH = 0;
    }
    const item = safeItem(id, profile, { x, y, w, h }, { i: id, x, y, w, h });
    x += w;
    rowH = Math.max(rowH, h);
    return item;
  });
}

// Stored data is untrusted. Rebuild bounds and constraints rather than spreading it.
export function normalizeLayout(
  section: SectionId,
  profile: LayoutProfile,
  value: unknown,
): Layout {
  const source = Array.isArray(value) ? value : [];
  const items = defaultLayout(section, profile).map((fallback) =>
    safeItem(
      fallback.i as WidgetId,
      profile,
      source.find((item) => record(item).i === fallback.i),
      fallback,
    ),
  );
  // Hidden entries may share a position with visible entries. Compact only the
  // displayed subset so a reload does not move visible widgets around a hidden one.
  return items;
}
export function normalizeLayouts(value: unknown): SavedLayouts {
  const source = record(value);
  return Object.fromEntries(
    SECTION_IDS.map((section) => [
      section,
      Object.fromEntries(
        PROFILES.map((profile) => [
          profile,
          normalizeLayout(section, profile, record(source[section])[profile]),
        ]),
      ),
    ]),
  ) as SavedLayouts;
}
export function visibleLayout(
  layout: Layout,
  ids: readonly WidgetId[],
  profile: LayoutProfile,
): Layout {
  return compactLayout(
    layout.filter((item) => ids.includes(item.i as WidgetId)),
    profile,
  );
}

// Only displayed widgets change; hidden widgets keep their last position and size.
export function mergeLayout(
  previous: Layout,
  changed: Layout,
  profile: LayoutProfile,
): Layout {
  return previous.map((item) => {
    const next = changed.find((candidate) => candidate.i === item.i);
    return next ? safeItem(item.i as WidgetId, profile, next, item) : item;
  });
}
export function sameGeometry(left: Layout, right: Layout): boolean {
  return (
    left.length === right.length &&
    left.every((item) => {
      const other = right.find((value) => value.i === item.i);
      return (
        other &&
        ["x", "y", "w", "h"].every(
          (key) =>
            item[key as keyof LayoutItem] === other[key as keyof LayoutItem],
        )
      );
    })
  );
}
export function changeWidget(
  layout: Layout,
  id: WidgetId,
  profile: LayoutProfile,
  change: Partial<Pick<LayoutItem, "x" | "y" | "w" | "h">>,
): Layout {
  const clone = layout.map((item) => ({ ...item }));
  const current = clone.find((item) => item.i === id);
  if (!current) return clone;
  const next = safeItem(id, profile, { ...current, ...change }, current);
  if (change.x !== undefined || change.y !== undefined) {
    const dense = toGridLayout(clone);
    return fromGridLayout(verticalCompactor.compact(
      moveElement(
        dense,
        dense.find((item) => item.i === id)!,
        next.x * GRID.precision,
        next.y * GRID.precision,
        true,
        false,
        "vertical",
        columns(profile) * GRID.precision,
      ),
      columns(profile) * GRID.precision,
    ));
  }
  return compactLayout(clone.map((item) => (item.i === id ? next : item)), profile);
}

// A finer render grid keeps saved coordinates compatible with existing layouts.
// Persist logical units; the interaction engine works on integer half-units.
function scaleLayout(layout: Layout, factor: number): Layout {
  return layout.map((item) => ({
    ...item,
    x: item.x * factor,
    y: item.y * factor,
    w: item.w * factor,
    h: item.h * factor,
    minW: item.minW === undefined ? undefined : item.minW * factor,
    maxW: item.maxW === undefined ? undefined : item.maxW * factor,
    minH: item.minH === undefined ? undefined : item.minH * factor,
    maxH: item.maxH === undefined ? undefined : item.maxH * factor,
  }));
}
export const toGridLayout = (layout: Layout) => scaleLayout(layout, GRID.precision);
export const fromGridLayout = (layout: Layout) => scaleLayout(layout, 1 / GRID.precision);
export const compactLayout = (layout: Layout, profile: LayoutProfile) =>
  fromGridLayout(verticalCompactor.compact(toGridLayout(layout), columns(profile) * GRID.precision));

export function fitLayout(
  layout: Layout,
  profile: LayoutProfile,
  containerWidth: number,
  measured: Partial<Record<WidgetId, number>> = {},
): Layout {
  const cols = columns(profile);
  const fitted = layout.map((item) => {
    const id = item.i as WidgetId;
    const minW = profile === "compact" ? 1 : Math.min(
      cols,
      Math.max(item.minW ?? 1, widthUnits(minimumWidth[id], containerWidth)),
    );
    const w = Math.max(item.w, minW);
    const pixels = profile === "compact" ? containerWidth : widthPixels(w, containerWidth);
    const minH = Math.max(
      item.minH ?? 1,
      heightUnits(Math.max(minimumHeight(id, pixels), measured[id] ?? 0)),
    );
    return {
      ...item,
      minW,
      minH,
      w,
      h: Math.max(item.h, minH),
      maxH: Math.max(item.maxH ?? 24, minH),
      x: Math.min(item.x, cols - w),
    };
  });
  return compactLayout(fitted, profile);
}
