export const BACKGROUND_PRESETS = [
  {
    id: "city",
    name: "Miasto",
    description: "Wieczór nad rzeką",
    image: "city.jpg",
  },
  {
    id: "mountains",
    name: "Góry",
    description: "Spokój o poranku",
    image: "mountains.jpg",
  },
  { id: "lagoon", name: "Laguna", description: "Błękit i turkus", image: null },
  { id: "aurora", name: "Zorza", description: "Fiolet i granat", image: null },
] as const;
export type BackgroundPreset = (typeof BACKGROUND_PRESETS)[number]["id"];
export type BackgroundKind = "default" | "preset" | "custom";
export type BackgroundPreferences = {
  kind: BackgroundKind;
  preset: BackgroundPreset;
  veil: number;
  blur: number;
  customId: string | null;
};
export const defaultBackground = (): BackgroundPreferences => ({
  kind: "default",
  preset: "city",
  veil: 28,
  blur: 0,
  customId: null,
});

function bounded(value: unknown, fallback: number, max: number) {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.max(0, Math.min(max, Math.round(value)))
    : fallback;
}
export function normalizeBackground(value: unknown): BackgroundPreferences {
  const defaults = defaultBackground();
  if (!value || typeof value !== "object" || Array.isArray(value))
    return defaults;
  const saved = value as Partial<BackgroundPreferences>;
  return {
    kind:
      saved.kind === "preset" || saved.kind === "custom"
        ? saved.kind
        : "default",
    preset:
      BACKGROUND_PRESETS.find((item) => item.id === saved.preset)?.id ??
      defaults.preset,
    veil: bounded(saved.veil, defaults.veil, 70),
    blur: bounded(saved.blur, defaults.blur, 16),
    customId:
      typeof saved.customId === "string" &&
      /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i.test(saved.customId)
        ? saved.customId
        : null,
  };
}

export function presetBackground(preset: BackgroundPreset, base = "/") {
  const item = BACKGROUND_PRESETS.find((item) => item.id === preset)!;
  if (item.image) return `url("${base}backgrounds/${item.image}")`;
  if (preset === "lagoon")
    return "radial-gradient(ellipse at 15% 15%, #8edee4, transparent 55%), radial-gradient(ellipse at 90% 80%, #267aa4, transparent 65%), linear-gradient(135deg, #a9d2ed, #268a99)";
  return "radial-gradient(ellipse at 15% 10%, #907bcb, transparent 60%), radial-gradient(ellipse at 85% 80%, #306e95, transparent 65%), linear-gradient(135deg, #253b69, #564475)";
}

export {
  MAX_IMAGE_BYTES,
  MAX_IMAGE_PIXELS,
  MAX_IMAGE_EDGE,
  validateImageFile,
  fitImage,
} from "../../../shared/media/image-model.ts";
