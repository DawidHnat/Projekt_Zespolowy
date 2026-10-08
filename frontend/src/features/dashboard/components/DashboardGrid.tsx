import { LayoutEditingContext } from "../../../shared/components/LayoutEditingContext";
import {
  cloneElement,
  memo,
  useCallback,
  useId,
  useMemo,
  useState,
  type KeyboardEvent,
} from "react";
import {
  gridBounds,
  minMaxSize,
  verticalCompactor,
  type LayoutConstraint,
} from "react-grid-layout/core";
import GridLayout, {
  useContainerWidth,
  type Layout,
  type LayoutItem,
  type GridLayoutProps,
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
import { useGesturePaint } from "./useGesturePaint";
import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";

export type DashboardGridProps = {
  section: SectionId;
  ids: WidgetId[];
  layouts: SavedLayouts;
  editing: boolean;
  onLayout: (
    section: SectionId,
    profile: LayoutProfile,
    layout: Layout,
  ) => void;
  onHide?: (id: WidgetId) => void;
};

// Domain widgets do not rerender while the interaction engine moves their frame.
const WidgetContent = memo(function WidgetContent({
  id,
  section,
}: {
  id: WidgetId;
  section: SectionId;
}) {
  const widget = widgetRegistry[id];
  const Component = widget.presentations?.[section] ?? widget.component;
  return <Component />;
});

export function DashboardGrid({
  section,
  ids,
  layouts,
  editing,
  onLayout,
  onHide,
}: DashboardGridProps) {
  const { width, containerRef, mounted } = useContainerWidth({
    measureBeforeMount: true,
  });
  const profile: LayoutProfile = width < 720 ? "compact" : "desktop";
  const [interacting, setInteracting] = useState(false);
  const gesturePaint = useGesturePaint();
  const keyboardHelpId = useId();
  const signature = `${section}-${profile}-${ids.join(",")}-${mounted}-${editing}`;
  const minimums = useWidgetMinimums(containerRef, signature, interacting);
  const layout = useMemo(
    () =>
      fitLayout(
        visibleLayout(layouts[section][profile], ids, profile),
        profile,
        width,
        minimums,
        section,
      ),
    [layouts, section, ids, profile, width, minimums],
  );
  const gridLayout = useMemo(() => toGridLayout(layout), [layout]);
  const gridConfig = useMemo(
    () => ({
      cols: columns(profile) * GRID.precision,
      rowHeight: (GRID.rowHeight + GRID.gap) / GRID.precision - GRID.gap,
      margin: [GRID.gap, GRID.gap] as const,
      containerPadding: [0, 0] as const,
    }),
    [profile],
  );
  const constraints = useMemo<LayoutConstraint[]>(
    () => [
      gridBounds,
      minMaxSize,
      {
        name: "widget-content",
        constrainSize(item, w, h) {
          const pixels =
            profile === "compact"
              ? width
              : widthPixels(w / GRID.precision, width);
          const minH = heightUnits(minimumHeight(item.i as WidgetId, pixels));
          return { w, h: Math.max(h, minH * GRID.precision) };
        },
      },
    ],
    [profile, width],
  );
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
  const update = useCallback(
    (id: WidgetId, change: Partial<Pick<LayoutItem, "x" | "y" | "w" | "h">>) =>
      apply(changeWidget(layout, id, profile, change, section), id),
    [layout, profile, section, apply],
  );
  const move = useCallback(
    (id: WidgetId, direction: string) => {
      const item = layout.find((value) => value.i === id)!;
      const offsets: Record<string, { x?: number; y?: number }> = {
        ArrowLeft: { x: item.x - 0.5 },
        ArrowRight: { x: item.x + 0.5 },
        ArrowUp: { y: item.y - 1 },
        ArrowDown: { y: item.y + item.h },
      };
      update(id, offsets[direction]);
    },
    [layout, update],
  );
  const keyboard = useCallback(
    (event: KeyboardEvent<HTMLButtonElement>, id: WidgetId) => {
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
            (event.key === "ArrowRight"
              ? 0.5
              : event.key === "ArrowLeft"
                ? -0.5
                : 0),
          h:
            item.h +
            (event.key === "ArrowDown"
              ? 0.5
              : event.key === "ArrowUp"
                ? -0.5
                : 0),
        });
      else move(id, event.key);
    },
    [layout, update, move],
  );
  const children = useMemo(
    () =>
      [...layout]
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
                    aria-describedby={keyboardHelpId}
                    onKeyDown={(event) => keyboard(event, id)}
                    onClick={(event) => {
                      if (event.detail === 0) setSelected(id);
                    }}
                    title="Chwyć kafelek lub przesuń go strzałkami"
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
              <WidgetContent id={id} section={section} />
            </div>
          );
        }),
    [layout, section, editing, keyboardHelpId, keyboard],
  );
  // Keep inactive children stable while requesting a sub-cell paint of the held card.
  const paintedChildren = useMemo(
    () =>
      children.map((child) =>
        child.key === gesturePaint.gesture?.id ? cloneElement(child) : child,
      ),
    [children, gesturePaint.gesture],
  );
  const startGesture = useCallback(
    (_layout: Layout, _old: LayoutItem | null, item: LayoutItem | null) => {
      if (!item) return;
      setInteracting(true);
      gesturePaint.start(item.i as WidgetId);
    },
    [gesturePaint.start],
  );
  const stopGesture = useCallback(
    (next: Layout, _old: LayoutItem | null, item: LayoutItem | null) => {
      gesturePaint.stop();
      setInteracting(false);
      apply(fromGridLayout(next), item?.i as WidgetId | undefined);
    },
    [gesturePaint.stop, apply],
  );
  const previewDrag = useCallback<NonNullable<GridLayoutProps["onDrag"]>>(
    (next, _old, item, placeholder) => {
      // RGL creates its placeholder before moving/compacting the item. Project the
      // final slot here so the highlight agrees with the layout committed on release.
      if (item && placeholder) {
        const target = verticalCompactor
          .compact(next, gridConfig.cols)
          .find((value) => value.i === item.i);
        if (target)
          Object.assign(placeholder, {
            x: target.x,
            y: target.y,
            w: target.w,
            h: target.h,
          });
      }
      gesturePaint.paint();
    },
    [gesturePaint.paint, gridConfig.cols],
  );
  return (
    <LayoutEditingContext value={editing}>
      <div
        ref={containerRef}
        className={`dashboard-canvas ${editing ? "is-editing" : ""} ${interacting ? "is-interacting" : ""}`}
        data-profile={profile}
      >
        <p className="sr-only" id={keyboardHelpId}>
          Przesuwaj strzałkami. Shift i strzałki zmieniają rozmiar. Enter
          otwiera ustawienia.
        </p>
        <span className="sr-only" role="status" aria-live="polite">
          {announcement}
        </span>
        {editing && (
          <p className="sr-only">
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
            gridConfig={gridConfig}
            dragConfig={{
              enabled: editing,
              cancel:
                "[data-no-drag],button:not(.widget-drag-handle),a,input,select,textarea,[contenteditable]",
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
            onDragStart={startGesture}
            onDrag={previewDrag}
            onResizeStart={startGesture}
            onResize={gesturePaint.paint}
            onDragStop={stopGesture}
            onResizeStop={stopGesture}
          >
            {paintedChildren}
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
          onHide={
            onHide
              ? () => {
                  if (selected) onHide(selected);
                  setSelected(null);
                }
              : undefined
          }
        />
      </div>
    </LayoutEditingContext>
  );
}
