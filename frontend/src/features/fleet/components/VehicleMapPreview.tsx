import { ArrowUpRight, Clock3, Gauge, MapPin, X } from "lucide-react";
import { useEffect, useId, useRef } from "react";
import { VehiclePhoto } from "./VehiclePhoto";
import { useVehiclePreferences } from "../model/VehiclePreferences";
import { vehiclePreview } from "../model/vehicle-preview";
import { positionTime, statusLabels, type Vehicle } from "../model/types";

export function VehicleMapPreview({
  vehicle,
  onDetails,
  onClose,
}: {
  vehicle: Vehicle | null;
  onDetails: () => void;
  onClose: () => void;
}) {
  const titleId = useId();
  const ref = useRef<HTMLElement>(null);
  const preferences = useVehiclePreferences();
  const info = vehicle ? vehiclePreview(vehicle) : null;
  useEffect(() => {
    if (vehicle) ref.current?.focus({ preventScroll: true });
  }, [vehicle?.id]);
  return (
    <aside
      ref={ref}
      className="map-vehicle-preview"
      aria-labelledby={titleId}
      aria-busy={!vehicle}
      tabIndex={-1}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.stopPropagation();
          onClose();
        }
      }}
    >
      <header className="map-preview-header">
        {vehicle && (
          <VehiclePhoto src={preferences.photos[vehicle.id]} name={info!.title} />
        )}
        <div>
          <h3 id={titleId}>{info?.title || "Ładowanie pojazdu…"}</h3>
          {info && <p>{info.subtitle}</p>}
        </div>
        <button
          className="icon-button"
          aria-label="Zamknij podgląd pojazdu"
          onClick={onClose}
          title="Zamknij podgląd"
        >
          <X size={16} aria-hidden="true" />
        </button>
      </header>
      {vehicle && info ? (
        <>
          <div className="map-preview-telemetry">
            <span className={`vehicle-status status-${vehicle.status}`}>
              {statusLabels[vehicle.status]}
            </span>
            {info.moving && (
              <span className="map-preview-speed">
                <Gauge size={15} aria-hidden="true" />
                {info.speed === null ? "Brak odczytu prędkości" : `${info.speed} km/h`}
              </span>
            )}
          </div>
          <div className="map-preview-location">
            <MapPin size={16} aria-hidden="true" />
            <div>
              <span>{info.locationLabel}</span>
              <p title={info.address}>{info.address}</p>
            </div>
          </div>
          <footer className="map-preview-footer">
            <span title="Czas pomiaru · czas polski">
              <Clock3 size={13} aria-hidden="true" />
              <span>{vehicle.position_at && "Pomiar · "}{positionTime(vehicle.position_at)}</span>
            </span>
            <button className="button button-secondary" onClick={onDetails}>
              Szczegóły <ArrowUpRight size={15} aria-hidden="true" />
            </button>
          </footer>
        </>
      ) : (
        <p className="map-preview-loading" role="status">Pobieranie danych pojazdu…</p>
      )}
    </aside>
  );
}
