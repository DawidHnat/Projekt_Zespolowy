import { useCallback, useEffect, useRef, useState } from "react";
import type { WidgetId } from "../model/widget-types";

// RGL memoizes GridItem by snapped coordinates. Its pixel position lives in a
// ref, so movement within a grid cell can skip a paint. Refresh only the active
// child's identity once per animation frame; other cards and domain content stay
// memoized. The engine still owns positioning, collisions and edge scrolling.
export function useGesturePaint() {
  const [gesture, setGesture] = useState<{ id: WidgetId; revision: number } | null>(null);
  const frame = useRef(0);
  const cancel = useCallback(() => {
    cancelAnimationFrame(frame.current);
    frame.current = 0;
  }, []);
  useEffect(() => cancel, [cancel]);
  const start = useCallback((id: WidgetId) => {
    cancel();
    setGesture({ id, revision: 0 });
  }, [cancel]);
  const paint = useCallback(() => {
    if (frame.current) return;
    frame.current = requestAnimationFrame(() => {
      frame.current = 0;
      setGesture(previous => previous && { ...previous, revision: previous.revision + 1 });
    });
  }, []);
  const stop = useCallback(() => {
    cancel();
    setGesture(null);
  }, [cancel]);
  return { gesture, start, paint, stop };
}
