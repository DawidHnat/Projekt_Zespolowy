import type { CSSProperties } from "react";
import { presetBackground, type BackgroundPreferences } from "../model/background-model";
import type { BackgroundImageController } from "../model/useBackgroundImage";

export function backgroundSource(preferences: BackgroundPreferences, media: BackgroundImageController) {
  if (preferences.kind === "preset") return presetBackground(preferences.preset, import.meta.env.BASE_URL);
  if (preferences.kind === "custom" && preferences.customId === media.image?.id && media.url)
    return `url("${media.url}")`;
  return "";
}
export function DashboardBackground({ source, preferences }: { source: string; preferences: BackgroundPreferences }) {
  if (!source) return null;
  return (
    <div className="dashboard-backdrop" aria-hidden="true" style={{
      "--wallpaper-image": source,
      "--wallpaper-veil": preferences.veil / 100,
      "--wallpaper-blur": `${preferences.blur}px`,
    } as CSSProperties}>
      <div className="dashboard-backdrop-image" />
      <div className="dashboard-backdrop-veil" />
    </div>
  );
}
