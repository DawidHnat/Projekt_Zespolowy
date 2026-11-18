import { useEffect, useRef } from "react";
import { Camera, X, Trash2 } from "lucide-react";
import type { Vehicle } from "../model/types";
import { useVehiclePreferences } from "../model/VehiclePreferences";
import { VehiclePhoto } from "./VehiclePhoto";

export function VehiclePhotoDialog({
  vehicle,
  onClose,
}: {
  vehicle: Vehicle | null;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const p = useVehiclePreferences();
  useEffect(() => {
    if (vehicle && !ref.current?.open) ref.current?.showModal();
    if (!vehicle) ref.current?.close();
  }, [vehicle]);
  return (
    <dialog
      ref={ref}
      className="widget-settings-dialog"
      aria-labelledby="vehicle-photo-title"
      onClose={onClose}
    >
      {vehicle && (
        <>
          <header className="panel-header">
            <div>
              <span className="eyebrow">ZDJĘCIE POJAZDU</span>
              <h2 id="vehicle-photo-title">{vehicle.name}</h2>
            </div>
            <button
              className="icon-button"
              aria-label="Zamknij zdjęcie pojazdu"
              onClick={onClose}
            >
              <X size={20} />
            </button>
          </header>
          <div className="vehicle-photo-settings">
            <VehiclePhoto src={p.photos[vehicle.id]} name={vehicle.name} />
            <p>
              To samo zdjęcie zobaczysz na kafelku i jako znacznik na mapie.
            </p>
            <p>
              Tylko na tym urządzeniu i w tej przeglądarce, dla Twojego konta.
              Zdjęcie nie jest wysyłane na serwer ani współdzielone z zespołem.
            </p>
            <label className="button button-primary photo-upload">
              <Camera size={17} />
              {p.busy === vehicle.id
                ? "Przygotowywanie…"
                : p.photos[vehicle.id]
                  ? "Zmień zdjęcie"
                  : "Dodaj zdjęcie"}
              <input
                type="file"
                aria-label="Zdjęcie pojazdu"
                accept="image/jpeg,image/png,image/webp"
                disabled={!!p.busy || p.photosLoading}
                onChange={(e) => {
                  const file = e.currentTarget.files?.[0];
                  e.currentTarget.value = "";
                  if (file) void p.upload(vehicle.id, file);
                }}
              />
            </label>
            {p.photos[vehicle.id] && (
              <button
                className="button button-secondary"
                disabled={!!p.busy || p.photosLoading}
                onClick={() => void p.remove(vehicle.id)}
              >
                <Trash2 size={16} />
                Usuń zdjęcie
              </button>
            )}
            {p.photoError && (
              <p role="alert" className="photo-error">
                {p.photoError}
              </p>
            )}
            <small>
              JPG, PNG lub WebP · do 10 MB. Zdjęcie zapisuje się od razu.
              Wyczyszczenie danych przeglądarki usuwa lokalne zdjęcie.
            </small>
          </div>
          <footer className="widget-settings-footer">
            <button
              className="button button-primary"
              disabled={!!p.busy}
              onClick={onClose}
            >
              Gotowe
            </button>
          </footer>
        </>
      )}
    </dialog>
  );
}
