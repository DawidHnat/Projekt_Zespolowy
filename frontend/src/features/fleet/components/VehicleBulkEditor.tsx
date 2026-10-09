import { Settings2 } from "lucide-react";
import { useVehiclePreferences } from "../model/VehiclePreferences";
import { CARD_PRESETS } from "../model/vehicle-layout";
export function VehicleBulkEditor({
  visibleIds,
  onSize,
}: {
  visibleIds: string[];
  onSize: () => void;
}) {
  const p = useVehiclePreferences();
  const enabled = p.editScope === "all" || p.selectedIds.length > 0;
  return (
    <div className="vehicle-bulk-editor">
      <div className="vehicle-bulk-row">
        <div
          className="vehicle-edit-scope"
          role="group"
          aria-label="Zakres edycji kafelków"
        >
          <button
            aria-pressed={p.editScope === "all"}
            onClick={() => p.setEditScope("all")}
          >
            Wszystkie pojazdy
          </button>
          <button
            aria-pressed={p.editScope === "selected"}
            onClick={() => p.setEditScope("selected")}
          >
            Zaznaczone <span>{p.selectedIds.length}</span>
          </button>
        </div>
        <div className="vehicle-selection-actions">
          <button
            onClick={() => p.selectVisible(visibleIds)}
            disabled={!visibleIds.length}
          >
            Zaznacz widoczne
          </button>
          <button
            onClick={p.clearSelection}
            disabled={p.editScope === "selected" && !p.selectedIds.length}
          >
            Wyczyść wybór
          </button>
        </div>
      </div>
      <div className="vehicle-bulk-row">
        <p role="status">
          {p.editScope === "all"
            ? "Edytujesz całą flotę, również poza tą stroną i aktywnymi filtrami."
            : p.selectedIds.length
              ? `Wybrano: ${p.selectedIds.length}. Wybór pozostaje przy zmianie strony i filtrów.`
              : "Kliknij kafelki, które chcesz wspólnie dopasować."}
        </p>
        <div className="vehicle-bulk-sizes">
          <span>Równy rozmiar</span>
          {CARD_PRESETS.map(({ name, ...size }) => (
            <button
              className="button button-secondary"
              key={name}
              disabled={!enabled}
              onClick={() => p.changeGroup(size)}
            >
              {name}
            </button>
          ))}
          <button
            className="button button-secondary"
            disabled={!enabled}
            onClick={onSize}
          >
            <Settings2 size={15} />
            Własny rozmiar
          </button>
        </div>
      </div>
    </div>
  );
}
