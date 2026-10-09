import { Truck } from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { EmptyState } from "../../../shared/components/EmptyState";
import { useFleet } from "../model/FleetProvider";
import { positionTime, statusLabels } from "../model/types";
import { FleetNotice } from "./FleetNotice";
import { FleetFilters, FleetPagination } from "./FleetControls";
export function VehicleListWidget({
  variant = "table",
}: {
  variant?: "table" | "sidebar";
}) {
  const f = useFleet();
  const items = f.list?.items || [];
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
            title={
              f.loading
                ? "Pobieranie pojazdów…"
                : f.error
                  ? "Lista chwilowo niedostępna"
                  : "Brak pasujących pojazdów"
            }
            description={
              f.error || "Zmień filtry lub poczekaj na aktualizację floty."
            }
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
                <small>
                  {positionTime(v.position_at)}
                  {v.latitude === null && <span>Brak GPS</span>}
                </small>
              </button>
            ))}
          </div>
        ) : (
          <div className="table-scroll">
            <table className="vehicle-table">
              <thead>
                <tr>
                  <th>Pojazd</th>
                  <th>Status</th>
                  <th>Kierowca</th>
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
                    <td>
                      <span className={`vehicle-status status-${v.status}`}>
                        {statusLabels[v.status]}
                      </span>
                      {v.latitude === null && (
                        <small className="no-gps">Brak GPS</small>
                      )}
                    </td>
                    <td>{v.driver?.display_name || "Nieprzypisany"}</td>
                    <td>
                      {v.odometer_km === null
                        ? "—"
                        : `${v.odometer_km.toLocaleString("pl-PL", { maximumFractionDigits: 1 })} km`}
                    </td>
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
