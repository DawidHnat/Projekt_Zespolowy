import { useLayoutEffect, useState, type RefObject } from "react";
import type { WidgetId } from "../model/widget-types";

export type ContentMinimums = Partial<Record<WidgetId, number>>;

function contentHeight(id: WidgetId, body: HTMLElement): number {
  // The map is stretched, so use its readable canvas minimum instead of its
  // current height. Tables reserve the heading and first row, not the whole list.
  if (id === "map") {
    const canvas = body.querySelector(".map-canvas");
    if (canvas) return Number.parseFloat(getComputedStyle(canvas).minHeight) || 0;
  }
  if (id === "vehicles") {
    const head = body.querySelector("thead");
    const row = body.querySelector("tbody tr");
    if (head) return head.getBoundingClientRect().height +
      Math.max(44, row?.getBoundingClientRect().height ?? 0);
  }
  return body.getBoundingClientRect().height;
}

// One observer and one animation frame batch all measurements. Observe natural
// content, not the stretched card, so enlarging a widget never raises its minimum.
// During a gesture the grid owns its layout; refresh measurements on release.
export function useWidgetMinimums(
  container: RefObject<HTMLDivElement | null>,
  signature: string,
  paused: boolean,
) {
  const [minimums, setMinimums] = useState<ContentMinimums>({});
  useLayoutEffect(() => {
    const root = container.current;
    if (!root || paused) return;
    let frame = 0;
    const measure = () => {
      frame = 0;
      const next: ContentMinimums = {};
      root.querySelectorAll<HTMLElement>("[data-widget]").forEach((tile) => {
        const id = tile.dataset.widget as WidgetId;
        const header = tile.querySelector<HTMLElement>(".widget-header");
        const body = tile.querySelector<HTMLElement>(".widget-content-inner");
        if (!header || !body) return;
        next[id] = Math.ceil(header.getBoundingClientRect().height + contentHeight(id, body) + 18);
      });
      setMinimums((previous) => {
        const ids = Object.keys(next) as WidgetId[];
        return ids.length === Object.keys(previous).length && ids.every((id) => next[id] === previous[id])
          ? previous : next;
      });
    };
    const schedule = () => {
      if (!frame) frame = requestAnimationFrame(measure);
    };
    const observer = new ResizeObserver(schedule);
    root.querySelectorAll(
      ".widget-header, .widget-content-inner, .vehicle-table thead, .vehicle-table tbody tr:first-child",
    ).forEach((element) => observer.observe(element));
    measure();
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [container, signature, paused]);
  return minimums;
}
