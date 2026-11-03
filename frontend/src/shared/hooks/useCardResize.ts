import { useEffect, useRef, useState, type PointerEvent } from "react";
import { normalizeCardSize, type CardSize } from "../model/card-layout";

export function useCardResize(
  size: CardSize,
  commit: (size: CardSize) => void,
) {
  const [live, setLive] = useState<CardSize | null>(null);
  const gesture = useRef<{
    x: number;
    y: number;
    start: CardSize;
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
          next: size,
        };
      },
      onPointerMove: (e: PointerEvent<HTMLButtonElement>) => {
        const current = gesture.current;
        if (!current) return;
        current.next = normalizeCardSize({
          width: current.start.width + e.clientX - current.x,
          height: current.start.height + e.clientY - current.y,
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
