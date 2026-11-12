import { Truck } from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { EmptyState } from "../../../shared/components/EmptyState";
import { useFleet } from "../model/FleetProvider";
import {
  measurementLabel,
  positionCoordinates,
  positionTime,
  statusLabels,
} from "../model/types";
import { FleetNotice } from "./FleetNotice";
import { FleetFilters, FleetPagination } from "./FleetControls";
export function VehicleListWidget({
  variant = "table",
}: {
  variant?: "table" | "sidebar";
}) {
  const f = useFleet();
  const items = f.list?.items || [];
  const isFiltered = Boolean(f.q.trim() || f.status);
  const emptyTitle = f.loading
    ? "Pobieranie pojazdów…"
    : f.error
      ? "Lista chwilowo niedostępna"
      : isFiltered
        ? "Brak wyników"
        : "Flota jest pusta";
  const emptyDescription = f.error || (isFiltered
    ? "Nie znaleziono pojazdów dla wybranych filtrów."
    : "Nie ma jeszcze pojazdów do wyświetlenia.");
  return (
    <WidgetFrame
      title="Pojazdy"
      icon={Truck}
      badge={f.list ? `${f.list.total} pojazdów` : "Lista floty"}
      className={`vehicles-widget vehicle-${variant}`}
    >
      <div className="fleet-list-content" aria-busy={f.loading}>
        <FleetFilters />
        <FleetNotice />
        {!items.length ? (
          <EmptyState
            icon={Truck}
            title={emptyTitle}
            description={emptyDescription}
          />
        ) : variant === "sidebar" ? (
          <div className="vehicle-cards">
            {items.map((v) => (
              <button
                key={v.id}
                className={`vehicle-card ${f.selectedId === v.id ? "selected" : ""}`}
                onClick={() => f.select(v.id)}
                aria-pressed={f.selectedId === v.id}
              >
                <div>
                  <strong>{v.name}</strong>
                  <small>
                    {v.license_plate || v.number || "Brak rejestracji"}
                  </small>
                </div>
                <span className={`vehicle-status status-${v.status}`}>
                  {statusLabels[v.status]}
                </span>
                <small className="vehicle-card-position">
                  {positionCoordinates(v.latitude, v.longitude)}
                </small>
                <small className="vehicle-card-measurements">
                  <span>Prędkość · {measurementLabel(v.speed_kmh, "km/h", 0)}</span>
                  <span>Przebieg · {measurementLabel(v.odometer_km, "km")}</span>
                </small>
                <small className="vehicle-card-time">{positionTime(v.position_at)}</small>
              </button>
            ))}
          </div>
        ) : (
          <div className="table-scroll">
            <table className="vehicle-table">
              <thead>
                <tr>
                  <th>Pojazd</th>
                  <th>GPS</th>
                  <th>Status</th>
                  <th>Kierowca</th>
                  <th>Prędkość</th>
                  <th>Przebieg</th>
                  <th>Pomiar · czas polski</th>
                </tr>
              </thead>
              <tbody>
                {items.map((v) => (
                  <tr
                    key={v.id}
                    className={f.selectedId === v.id ? "selected" : ""}
                  >
                    <td>
                      <button
                        className="vehicle-name"
                        onClick={() => f.select(v.id)}
                        aria-pressed={f.selectedId === v.id}
                      >
                        <strong>{v.name}</strong>
                        <small>
                          {v.license_plate || v.number || "Brak rejestracji"}
                        </small>
                      </button>
                    </td>
                    <td>{positionCoordinates(v.latitude, v.longitude)}</td>
                    <td>
                      <span className={`vehicle-status status-${v.status}`}>
                        {statusLabels[v.status]}
                      </span>
                    </td>
                    <td>{v.driver?.display_name || "Nieprzypisany"}</td>
                    <td>{measurementLabel(v.speed_kmh, "km/h", 0)}</td>
                    <td>{measurementLabel(v.odometer_km, "km")}</td>
                    <td>{positionTime(v.position_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <FleetPagination />
      </div>
    </WidgetFrame>
  );
}
export function VehicleSidebarWidget() {
  return <VehicleListWidget variant="sidebar" />;
}
