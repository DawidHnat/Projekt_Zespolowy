import { useEffect, useLayoutEffect, useState } from "react";
import {
  defaultPreferences,
  parsePreferences,
  STORAGE_KEY,
  LEGACY_STORAGE_KEY,
} from "./preference-model";
import type { WidgetId } from "../features/dashboard/model/widget-types";
export { ACCENT_PRESETS, defaultPreferences } from "./preference-model";
export type {
  DashboardPreferences,
  ThemeMode,
  Arrangement,
} from "./preference-model";

function readPreferences() {
  try {
    return parsePreferences(
      localStorage.getItem(STORAGE_KEY) ??
        localStorage.getItem(LEGACY_STORAGE_KEY),
    );
  } catch {
    return defaultPreferences();
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
    root.dataset.material = preferences.material;
    root.style.colorScheme = resolvedTheme;
    root.style.setProperty("--accent", preferences.accent);
    root.style.setProperty("--accent-on", accentForeground(preferences.accent));
  }, [resolvedTheme, preferences.accent, preferences.material]);
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
    reset: () => setPreferences(defaultPreferences()),
  };
}
