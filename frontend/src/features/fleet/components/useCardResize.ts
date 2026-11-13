import { useEffect, useRef, useState, type PointerEvent } from "react";
import { normalizeCardSize, type CardSize } from "../model/vehicle-layout";

export function useCardResize(
  size: CardSize,
  commit: (size: CardSize) => void,
) {
  const [live, setLive] = useState<CardSize | null>(null);
  const gesture = useRef<{
    x: number;
    y: number;
    start: CardSize;
    saved: CardSize;
    next: CardSize;
  } | null>(null);
  const frame = useRef(0);
  useEffect(() => () => cancelAnimationFrame(frame.current), []);
  const stop = (save: boolean) => {
    cancelAnimationFrame(frame.current);
    frame.current = 0;
    const next = gesture.current?.next;
    gesture.current = null;
    if (save && next) commit(next);
    setLive(null);
  };
  return {
    live,
    handle: {
      onPointerDown: (e: PointerEvent<HTMLButtonElement>) => {
        if (e.button !== 0 || !e.isPrimary) return;
        e.preventDefault();
        e.currentTarget.setPointerCapture(e.pointerId);
        const bounds = e.currentTarget
          .closest("article")!
          .getBoundingClientRect();
        gesture.current = {
          x: e.clientX,
          y: e.clientY,
          start: { width: bounds.width, height: size.height },
          saved: size,
          next: size,
        };
      },
      onPointerMove: (e: PointerEvent<HTMLButtonElement>) => {
        const current = gesture.current;
        if (!current) return;
        const dx = e.clientX - current.x;
        const dy = e.clientY - current.y;
        // A narrow viewport can clamp the rendered width below the saved one.
        // Preserve an untouched axis, including small pointer jitter. A deliberate
        // horizontal resize still starts at the visible edge of the card.
        current.next = normalizeCardSize({
          width: Math.abs(dx) < 5 ? current.saved.width : current.start.width + dx,
          height: Math.abs(dy) < 5 ? current.saved.height : current.start.height + dy,
        });
        if (!frame.current)
          frame.current = requestAnimationFrame(() => {
            frame.current = 0;
            setLive(gesture.current?.next ?? null);
          });
      },
      onPointerUp: () => stop(true),
      onPointerCancel: () => stop(false),
      onLostPointerCapture: () => {
        if (gesture.current) stop(false);
      },
    },
  };
}
