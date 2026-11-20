import { useState } from "react";
import {
  normalizeLayout,
  type LayoutProfile,
  type SavedLayouts,
} from "../../dashboard/model/widget-layout";
import {
  DRIVER_WIDGET_IDS,
  type WidgetId,
} from "../../dashboard/model/widget-types";
import {
  normalizeLayoutConfig,
  validVehicleId,
  type VehicleLayoutConfig,
} from "../../../shared/model/card-layout";

export type DriverPreferences = {
  version: 1;
  view: "list" | "cards";
  visible: WidgetId[];
  layouts: SavedLayouts["drivers"];
  cards: VehicleLayoutConfig;
  order: string[];
};
export function parseDriverPreferences(raw: string | null): DriverPreferences {
  let value: Partial<DriverPreferences> = {};
  try {
    const data: unknown = JSON.parse(raw || "null");
    if (data && typeof data === "object" && !Array.isArray(data)) value = data;
  } catch {
    /* Recover corrupt local geometry. */
  }
  const layouts = Object.fromEntries(
    (["desktop", "compact"] as LayoutProfile[]).map((profile) => [
      profile,
      normalizeLayout("drivers", profile, value.layouts?.[profile]),
    ]),
  ) as SavedLayouts["drivers"];
  return {
    version: 1,
    view: value.view === "cards" ? "cards" : "list",
    visible: Array.isArray(value.visible)
      ? DRIVER_WIDGET_IDS.filter((id) => value.visible!.includes(id))
      : [...DRIVER_WIDGET_IDS],
    layouts,
    cards: normalizeLayoutConfig(value.cards),
    order: Array.isArray(value.order)
      ? [
          ...new Set(
            value.order.filter(
              (item) => typeof item === "string" && validVehicleId(item),
            ),
          ),
        ].slice(0, 2000)
      : [],
  };
}
export function useDriverPreferences(userId: string) {
  const key = `fleet-flow.drivers.v1.${userId}`;
  const [saved, setSaved] = useState(() => {
    try {
      return parseDriverPreferences(localStorage.getItem(key));
    } catch {
      return parseDriverPreferences(null);
    }
  });
  const [draft, setDraft] = useState<DriverPreferences | null>(null);
  const [persistent, setPersistent] = useState(true);
  const persist = (value: DriverPreferences) => {
    setSaved(value);
    try {
      localStorage.setItem(key, JSON.stringify(value));
      setPersistent(true);
    } catch {
      setPersistent(false);
    }
  };
  return {
    saved,
    draft,
    effective: draft ?? saved,
    persistent,
    start: () => setDraft(structuredClone(saved)),
    cancel: () => setDraft(null),
    save: () => {
      if (draft) persist(draft);
      setDraft(null);
    },
    reset: () => setDraft(parseDriverPreferences(null)),
    update: (change: (value: DriverPreferences) => DriverPreferences) =>
      setDraft((value) => (value ? change(value) : value)),
    setView: (view: DriverPreferences["view"]) => {
      if (draft) setDraft((value) => (value ? { ...value, view } : value));
      else persist({ ...saved, view });
    },
  };
}
