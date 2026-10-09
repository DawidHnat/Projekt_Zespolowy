import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { CARD_MIN, CARD_MAX } from "../model/vehicle-layout";
import { useVehiclePreferences } from "../model/VehiclePreferences";
import type { Vehicle } from "../model/types";

export function VehicleSizeDialog({
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
  const size = vehicle ? p.size(vehicle.id) : CARD_MIN;
  return (
    <dialog
      ref={ref}
      className="widget-settings-dialog"
      aria-labelledby="vehicle-size-title"
      onClose={onClose}
    >
      {vehicle && (
        <>
          <header className="panel-header">
            <div>
              <span className="eyebrow">ROZMIAR KAFELKA</span>
              <h2 id="vehicle-size-title">{vehicle.name}</h2>
            </div>
            <button
              className="icon-button"
              aria-label="Zamknij rozmiar kafelka"
              onClick={onClose}
            >
              <X size={20} />
            </button>
          </header>
          <div className="widget-settings-content">
            <p>
              Zmieniasz tylko ten pojazd. Zatwierdź później przyciskiem „Zapisz
              układ”.
            </p>
            {(["width", "height"] as const).map((axis) => (
              <label key={axis} className="size-control">
                {axis === "width" ? "Szerokość" : "Wysokość"}
                <output>{size[axis]} px</output>
                <input
                  type="range"
                  aria-label={
                    axis === "width" ? "Szerokość kafelka" : "Wysokość kafelka"
                  }
                  min={CARD_MIN[axis]}
                  max={CARD_MAX[axis]}
                  step={10}
                  value={size[axis]}
                  onChange={(e) =>
                    p.change(vehicle.id, {
                      ...size,
                      [axis]: Number(e.target.value),
                    })
                  }
                />
              </label>
            ))}
            <div className="size-presets">
              {[
                { name: "Mały", width: 280, height: 420 },
                { name: "Standardowy", width: 320, height: 440 },
                { name: "Duży", width: 480, height: 500 },
              ].map(({ name, ...next }) => (
                <button
                  key={name}
                  className="button button-secondary"
                  onClick={() => p.change(vehicle.id, next)}
                >
                  {name}
                </button>
              ))}
            </div>
            <p>
              Minimum zachowuje zdjęcie, nazwę, status i podstawowe dane. Na
              mniejszym ekranie szerokość zmieści się w widoku bez zmiany
              zapisu.
            </p>
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
