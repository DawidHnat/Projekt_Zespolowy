import { useEffect, useRef } from "react";
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, EyeOff, X } from "lucide-react";
import type { LayoutItem } from "react-grid-layout";
import { widgetRegistry } from "../model/widget-registry";
import { GRID, heightPixels } from "../model/widget-sizing";
import type { LayoutProfile } from "../model/widget-layout";
import type { WidgetId } from "../model/widget-types";

export function WidgetSettingsDialog({
  item,
  profile,
  onClose,
  onChange,
  onMove,
  onHide,
}: {
  item?: LayoutItem;
  profile: LayoutProfile;
  onClose: () => void;
  onChange: (change: Partial<Pick<LayoutItem, "w" | "h">>) => void;
  onMove: (direction: string) => void;
  onHide: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (item && ref.current && !ref.current.open) ref.current.showModal();
    if (!item && ref.current?.open) ref.current.close();
  }, [item]);
  return (
    <dialog
      ref={ref}
      className="widget-settings-dialog"
      aria-labelledby="widget-settings-title"
      onClose={onClose}
      onKeyDown={(event) => event.stopPropagation()}
    >
      {item && (
        <>
          <header className="panel-header">
            <div>
              <span className="eyebrow">EDYCJA WIDGETU</span>
              <h2 id="widget-settings-title">
                {widgetRegistry[item.i as WidgetId].title}
              </h2>
            </div>
            <button
              className="icon-button"
              onClick={onClose}
              aria-label="Zamknij ustawienia widgetu"
            >
              <X size={20} />
            </button>
          </header>
          <div className="widget-settings-content">
            <p>
              Dobierz rozmiar i miejsce. Zmiany zatwierdzisz przyciskiem „Zapisz
              układ”.
            </p>
            <p className="minimum-size-hint">
              Minimalny rozmiar zachowuje podstawowe informacje i miejsce na pierwszy rekord.
            </p>
            {profile === "desktop" ? (
              <>
                <label className="size-control">
                  Szerokość <output>{Math.round(item.w / GRID.columns * 100)}%</output>
                  <input
                    type="range"
                    aria-label="Szerokość widgetu"
                    min={item.minW}
                    step={0.5}
                    max={12}
                    value={item.w}
                    onChange={(event) =>
                      onChange({ w: Number(event.target.value) })
                    }
                  />
                </label>
                <div className="size-presets">
                  {[
                    { name: "Kompaktowy", w: item.minW! },
                    { name: "Szeroki", w: Math.max(8, item.minW!) },
                    { name: "Pełna szerokość", w: 12 },
                  ].map(({ name, w }) => (
                    <button
                      className="button button-secondary"
                      key={name}
                      aria-pressed={item.w === w}
                      onClick={() => onChange({ w })}
                    >
                      {name}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <p className="compact-hint">
                Na małych ekranach widgety zajmują całą szerokość.
              </p>
            )}
            <label className="size-control">
              Wysokość <output>{heightPixels(item.h)} px</output>
              <input
                type="range"
                aria-label="Wysokość widgetu"
                min={item.minH}
                step={0.5}
                max={item.maxH}
                value={item.h}
                onChange={(event) =>
                  onChange({ h: Number(event.target.value) })
                }
              />
            </label>
            <div className="move-controls">
              <span>Przesuń</span>
              {[
                { key: "ArrowUp", label: "w górę", icon: ArrowUp },
                { key: "ArrowDown", label: "w dół", icon: ArrowDown },
                ...(profile === "desktop"
                  ? [
                      { key: "ArrowLeft", label: "w lewo", icon: ArrowLeft },
                      { key: "ArrowRight", label: "w prawo", icon: ArrowRight },
                    ]
                  : []),
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  className="icon-button"
                  aria-label={`Przesuń widget ${label}`}
                  onClick={() => onMove(key)}
                >
                  <Icon size={18} />
                </button>
              ))}
            </div>
            <button
              className="button button-secondary hide-widget-button"
              onClick={onHide}
            >
              <EyeOff size={17} />
              Ukryj w widokach
            </button>
            <small>Możesz włączyć go ponownie w „Dopasuj widok”.</small>
          </div>
          <footer className="widget-settings-footer">
            <button className="button button-primary" onClick={onClose}>
              Gotowe
            </button>
          </footer>
        </>
      )}
    </dialog>
  );
}
