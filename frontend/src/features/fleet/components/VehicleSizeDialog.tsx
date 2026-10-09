import { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { CARD_MIN, CARD_MAX, CARD_PRESETS } from "../model/vehicle-layout";
import { useVehiclePreferences } from "../model/VehiclePreferences";

export function VehicleSizeDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const p = useVehiclePreferences();
  useEffect(() => {
    if (open && !ref.current?.open) ref.current?.showModal();
    if (!open) ref.current?.close();
  }, [open]);
  const size = p.groupSize.first;
  return (
    <dialog
      ref={ref}
      className="widget-settings-dialog"
      aria-labelledby="vehicle-size-title"
      onClose={onClose}
    >
      {open && (
        <>
          <header className="panel-header">
            <div>
              <span className="eyebrow">ROZMIAR KAFELKÓW</span>
              <h2 id="vehicle-size-title">
                {p.editScope === "all"
                  ? "Wszystkie pojazdy"
                  : `Zaznaczone: ${p.selectedIds.length}`}
              </h2>
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
              {p.editScope === "all"
                ? "Zmieniasz całą flotę, także pojazdy na innych stronach i poza filtrami."
                : "Zmieniasz wyłącznie zaznaczone pojazdy, także na innych stronach."}{" "}
              Zatwierdź przyciskiem „Zapisz układ”.
            </p>
            {(["width", "height"] as const).map((axis) => (
              <label key={axis} className="size-control">
                {axis === "width" ? "Szerokość" : "Wysokość"}
                <output>
                  {(
                    axis === "width"
                      ? p.groupSize.mixedWidth
                      : p.groupSize.mixedHeight
                  )
                    ? "Różne rozmiary"
                    : `${size[axis]} px`}
                </output>
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
                    p.changeGroup({ [axis]: Number(e.target.value) })
                  }
                />
              </label>
            ))}
            <div className="size-presets">
              {CARD_PRESETS.map(({ name, ...next }) => (
                <button
                  key={name}
                  className="button button-secondary"
                  onClick={() => p.changeGroup(next)}
                >
                  {name}
                </button>
              ))}
            </div>
            <p>
              Suwak wyrównuje jeden wymiar, preset oba. Minimum zachowuje
              zdjęcie, nazwę, status i podstawowe dane. Na mniejszym ekranie
              szerokość zmieści się w widoku bez zmiany zapisu.
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
