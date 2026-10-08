import {
  WIDGET_IDS,
  type WidgetId,
} from "../features/dashboard/model/widget-types.ts";
import {
  normalizeLayouts,
  type SavedLayouts,
} from "../features/dashboard/model/widget-layout.ts";
import {
  defaultBackground,
  normalizeBackground,
  type BackgroundPreferences,
} from "../features/dashboard/model/background-model.ts";

export type ThemeMode = "light" | "dark" | "system";
export type Material = "solid" | "glass";
export type Arrangement = { visibleWidgets: WidgetId[]; layouts: SavedLayouts };
export type DashboardPreferences = Arrangement & {
  theme: ThemeMode;
  accent: string;
  material: Material;
  background: BackgroundPreferences;
};
export const STORAGE_KEY = "fleet-flow.dashboard.v2";
export const LEGACY_STORAGE_KEY = "fleet-flow.dashboard.v1";
export const ACCENT_PRESETS = [
  { name: "Ocean", value: "#1479e8" },
  { name: "Turkus", value: "#008b83" },
  { name: "Fiolet", value: "#7954d6" },
  { name: "Bursztyn", value: "#b66b0b" },
  { name: "Róża", value: "#c74470" },
];
export const defaultPreferences = (): DashboardPreferences => ({
  theme: "light",
  accent: ACCENT_PRESETS[0].value,
  material: "glass",
  background: defaultBackground(),
  visibleWidgets: [...WIDGET_IDS],
  layouts: normalizeLayouts(null),
});
export function parsePreferences(raw: string | null): DashboardPreferences {
  try {
    const parsed: unknown = JSON.parse(raw ?? "null");
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed))
      return defaultPreferences();
    const value = parsed as Partial<DashboardPreferences>;
    return {
      theme:
        value.theme === "dark" || value.theme === "system"
          ? value.theme
          : "light",
      accent:
        typeof value.accent === "string" && /^#[0-9a-f]{6}$/i.test(value.accent)
          ? value.accent
          : ACCENT_PRESETS[0].value,
      material: value.material === "solid" ? "solid" : "glass",
      background: normalizeBackground(value.background),
      visibleWidgets: Array.isArray(value.visibleWidgets)
        ? WIDGET_IDS.filter((id) => value.visibleWidgets!.includes(id))
        : [...WIDGET_IDS],
      layouts: normalizeLayouts(value.layouts),
    };
  } catch {
    return defaultPreferences();
  }
}
