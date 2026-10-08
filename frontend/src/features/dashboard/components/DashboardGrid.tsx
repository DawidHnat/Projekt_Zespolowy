import { memo, useCallback, useMemo, useState, type KeyboardEvent } from "react";
import {
  gridBounds,
  minMaxSize,
  type LayoutConstraint,
} from "react-grid-layout/core";
import GridLayout, {
  useContainerWidth,
  type Layout,
  type LayoutItem,
} from "react-grid-layout";
import { Grip, MoveDiagonal2, Settings2 } from "lucide-react";
import {
  changeWidget,
  columns,
  visibleLayout,
  fitLayout,
  fromGridLayout,
  toGridLayout,
  type LayoutProfile,
  type SavedLayouts,
} from "../model/widget-layout";
import { widgetRegistry } from "../model/widget-registry";
import type { SectionId, WidgetId } from "../model/widget-types";
import {
  GRID,
  heightUnits,
  minimumHeight,
  widthPixels,
} from "../model/widget-sizing";
import { useWidgetMinimums } from "./useWidgetMinimums";
import { WidgetSettingsDialog } from "./WidgetSettingsDialog";
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

// Domain widgets do not rerender while the interaction engine moves their frame.
const WidgetContent = memo(function WidgetContent({ id }: { id: WidgetId }) {
  const Component = widgetRegistry[id].component;
  return <Component />;
});

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
  const [interacting, setInteracting] = useState(false);
  const signature = `${section}-${profile}-${ids.join(",")}-${mounted}-${editing}`;
  const minimums = useWidgetMinimums(containerRef, signature, interacting);
  const layout = useMemo(
    () => fitLayout(
      visibleLayout(layouts[section][profile], ids, profile),
      profile,
      width,
      minimums,
    ),
    [layouts, section, ids, profile, width, minimums],
  );
  const gridLayout = useMemo(() => toGridLayout(layout), [layout]);
  const constraints = useMemo<LayoutConstraint[]>(() => [
    gridBounds,
    minMaxSize,
    {
      name: "widget-content",
      constrainSize(item, w, h) {
        const pixels = profile === "compact"
          ? width : widthPixels(w / GRID.precision, width);
        const minH = heightUnits(minimumHeight(item.i as WidgetId, pixels));
        return { w, h: Math.max(h, minH * GRID.precision) };
      },
    },
  ], [profile, width]);
  const [selected, setSelected] = useState<WidgetId | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const selectedItem = layout.find((item) => item.i === selected);
  const apply = useCallback(
    (next: Layout, id?: WidgetId) => {
      if (!editing) return;
      onLayout(section, profile, next);
      if (id) setAnnouncement(`Zmieniono układ: ${widgetRegistry[id].title}.`);
    },
    [editing, onLayout, section, profile],
  );
  const update = (
    id: WidgetId,
    change: Partial<Pick<LayoutItem, "x" | "y" | "w" | "h">>,
  ) => apply(changeWidget(layout, id, profile, change), id);
  const move = (id: WidgetId, direction: string) => {
    const item = layout.find((value) => value.i === id)!;
    const offsets: Record<string, { x?: number; y?: number }> = {
      ArrowLeft: { x: item.x - 0.5 },
      ArrowRight: { x: item.x + 0.5 },
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
          (event.key === "ArrowRight" ? 0.5 : event.key === "ArrowLeft" ? -0.5 : 0),
        h:
          item.h +
          (event.key === "ArrowDown" ? 0.5 : event.key === "ArrowUp" ? -0.5 : 0),
      });
    else move(id, event.key);
  };
  return (
    <div
      ref={containerRef}
      className={`dashboard-canvas ${editing ? "is-editing" : ""} ${interacting ? "is-interacting" : ""}`}
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
          layout={gridLayout}
          constraints={constraints}
          className="dashboard-grid"
          gridConfig={{
            cols: columns(profile) * GRID.precision,
            rowHeight: (GRID.rowHeight + GRID.gap) / GRID.precision - GRID.gap,
            margin: [GRID.gap, GRID.gap],
            containerPadding: [0, 0],
          }}
          dragConfig={{
            enabled: editing,
            handle: ".widget-drag-handle",
            cancel: "[data-no-drag]",
            threshold: 3,
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
          onDragStart={() => setInteracting(true)}
          onResizeStart={() => setInteracting(true)}
          onDragStop={(next, _old, item) => {
            setInteracting(false);
            apply(fromGridLayout(next), item?.i as WidgetId | undefined);
          }}
          onResizeStop={(next, _old, item) => {
            setInteracting(false);
            apply(fromGridLayout(next), item?.i as WidgetId | undefined);
          }}
        >
          {[...layout]
            .sort((a, b) => a.y - b.y || a.x - b.x)
            .map(({ i }) => {
              const id = i as WidgetId;
              const widget = widgetRegistry[id];
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
                  <WidgetContent id={id} />
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
