import { useState, memo, type KeyboardEvent } from "react";
import {
  Camera,
  CarFront,
  MapPin,
  MoveDiagonal2,
  Settings2,
} from "lucide-react";
import { useFleet } from "../model/FleetProvider";
import { useVehiclePreferences } from "../model/VehiclePreferences";
import { positionTime, statusLabels, type Vehicle } from "../model/types";
import { useCardResize } from "./useCardResize";
import { VehiclePhoto } from "./VehiclePhoto";
import { FleetFilters, FleetPagination } from "./FleetControls";
import { FleetNotice } from "./FleetNotice";
import { VehicleSizeDialog } from "./VehicleSizeDialog";
import { VehiclePhotoDialog } from "./VehiclePhotoDialog";
import { EmptyState } from "../../../shared/components/EmptyState";

const VehicleCard = memo(function VehicleCard({
  vehicle: v,
  onSize,
  onPhoto,
}: {
  vehicle: Vehicle;
  onSize: () => void;
  onPhoto: () => void;
}) {
  const f = useFleet();
  const p = useVehiclePreferences();
  const size = p.size(v.id);
  const resize = useCardResize(size, (next) => p.change(v.id, next));
  const current = resize.live ?? size;
  const keyboardResize = (e: KeyboardEvent) => {
    if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key))
      return;
    e.preventDefault();
    p.change(v.id, {
      width:
        size.width +
        (e.key === "ArrowLeft" ? -10 : e.key === "ArrowRight" ? 10 : 0),
      height:
        size.height +
        (e.key === "ArrowUp" ? -10 : e.key === "ArrowDown" ? 10 : 0),
    });
  };
  return (
    <article
      className={`vehicle-tile widget ${p.editing ? "tile-editing" : ""} ${resize.live ? "tile-resizing" : ""}`}
      style={{ width: current.width, height: current.height }}
      aria-label={`Kafelek ${v.name}`}
    >
      <VehiclePhoto src={p.photos[v.id]} name={v.name} />
      <div className="vehicle-tile-body">
        <header>
          <div>
            <h2 title={v.name}>{v.name}</h2>
            <span>{v.license_plate || v.number || "Brak rejestracji"}</span>
          </div>
          <span className={`vehicle-status status-${v.status}`}>
            {statusLabels[v.status]}
          </span>
        </header>
        <dl>
          <div>
            <dt>Przebieg</dt>
            <dd>
              {v.odometer_km === null
                ? "Brak danych"
                : `${v.odometer_km.toLocaleString("pl-PL", { maximumFractionDigits: 0 })} km`}
            </dd>
          </div>
          <div>
            <dt>Kierowca</dt>
            <dd title={v.driver?.display_name}>
              {v.driver?.display_name || "Nieprzypisany"}
            </dd>
          </div>
        </dl>
        <small className="vehicle-tile-time">
          {positionTime(v.position_at)}
          {v.latitude === null && " · Brak GPS"}
        </small>
        <footer>
          <a
            className="button button-secondary"
            href="#map"
            onClick={() => f.select(v.id)}
          >
            <MapPin size={14} />
            Na mapie
          </a>
          <button
            className="icon-button"
            aria-label={`Zdjęcie: ${v.name}`}
            title="Zdjęcie pojazdu"
            disabled={p.photosLoading}
            onClick={onPhoto}
          >
            <Camera size={17} />
          </button>
        </footer>
      </div>
      {p.editing && (
        <>
          <button
            className="tile-size-button icon-button"
            aria-label={`Rozmiar: ${v.name}`}
            title="Rozmiar kafelka"
            onClick={onSize}
          >
            <Settings2 size={17} />
          </button>
          <button
            className="tile-resize-handle icon-button"
            aria-label={`Zmień rozmiar: ${v.name}`}
            title="Przeciągnij lub użyj strzałek; Enter otwiera ustawienia"
            {...resize.handle}
            onKeyDown={keyboardResize}
            onClick={(e) => {
              if (e.detail === 0) onSize();
            }}
          >
            <MoveDiagonal2 size={18} />
          </button>
        </>
      )}
    </article>
  );
});
export function VehicleCardsPage() {
  const f = useFleet();
  const p = useVehiclePreferences();
  const [sizing, setSizing] = useState<Vehicle | null>(null);
  const [photo, setPhoto] = useState<Vehicle | null>(null);
  return (
    <section
      className="vehicle-gallery"
      aria-label="Kafelki pojazdów"
      aria-busy={f.loading}
    >
      <div className="vehicle-gallery-toolbar widget">
        <FleetFilters />
        <FleetNotice />
        <div className="vehicle-gallery-hint">
          <span>
            {f.list ? `${f.list.total} pojazdów` : "Lista floty"} ·{" "}
            {p.editing
              ? "Rozciągnij narożnik lub otwórz rozmiar kafelka."
              : "Twój widok floty. Każdy kafelek ma własny rozmiar."}
          </span>
          {!p.persistent && (
            <span role="status">
              Układ działa w tej sesji — zapis przeglądarki jest niedostępny.
            </span>
          )}
        </div>
      </div>
      {!f.list?.items.length ? (
        <EmptyState
          icon={CarFront}
          title={
            f.loading ? "Pobieranie pojazdów…" : "Brak pasujących pojazdów"
          }
          description={f.error || "Zmień filtry lub poczekaj na dane floty."}
        />
      ) : (
        <div className="vehicle-gallery-grid">
          {f.list.items.map((v) => (
            <VehicleCard
              key={v.id}
              vehicle={v}
              onSize={() => setSizing(v)}
              onPhoto={() => setPhoto(v)}
            />
          ))}
        </div>
      )}
      <FleetPagination />
      <VehicleSizeDialog
        vehicle={p.editing ? sizing : null}
        onClose={() => setSizing(null)}
      />
      <VehiclePhotoDialog vehicle={photo} onClose={() => setPhoto(null)} />
    </section>
  );
}
