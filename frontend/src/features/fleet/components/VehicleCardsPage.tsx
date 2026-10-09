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
    p.focus(v.id);
    const horizontal = e.key === "ArrowLeft" || e.key === "ArrowRight";
    p.change(
      v.id,
      horizontal
        ? { width: size.width + (e.key === "ArrowLeft" ? -10 : 10) }
        : { height: size.height + (e.key === "ArrowUp" ? -10 : 10) },
    );
  };
  return (
    <article
      className={`vehicle-tile widget ${p.editing ? "tile-editing" : ""} ${p.isSelected(v.id) ? "tile-selected" : ""} ${resize.live ? "tile-resizing" : ""}`}
      style={{ width: current.width, height: current.height }}
      aria-label={`Kafelek ${v.name}`}
      onClick={(e) => {
        if (
          p.editing &&
          !(e.target as Element).closest("button, a, input, select, label")
        )
          p.toggle(v.id);
      }}
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
          <label className="tile-selection">
            <input
              type="checkbox"
              aria-label={`Zaznacz pojazd: ${v.name}`}
              checked={p.isSelected(v.id)}
              onChange={() => p.toggle(v.id)}
            />
            <span>{p.isSelected(v.id) ? "Zaznaczony" : "Wybierz"}</span>
          </label>
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
            onPointerDown={(e) => {
              if (e.button === 0 && e.isPrimary) p.focus(v.id);
              resize.handle.onPointerDown(e);
            }}
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
  const [sizing, setSizing] = useState(false);
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
              ? "Zaznacz kafelki i dopasuj je razem. Narożnik zmienia rozmiar wybranej grupy."
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
              onSize={() => {
                p.focus(v.id);
                setSizing(true);
              }}
              onPhoto={() => setPhoto(v)}
            />
          ))}
        </div>
      )}
      <FleetPagination />
      <VehicleSizeDialog
        open={p.editing && sizing}
        onClose={() => setSizing(false)}
      />
      <VehiclePhotoDialog vehicle={photo} onClose={() => setPhoto(null)} />
    </section>
  );
}
