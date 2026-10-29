import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Users } from "lucide-react";
import { useAuth } from "../auth/AuthProvider";
import {
  DriverProvider,
  useDrivers,
  type DriverSort,
} from "./model/DriverContext";
import { useDriverPreferences } from "./model/preferences";
import { DriverCard } from "./components/DriverCard";
import {
  DriverDetailsPanel,
  type DriverPanel,
} from "./components/DriverDetailsPanel";
import { DashboardGrid } from "../dashboard/components/DashboardGrid";
import { LayoutEditorControls } from "../dashboard/components/LayoutEditorControls";
import {
  mergeLayout,
  normalizeLayouts,
} from "../dashboard/model/widget-layout";
import {
  DRIVER_WIDGET_IDS,
  type WidgetId,
} from "../dashboard/model/widget-types";
import { widgetRegistry } from "../dashboard/model/widget-registry";
import {
  CARD_MAX,
  CARD_MIN,
  cardSize,
  resizeCards,
  targetSizes,
  type CardSize,
} from "../../shared/model/card-layout";
import { ListPagination } from "../../shared/components/ListPagination";
import { EmptyState } from "../../shared/components/EmptyState";

type Preferences = ReturnType<typeof useDriverPreferences>;
export function DriversPage() {
  const { user } = useAuth();
  return user ? <AccountDriversPage key={user.id} userId={user.id} /> : null;
}
function AccountDriversPage({ userId }: { userId: string }) {
  const preferences = useDriverPreferences(userId);
  return (
    <DriverProvider customOrder={preferences.saved.order}>
      <DriverWorkspace preferences={preferences} />
    </DriverProvider>
  );
}
function DriverWorkspace({ preferences: p }: { preferences: Preferences }) {
  const { user } = useAuth();
  const d = useDrivers();
  const canEdit = user?.role === "admin" || user?.role === "editor";
  const [panel, setPanel] = useState<DriverPanel | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [scope, setScope] = useState<"all" | "selected">("all");
  const [sizesOpen, setSizesOpen] = useState(false);
  const [layoutNotice, setLayoutNotice] = useState<string | null>(null);
  const opener = useRef<HTMLElement | null>(null);
  const previousSort = useRef<DriverSort>("name_asc");
  const sizeControls = useRef<HTMLElement>(null);
  const editing = !!p.draft;
  const geometry = useMemo(
    () => ({ ...normalizeLayouts(null), drivers: p.effective.layouts }),
    [p.effective.layouts],
  );
  const display = useMemo(() => {
    const rows = [...(d.data?.items ?? [])];
    if (editing && d.filters.sort === "custom") {
      const ranks = new Map(p.effective.order.map((id, index) => [id, index]));
      rows.sort(
        (a, b) => (ranks.get(a.id) ?? Infinity) - (ranks.get(b.id) ?? Infinity),
      );
    }
    return rows;
  }, [d.data, d.filters.sort, editing, p.effective.order]);
  const rowIds = useMemo(() => display.map((person) => person.id), [display]);
  useEffect(() => {
    if (
      !editing ||
      d.filters.sort !== "custom" ||
      !d.data ||
      d.data.page !== d.page
    )
      return;
    const additional = d.data.items
      .map((person) => person.id)
      .filter((id) => !p.effective.order.includes(id));
    if (additional.length)
      p.update((value) => ({
        ...value,
        order: [...value.order, ...additional].slice(0, 2000),
      }));
  }, [editing, d.filters.sort, d.data, d.page, p.effective.order]);
  const open = (id: string | null, mode: DriverPanel["mode"]) => {
    opener.current = document.activeElement as HTMLElement;
    setPanel({ id, mode });
  };
  const close = useCallback(() => {
    setPanel(null);
    requestAnimationFrame(() => {
      if (opener.current?.isConnected) opener.current.focus();
      else document.getElementById("main-content")?.focus();
    });
  }, []);
  const toggle = (id: string) => {
    setScope("selected");
    setSelected((value) =>
      value.includes(id) ? value.filter((item) => item !== id) : [...value, id],
    );
  };
  const resize = (patch: Partial<CardSize>, identity?: string) => {
    const target =
      scope === "all"
        ? "all"
        : identity && !selected.includes(identity)
          ? [identity]
          : selected;
    p.update((value) => ({
      ...value,
      cards: resizeCards(value.cards, target, patch),
    }));
  };
  const reorder = (identity: string, destination: string) => {
    if (
      !editing ||
      !rowIds.includes(identity) ||
      !rowIds.includes(destination) ||
      identity === destination
    )
      return;
    d.change({ sort: "custom" });
    p.update((value) => {
      const order = [...new Set([...value.order, ...rowIds])];
      const source = order.indexOf(identity),
        target = order.indexOf(destination);
      order.splice(source, 1);
      order.splice(target, 0, identity);
      return { ...value, order: order.slice(0, 2000) };
    });
    setLayoutNotice(
      "Zmieniono szkic kolejności. Zapisz układ, aby go zachować.",
    );
  };
  const group = targetSizes(
    p.effective.cards,
    scope === "all" ? "all" : selected,
  );
  useEffect(() => {
    if (sizesOpen)
      sizeControls.current
        ?.querySelector<HTMLInputElement>('input[type="range"]')
        ?.focus();
  }, [sizesOpen]);
  return (
    <div className="drivers-page">
      <div className="driver-page-actions">
        <p>
          Tylko na tym urządzeniu i w tej przeglądarce: widok, układ i rozmiary
          kafelków.
        </p>
        <LayoutEditorControls
          title="Kierowcy"
          editing={editing}
          onEdit={() => {
            previousSort.current = d.filters.sort;
            p.start();
            setSelected([]);
            setLayoutNotice(null);
          }}
          onSave={() => {
            p.save();
            setSizesOpen(false);
            setLayoutNotice("Układ kierowców został zapisany.");
            d.setPage(1);
          }}
          onCancel={() => {
            p.cancel();
            d.change({ sort: previousSort.current });
            setSizesOpen(false);
            setLayoutNotice("Odrzucono szkic układu kierowców.");
          }}
          onReset={() => {
            p.reset();
            setSelected([]);
            setLayoutNotice(
              "Przywrócono domyślny szkic. Zapisz układ, aby zachować zmianę.",
            );
          }}
        />
      </div>
      {!p.persistent && (
        <p role="status">
          Układ działa w tej sesji. Zapis przeglądarki jest niedostępny.
        </p>
      )}
      {layoutNotice && <p role="status">{layoutNotice}</p>}
      {editing && (
        <fieldset className="driver-widget-choices">
          <legend>Moduły przeglądu kierowców</legend>
          {DRIVER_WIDGET_IDS.map((id) => (
            <label key={id} className="driver-checkbox">
              <input
                type="checkbox"
                checked={p.effective.visible.includes(id)}
                onChange={() =>
                  p.update((value) => ({
                    ...value,
                    visible: value.visible.includes(id)
                      ? value.visible.filter((item) => item !== id)
                      : [...value.visible, id],
                  }))
                }
              />
              {widgetRegistry[id].title}
            </label>
          ))}
        </fieldset>
      )}
      {p.effective.visible.length ? (
        <DashboardGrid
          section="drivers"
          ids={p.effective.visible}
          layouts={geometry}
          editing={editing}
          onLayout={(_, profile, layout) =>
            p.update((value) => ({
              ...value,
              layouts: {
                ...value.layouts,
                [profile]: mergeLayout(
                  value.layouts[profile],
                  layout,
                  profile,
                  "drivers",
                ),
              },
            }))
          }
          onHide={(id: WidgetId) =>
            p.update((value) => ({
              ...value,
              visible: value.visible.filter((item) => item !== id),
            }))
          }
        />
      ) : (
        <p>
          Moduły przeglądu są ukryte. Możesz je włączyć podczas edycji układu.
        </p>
      )}
      <section
        className="widget driver-directory"
        aria-label="Kartoteka kierowców"
        aria-busy={d.loading}
      >
        <header className="driver-directory-header">
          <h2>Kartoteka kierowców</h2>
          <div className="driver-actions">
            <div role="group" aria-label="Prezentacja kierowców">
              <button
                className="button button-secondary"
                aria-pressed={p.effective.view === "list"}
                onClick={() => p.setView("list")}
              >
                Lista
              </button>
              <button
                className="button button-secondary"
                aria-pressed={p.effective.view === "cards"}
                onClick={() => p.setView("cards")}
              >
                Kafelki
              </button>
            </div>
            {canEdit && (
              <button
                className="button button-primary"
                disabled={editing}
                onClick={() => open(null, "create")}
              >
                Dodaj kierowcę
              </button>
            )}
          </div>
        </header>
        <div className="driver-filters">
          <label>
            Szukaj kierowcy
            <input
              type="search"
              value={d.filters.q}
              maxLength={200}
              disabled={editing}
              placeholder="Osoba, kontakt lub pojazd"
              onChange={(event) => d.change({ q: event.target.value })}
            />
          </label>
          <label>
            Aktywność
            <select
              aria-label="Aktywność kierowców"
              value={d.filters.active}
              disabled={editing}
              onChange={(event) =>
                d.change({
                  active: event.target.value as typeof d.filters.active,
                })
              }
            >
              <option value="all">Wszyscy</option>
              <option value="active">Aktywni</option>
              <option value="inactive">Nieaktywni</option>
            </select>
          </label>
          <label>
            Przypisania
            <select
              aria-label="Filtr przypisań kierowców"
              value={d.filters.assigned}
              disabled={editing}
              onChange={(event) =>
                d.change({
                  assigned: event.target.value as typeof d.filters.assigned,
                })
              }
            >
              <option value="all">Wszystkie osoby</option>
              <option value="with">Z pojazdem</option>
              <option value="without">Bez pojazdu</option>
            </select>
          </label>
          <label>
            Kategorie
            <select
              aria-label="Filtr kategorii kierowców"
              value={d.filters.category}
              disabled={editing || !d.catalog}
              onChange={(event) => d.change({ category: event.target.value })}
            >
              <option value="">Wszystkie</option>
              <option value="missing">Brak wpisanych kategorii</option>
              {d.catalog?.items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Kolejność
            <select
              aria-label="Kolejność kierowców"
              value={d.filters.sort}
              disabled={editing}
              onChange={(event) => {
                d.change({ sort: event.target.value as DriverSort });
              }}
            >
              <option value="name_asc">Nazwisko A–Z</option>
              <option value="name_desc">Nazwisko Z–A</option>
              <option value="vehicles_desc">Najwięcej pojazdów</option>
              <option value="vehicles_asc">Najmniej pojazdów</option>
              <option value="custom">Własna kolejność</option>
            </select>
          </label>
          <button
            className="button button-secondary"
            disabled={d.loading || editing}
            onClick={d.refresh}
          >
            Odśwież kierowców
          </button>
        </div>
        <p className="driver-note">
          Kategorie są wpisane ręcznie. Ocena zgodności kierowca–pojazd nie jest
          jeszcze dostępna.
        </p>
        {d.catalogError && (
          <p role="alert">
            Nie można pobrać kategorii.{" "}
            <button
              className="button button-secondary"
              onClick={d.retryCatalog}
            >
              Ponów kategorie
            </button>
          </p>
        )}
        {d.error && <p role="alert">{d.error}</p>}
        {d.loading && !d.data && <p role="status">Pobieranie kierowców…</p>}
        {d.data && (
          <>
            {!display.length ? (
              <EmptyState
                icon={Users}
                title="Brak kierowców w tym widoku"
                description="Zmień filtry lub dodaj kierowcę ręcznie, jeśli masz uprawnienia do edycji."
              />
            ) : p.effective.view === "list" ? (
              <div
                className="driver-table-wrap"
                role="region"
                aria-label="Lista kierowców"
                tabIndex={0}
              >
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Kierowca</th>
                      <th scope="col">Kontakt</th>
                      <th scope="col">Wpisane kategorie</th>
                      <th scope="col">Pojazdy</th>
                      <th scope="col">Działania</th>
                    </tr>
                  </thead>
                  <tbody>
                    {display.map((person) => (
                      <tr key={person.id}>
                        <td>
                          <button
                            className="driver-name"
                            disabled={editing}
                            onClick={() => open(person.id, "view")}
                          >
                            {person.display_name}
                          </button>
                          <small>
                            {person.identifier ||
                              "Identyfikator do uzupełnienia"}{" "}
                            · {person.active ? "Aktywny" : "Nieaktywny"}
                          </small>
                        </td>
                        <td>
                          {person.phone ? (
                            <a
                              href={`tel:${person.phone.replace(/[^+0-9]/g, "")}`}
                            >
                              {person.phone}
                            </a>
                          ) : (
                            "Brak telefonu"
                          )}
                          <br />
                          {person.email ? (
                            <a
                              href={`mailto:${encodeURIComponent(person.email)}`}
                            >
                              {person.email}
                            </a>
                          ) : (
                            "Brak e-maila"
                          )}
                        </td>
                        <td>
                          {person.categories.join(", ") ||
                            "Brak wpisanych kategorii"}
                        </td>
                        <td>
                          {person.first_vehicle ? (
                            <>
                              {person.first_vehicle.name}
                              {person.vehicles_total > 1 && (
                                <button
                                  className="driver-more"
                                  disabled={editing}
                                  aria-label={`+${person.vehicles_total - 1} poj. — pozostałe pojazdy: ${person.display_name}`}
                                  onClick={() => open(person.id, "assignments")}
                                >
                                  +{person.vehicles_total - 1} poj.
                                </button>
                              )}
                            </>
                          ) : (
                            "Brak pojazdów"
                          )}
                        </td>
                        <td>
                          <div className="driver-actions">
                            <button
                              className="button button-secondary"
                              disabled={editing}
                              onClick={() => open(person.id, "view")}
                            >
                              Szczegóły
                            </button>
                            {canEdit && (
                              <button
                                className="button button-secondary"
                                disabled={editing}
                                onClick={() => open(person.id, "edit")}
                              >
                                Edytuj
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="driver-cards">
                {display.map((person, index) => (
                  <DriverCard
                    key={person.id}
                    profile={person}
                    size={cardSize(p.effective.cards, person.id)}
                    editing={editing}
                    selected={selected.includes(person.id)}
                    canEdit={canEdit}
                    onSelect={() => toggle(person.id)}
                    onOpen={(assignments) =>
                      open(person.id, assignments ? "assignments" : "view")
                    }
                    onEdit={() => open(person.id, "edit")}
                    onSize={() => {
                      setSelected([person.id]);
                      setScope("selected");
                      setSizesOpen(true);
                    }}
                    onResize={(size) => resize(size, person.id)}
                    onDrag={reorder}
                    onMove={(direction) => {
                      const target = display[index + direction];
                      if (target) reorder(person.id, target.id);
                    }}
                  />
                ))}
              </div>
            )}
            <ListPagination
              label="Kierowcy"
              page={d.page}
              pageSize={d.pageSize}
              total={d.data.total}
              loading={d.loading}
              onPage={d.setPage}
              onPageSize={d.setPageSize}
            />
          </>
        )}
        {editing && p.effective.view === "cards" && (
          <section
            ref={sizeControls}
            className="driver-size-controls"
            aria-label="Rozmiary kafelków kierowców"
          >
            <button
              className="button button-secondary"
              onClick={() => setSizesOpen((value) => !value)}
            >
              Rozmiary kafelków
            </button>
            {sizesOpen && (
              <fieldset>
                <legend>Rozmiar kafelków kierowców</legend>
                <label className="driver-checkbox">
                  <input
                    type="radio"
                    name="driver-resize-scope"
                    checked={scope === "all"}
                    onChange={() => setScope("all")}
                  />
                  Wszyscy kierowcy, także poza stroną
                </label>
                <label className="driver-checkbox">
                  <input
                    type="radio"
                    name="driver-resize-scope"
                    checked={scope === "selected"}
                    disabled={!selected.length}
                    onChange={() => setScope("selected")}
                  />
                  Zaznaczeni ({selected.length})
                </label>
                {(["width", "height"] as const).map((axis) => (
                  <label key={axis}>
                    {axis === "width" ? "Szerokość" : "Wysokość"}
                    <output>
                      {(axis === "width" ? group.mixedWidth : group.mixedHeight)
                        ? "Różne rozmiary"
                        : `${group.first[axis]} px`}
                    </output>
                    <input
                      type="range"
                      aria-label={
                        axis === "width"
                          ? "Szerokość kafelka kierowcy"
                          : "Wysokość kafelka kierowcy"
                      }
                      min={CARD_MIN[axis]}
                      max={CARD_MAX[axis]}
                      step={10}
                      value={group.first[axis]}
                      onChange={(event) =>
                        resize({ [axis]: Number(event.target.value) })
                      }
                    />
                  </label>
                ))}
              </fieldset>
            )}
            <p>
              Własna kolejność jest oddzielna od sortowania A–Z. Podczas edycji
              przeciągaj uchwyt lub użyj Wyżej/Niżej. Rozmiar zmienisz uchwytem,
              strzałkami lub suwakiem. Zapisz układ, aby zachować szkic.
            </p>
          </section>
        )}
      </section>
      {panel && (
        <DriverDetailsPanel
          key={panel.id || "new"}
          panel={panel}
          onClose={close}
        />
      )}
    </div>
  );
}
