export const BACKGROUND_PRESETS = [
  { id: "city", name: "Miasto", description: "Wieczór nad rzeką", image: "city.jpg" },
  { id: "mountains", name: "Góry", description: "Spokój o poranku", image: "mountains.jpg" },
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
  kind: "default", preset: "city", veil: 28, blur: 0, customId: null,
});

function bounded(value: unknown, fallback: number, max: number) {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.max(0, Math.min(max, Math.round(value)))
    : fallback;
}
export function normalizeBackground(value: unknown): BackgroundPreferences {
  const defaults = defaultBackground();
  if (!value || typeof value !== "object" || Array.isArray(value)) return defaults;
  const saved = value as Partial<BackgroundPreferences>;
  return {
    kind: saved.kind === "preset" || saved.kind === "custom" ? saved.kind : "default",
    preset: BACKGROUND_PRESETS.find(item => item.id === saved.preset)?.id ?? defaults.preset,
    veil: bounded(saved.veil, defaults.veil, 70),
    blur: bounded(saved.blur, defaults.blur, 16),
    customId: typeof saved.customId === "string" && /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i.test(saved.customId)
      ? saved.customId : null,
  };
}

export function presetBackground(preset: BackgroundPreset, base = "/") {
  const item = BACKGROUND_PRESETS.find(item => item.id === preset)!;
  if (item.image) return `url("${base}backgrounds/${item.image}")`;
  if (preset === "lagoon") return "radial-gradient(ellipse at 15% 15%, #8edee4, transparent 55%), radial-gradient(ellipse at 90% 80%, #267aa4, transparent 65%), linear-gradient(135deg, #a9d2ed, #268a99)";
  return "radial-gradient(ellipse at 15% 10%, #907bcb, transparent 60%), radial-gradient(ellipse at 85% 80%, #306e95, transparent 65%), linear-gradient(135deg, #253b69, #564475)";
}

export const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
export const MAX_IMAGE_PIXELS = 40_000_000;
export const MAX_IMAGE_EDGE = 2560;
export function validateImageFile(file: Pick<File, "size" | "type">) {
  if (!["image/jpeg", "image/png", "image/webp"].includes(file.type))
    throw new Error("Wybierz zdjęcie JPG, PNG lub WebP.");
  if (!file.size || file.size > MAX_IMAGE_BYTES)
    throw new Error("Wybierz obraz o rozmiarze do 10 MB.");
}
export function fitImage(width: number, height: number) {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0 || width * height > MAX_IMAGE_PIXELS)
    throw new Error("Obraz jest zbyt duży. Wybierz zdjęcie do 40 megapikseli.");
  const scale = Math.min(1, MAX_IMAGE_EDGE / Math.max(width, height));
  return { width: Math.max(1, Math.round(width * scale)), height: Math.max(1, Math.round(height * scale)) };
}
