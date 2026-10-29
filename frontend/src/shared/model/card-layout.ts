export type CardSize = { width: number; height: number };
export type VehicleLayout = Record<string, CardSize>;
export const CARD_MIN = { width: 280, height: 420 };
export const CARD_MAX = { width: 720, height: 720 };
export const CARD_DEFAULT = { width: 320, height: 440 };
export const CARD_PRESETS = [
  { name: "Małe", width: 280, height: 420 },
  { name: "Standardowe", width: 320, height: 440 },
  { name: "Duże", width: 480, height: 500 },
];
export const validVehicleId = (value: string) =>
  /^[a-f\d]{8}-(?:[a-f\d]{4}-){3}[a-f\d]{12}$/i.test(value);
const bounded = (value: unknown, fallback: number, min: number, max: number) =>
  typeof value === "number" && Number.isFinite(value)
    ? Math.max(min, Math.min(max, Math.round(value)))
    : fallback;
export function normalizeCardSize(value: unknown): CardSize {
  const item =
    value && typeof value === "object" ? (value as Partial<CardSize>) : {};
  return {
    width: bounded(
      item.width,
      CARD_DEFAULT.width,
      CARD_MIN.width,
      CARD_MAX.width,
    ),
    height: bounded(
      item.height,
      CARD_DEFAULT.height,
      CARD_MIN.height,
      CARD_MAX.height,
    ),
  };
}
export function normalizeVehicleLayout(value: unknown): VehicleLayout {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return Object.fromEntries(
    Object.entries(value)
      .filter(([id]) => validVehicleId(id))
      .slice(0, 2000)
      .map(([id, size]) => [id, normalizeCardSize(size)]),
  );
}
export function resizeCard(
  layout: VehicleLayout,
  id: string,
  size: CardSize,
): VehicleLayout {
  return validVehicleId(id)
    ? { ...layout, [id]: normalizeCardSize(size) }
    : layout;
}

// A fleet-wide default also covers vehicles that have not been loaded yet.
// Individual overrides and the legacy v1 layout remain compatible.
export type VehicleLayoutConfig = {
  version: 2;
  defaultSize: CardSize;
  sizes: VehicleLayout;
};
export type ResizeTarget = "all" | readonly string[];
export function normalizeLayoutConfig(value: unknown): VehicleLayoutConfig {
  const item =
    value && typeof value === "object"
      ? (value as Partial<VehicleLayoutConfig>)
      : {};
  return {
    version: 2,
    defaultSize:
      item.version === 2
        ? normalizeCardSize(item.defaultSize)
        : { ...CARD_DEFAULT },
    sizes: normalizeVehicleLayout(item.version === 2 ? item.sizes : value),
  };
}
export function cardSize(layout: VehicleLayoutConfig, id: string): CardSize {
  return layout.sizes[id] ?? layout.defaultSize;
}
export function resizeCards(
  layout: VehicleLayoutConfig,
  target: ResizeTarget,
  patch: Partial<CardSize>,
): VehicleLayoutConfig {
  const defaultSize =
    target === "all"
      ? normalizeCardSize({ ...layout.defaultSize, ...patch })
      : layout.defaultSize;
  const sizes = { ...layout.sizes };
  const ids =
    target === "all"
      ? Object.keys(sizes)
      : [...new Set(target)].filter(validVehicleId);
  for (const id of ids) {
    const next = normalizeCardSize({ ...cardSize(layout, id), ...patch });
    if (next.width === defaultSize.width && next.height === defaultSize.height)
      delete sizes[id];
    else sizes[id] = next;
  }
  return { version: 2, defaultSize, sizes };
}
export function targetSizes(layout: VehicleLayoutConfig, target: ResizeTarget) {
  const values =
    target === "all"
      ? [layout.defaultSize, ...Object.values(layout.sizes)]
      : [...new Set(target)]
          .filter(validVehicleId)
          .map((id) => cardSize(layout, id));
  const first = values[0] ?? layout.defaultSize;
  return {
    first,
    mixedWidth: values.some((size) => size.width !== first.width),
    mixedHeight: values.some((size) => size.height !== first.height),
  };
}
