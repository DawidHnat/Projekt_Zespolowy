import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import GridLayout, {
  useContainerWidth,
  type Layout,
  type LayoutItem,
} from "react-grid-layout";
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  EyeOff,
  Grip,
  MoveDiagonal2,
  Settings2,
  X,
} from "lucide-react";
import {
  changeWidget,
  columns,
  visibleLayout,
  type LayoutProfile,
  type SavedLayouts,
} from "../model/widget-layout";
import { widgetRegistry } from "../model/widget-registry";
import type { SectionId, WidgetId } from "../model/widget-types";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";

type Props = {
  section: SectionId;
  ids: WidgetId[];
  layouts: SavedLayouts;
  editing: boolean;
  onLayout: (
    section: SectionId,
    profile: LayoutProfile,
    layout: Layout,
  ) => void;
  onHide: (id: WidgetId) => void;
};

export function DashboardGrid({
  section,
  ids,
  layouts,
  editing,
  onLayout,
  onHide,
}: Props) {
  const { width, containerRef, mounted } = useContainerWidth({
    measureBeforeMount: true,
  });
  const profile: LayoutProfile = width < 720 ? "compact" : "desktop";
  const layout = visibleLayout(layouts[section][profile], ids, profile);
  const [selected, setSelected] = useState<WidgetId | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const selectedItem = layout.find((item) => item.i === selected);
  const apply = (next: Layout, id?: WidgetId) => {
    if (!editing) return;
    onLayout(section, profile, next);
    if (id) setAnnouncement(`Zmieniono układ: ${widgetRegistry[id].title}.`);
  };
  const update = (
    id: WidgetId,
    change: Partial<Pick<LayoutItem, "x" | "y" | "w" | "h">>,
  ) => apply(changeWidget(layout, id, profile, change), id);
  const move = (id: WidgetId, direction: string) => {
    const item = layout.find((value) => value.i === id)!;
    const offsets: Record<string, { x?: number; y?: number }> = {
      ArrowLeft: { x: item.x - 1 },
      ArrowRight: { x: item.x + 1 },
      ArrowUp: { y: item.y - 1 },
      ArrowDown: { y: item.y + item.h },
    };
    update(id, offsets[direction]);
  };
  const keyboard = (event: KeyboardEvent<HTMLButtonElement>, id: WidgetId) => {
    if (
      !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)
    )
      return;
    event.preventDefault();
    event.stopPropagation();
    const item = layout.find((value) => value.i === id)!;
    if (event.shiftKey)
      update(id, {
        w:
          item.w +
          (event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0),
        h:
          item.h +
          (event.key === "ArrowDown" ? 1 : event.key === "ArrowUp" ? -1 : 0),
      });
    else move(id, event.key);
  };
  return (
    <div
      ref={containerRef}
      className={`dashboard-canvas ${editing ? "is-editing" : ""}`}
      data-profile={profile}
    >
      <p className="sr-only" id="widget-keyboard-help">
        Przesuwaj strzałkami. Shift i strzałki zmieniają rozmiar. Enter otwiera
        ustawienia.
      </p>
      <span className="sr-only" role="status" aria-live="polite">
        {announcement}
      </span>
      {editing && (
        <p className="layout-profile-note">
          {profile === "compact"
            ? "Edytujesz układ na małe ekrany"
            : "Edytujesz układ na duże ekrany"}{" "}
          · zmiany dotyczą tego widoku
        </p>
      )}
      {mounted && ids.length > 0 && (
        <GridLayout
          key={`${section}-${profile}`}
          width={width}
          layout={layout}
          className="dashboard-grid"
          gridConfig={{
            cols: columns(profile),
            rowHeight: 18,
            margin: [16, 16],
            containerPadding: [0, 0],
          }}
          dragConfig={{
            enabled: editing,
            handle: ".widget-drag-handle",
            cancel: "[data-no-drag]",
            threshold: 5,
          }}
          resizeConfig={{
            enabled: editing,
            handles: ["se"],
            handleComponent: (axis, ref) => (
              <span
                ref={ref}
                className={`react-resizable-handle react-resizable-handle-${axis} widget-resize-handle`}
                title="Przeciągnij, aby zmienić rozmiar"
                aria-hidden="true"
              >
                <MoveDiagonal2 size={17} />
              </span>
            ),
          }}
          onDragStop={(next, _old, item) =>
            apply(next, item?.i as WidgetId | undefined)
          }
          onResizeStop={(next, _old, item) =>
            apply(next, item?.i as WidgetId | undefined)
          }
        >
          {[...layout]
            .sort((a, b) => a.y - b.y || a.x - b.x)
            .map(({ i }) => {
              const id = i as WidgetId;
              const widget = widgetRegistry[id];
              const Component = widget.component;
              return (
                <div
                  className={`widget-slot widget-slot-${id}`}
                  key={id}
                  data-widget={id}
                >
                  {editing && (
                    <div className="widget-editor-controls">
                      <button
                        className="widget-drag-handle"
                        aria-label={`Przesuń: ${widget.title}`}
                        aria-describedby="widget-keyboard-help"
                        onKeyDown={(event) => keyboard(event, id)}
                        onClick={(event) => {
                          if (event.detail === 0) setSelected(id);
                        }}
                        title="Przeciągnij lub użyj strzałek"
                      >
                        <Grip size={17} />
                      </button>
                      <button
                        data-no-drag
                        className="widget-settings-button"
                        aria-label={`Edytuj: ${widget.title}`}
                        onClick={() => setSelected(id)}
                      >
                        <Settings2 size={17} />
                      </button>
                    </div>
                  )}
                  <Component />
                </div>
              );
            })}
        </GridLayout>
      )}
      <WidgetSettingsDialog
        item={editing ? selectedItem : undefined}
        profile={profile}
        onClose={() => setSelected(null)}
        onChange={(change) => {
          if (selected) update(selected, change);
        }}
        onMove={(direction) => {
          if (selected) move(selected, direction);
        }}
        onHide={() => {
          if (selected) onHide(selected);
          setSelected(null);
        }}
      />
    </div>
  );
}

function WidgetSettingsDialog({
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
            {profile === "desktop" ? (
              <>
                <label className="size-control">
                  Szerokość <output>{item.w} / 12 kolumn</output>
                  <input
                    type="range"
                    aria-label="Szerokość widgetu"
                    min={item.minW}
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
              Wysokość <output>{item.h * 34 - 16} px</output>
              <input
                type="range"
                aria-label="Wysokość widgetu"
                min={item.minH}
                max={24}
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
