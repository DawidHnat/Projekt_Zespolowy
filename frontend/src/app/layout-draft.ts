import type { DashboardPreferences } from "./preference-model.ts";
import type { SavedLayouts } from "../features/dashboard/model/widget-layout.ts";
import type { WidgetId } from "../features/dashboard/model/widget-types.ts";

export type EditableSection = "dashboard" | "map";
export type LayoutDraft = {
  layouts: SavedLayouts[EditableSection];
  visibleWidgets?: WidgetId[];
};
export type LayoutDrafts = Partial<Record<EditableSection, LayoutDraft>>;

export function createLayoutDraft(
  preferences: DashboardPreferences,
  view: EditableSection,
): LayoutDraft {
  return structuredClone({
    layouts: preferences.layouts[view],
    ...(view === "dashboard" ? { visibleWidgets: preferences.visibleWidgets } : {}),
  });
}

// Commit only this view, preserving changes saved in the other view or settings.
export function commitLayoutDraft(
  preferences: DashboardPreferences,
  view: EditableSection,
  draft: LayoutDraft,
): DashboardPreferences {
  return {
    ...preferences,
    layouts: { ...preferences.layouts, [view]: draft.layouts },
    ...(view === "dashboard" && draft.visibleWidgets ? { visibleWidgets: draft.visibleWidgets } : {}),
  };
}
