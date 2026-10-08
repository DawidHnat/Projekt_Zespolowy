import { useEffect, useLayoutEffect, useState } from "react";
import {
  WIDGET_IDS,
  type WidgetId,
} from "../features/dashboard/model/widget-types";

export type ThemeMode = "light" | "dark" | "system";
export type DashboardPreferences = {
  theme: ThemeMode;
  accent: string;
  visibleWidgets: WidgetId[];
};
const STORAGE_KEY = "fleet-flow.dashboard.v1";
export const ACCENT_PRESETS = [
  { name: "Ocean", value: "#1479e8" },
  { name: "Turkus", value: "#008b83" },
  { name: "Fiolet", value: "#7954d6" },
  { name: "Bursztyn", value: "#b66b0b" },
  { name: "Róża", value: "#c74470" },
];
const defaults = (): DashboardPreferences => ({
  theme: "light",
  accent: ACCENT_PRESETS[0].value,
  visibleWidgets: [...WIDGET_IDS],
});

function readPreferences(): DashboardPreferences {
  try {
    const stored: unknown = JSON.parse(
      localStorage.getItem(STORAGE_KEY) ?? "null",
    );
    if (!stored || typeof stored !== "object") return defaults();
    const value = stored as Partial<DashboardPreferences>;
    return {
      theme:
        value.theme === "dark" || value.theme === "system"
          ? value.theme
          : "light",
      accent:
        typeof value.accent === "string" && /^#[0-9a-f]{6}$/i.test(value.accent)
          ? value.accent
          : ACCENT_PRESETS[0].value,
      visibleWidgets: Array.isArray(value.visibleWidgets)
        ? WIDGET_IDS.filter((id) => value.visibleWidgets!.includes(id))
        : [...WIDGET_IDS],
    };
  } catch {
    return defaults();
  }
}

// Choose legible text for any user-selected accent, including pale colors.
function accentForeground(hex: string) {
  const rgb = [1, 3, 5]
    .map((index) => parseInt(hex.slice(index, index + 2), 16) / 255)
    .map((value) =>
      value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4,
    );
  const luminance = rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
  return (luminance + 0.05) / 0.05 >= 1.05 / (luminance + 0.05)
    ? "#000000"
    : "#ffffff";
}

export function useDashboardPreferences() {
  const [preferences, setPreferences] = useState(readPreferences);
  const [systemDark, setSystemDark] = useState(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches,
  );
  const [persistent, setPersistent] = useState(true);
  const resolvedTheme =
    preferences.theme === "system"
      ? systemDark
        ? "dark"
        : "light"
      : preferences.theme;

  useEffect(() => {
    const query = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => setSystemDark(query.matches);
    query.addEventListener("change", handleChange);
    return () => query.removeEventListener("change", handleChange);
  }, []);
  useLayoutEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = resolvedTheme;
    root.style.colorScheme = resolvedTheme;
    root.style.setProperty("--accent", preferences.accent);
    root.style.setProperty("--accent-on", accentForeground(preferences.accent));
  }, [resolvedTheme, preferences.accent]);
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
      setPersistent(true);
    } catch {
      setPersistent(false);
    }
  }, [preferences]);

  const toggleWidget = (id: WidgetId) =>
    setPreferences((previous) => ({
      ...previous,
      visibleWidgets: previous.visibleWidgets.includes(id)
        ? previous.visibleWidgets.filter((value) => value !== id)
        : [...previous.visibleWidgets, id],
    }));
  return {
    preferences,
    setPreferences,
    resolvedTheme,
    persistent,
    toggleWidget,
    reset: () => setPreferences(defaults()),
  };
}
