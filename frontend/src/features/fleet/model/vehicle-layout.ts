export type CardSize = { width: number; height: number };
export type VehicleLayout = Record<string, CardSize>;
export const CARD_MIN = { width: 280, height: 420 };
export const CARD_MAX = { width: 720, height: 720 };
export const CARD_DEFAULT = { width: 320, height: 440 };
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
