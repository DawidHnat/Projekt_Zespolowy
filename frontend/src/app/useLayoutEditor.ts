import { useCallback, useMemo, useState } from "react";
import { defaultPreferences, type useDashboardPreferences } from "./preferences";
import {
  commitLayoutDraft,
  createLayoutDraft,
  type EditableSection,
  type LayoutDrafts,
} from "./layout-draft";
import {
  defaultLayout,
  mergeLayout,
  sameGeometry,
} from "../features/dashboard/model/widget-layout";
import type { DashboardGridProps } from "../features/dashboard/components/DashboardGrid";
import type { WidgetId } from "../features/dashboard/model/widget-types";

export function useLayoutEditor(
  settings: ReturnType<typeof useDashboardPreferences>,
) {
  const [drafts, setDrafts] = useState<LayoutDrafts>({});
  const effective = useMemo(() => ({
    ...settings.preferences,
    visibleWidgets:
      drafts.dashboard?.visibleWidgets ?? settings.preferences.visibleWidgets,
    layouts: {
      ...settings.preferences.layouts,
      ...(drafts.dashboard ? { dashboard: drafts.dashboard.layouts } : {}),
      ...(drafts.map ? { map: drafts.map.layouts } : {}),
    },
  }), [settings.preferences, drafts]);
  const start = (view: EditableSection) => {
    if (view === "dashboard" && (
      settings.cloud.loading ||
      settings.cloud.saving
    )) return;
    setDrafts(previous => ({
      ...previous,
      [view]: previous[view] ?? createLayoutDraft(settings.preferences, view),
    }));
  };
  const cancel = (view: EditableSection) => setDrafts(previous => {
    const next = { ...previous };
    delete next[view];
    return next;
  });
  const save = async (view: EditableSection, overwrite = false) => {
    const draft = drafts[view];
    if (!draft) return false;
    const next = commitLayoutDraft(settings.preferences, view, draft);
    if (view === "dashboard") {
      const saved = await settings.saveArrangement({
        visibleWidgets: next.visibleWidgets,
        layouts: { dashboard: next.layouts.dashboard },
      }, overwrite);
      if (!saved) return false;
    } else {
      const saved = await settings.saveArrangement({
        visibleWidgets: next.visibleWidgets,
        layouts: { map: next.layouts.map },
      }, overwrite);
      if (!saved) return false;
    }
    setDrafts(previous => {
      if (previous[view] !== draft) return previous;
      const remaining = { ...previous };
      delete remaining[view];
      return remaining;
    });
    return true;
  };
  const update = useCallback<DashboardGridProps["onLayout"]>((view, profile, layout) => {
    if (view !== "map" && view !== "dashboard") return;
    setDrafts(previous => {
      const draft = previous[view];
      if (!draft) return previous;
      const merged = mergeLayout(draft.layouts[profile], layout, profile, view);
      if (sameGeometry(draft.layouts[profile], merged)) return previous;
      return {
        ...previous,
        [view]: { ...draft, layouts: { ...draft.layouts, [profile]: merged } },
      };
    });
  }, []);
  const toggleWidget = (id: WidgetId) => {
    if (
      settings.cloud.loading ||
      settings.cloud.saving
    ) return;
    if (!drafts.dashboard) {
      settings.setPreferences(previous => ({
        ...previous,
        visibleWidgets: previous.visibleWidgets.includes(id)
          ? previous.visibleWidgets.filter(value => value !== id)
          : [...previous.visibleWidgets, id],
      }));
      return;
    }
    setDrafts(previous => {
      const draft = previous.dashboard;
      if (!draft?.visibleWidgets) return previous;
      const visibleWidgets = draft.visibleWidgets.includes(id)
        ? draft.visibleWidgets.filter(value => value !== id) : [...draft.visibleWidgets, id];
      return { ...previous, dashboard: { ...draft, visibleWidgets } };
    });
  };
  const resetView = (view: EditableSection) => setDrafts(previous => {
    if (!previous[view]) return previous;
    return {
      ...previous,
      [view]: {
        ...previous[view],
        layouts: {
          desktop: defaultLayout(view, "desktop"),
          compact: defaultLayout(view, "compact"),
        },
      },
    };
  });
  const resetAll = () => {
    const defaults = defaultPreferences();
    const next = {
      ...defaults,
      visibleWidgets: defaults.visibleWidgets,
      layouts: {
        ...defaults.layouts,
      },
    };
    settings.setPreferences(next);
    setDrafts(previous => Object.fromEntries(
      (Object.keys(previous) as EditableSection[]).map(view => [
        view, createLayoutDraft(defaults, view),
      ]),
    ));
  };
  const reloadDashboard = () => {
    settings.reloadRemoteArrangement();
    cancel("dashboard");
  };
  const overwriteDashboard = () => save("dashboard", true);
  return {
    drafts, effective, start, cancel, save, update, toggleWidget, resetView,
    resetAll, reloadDashboard, overwriteDashboard,
  };
}
