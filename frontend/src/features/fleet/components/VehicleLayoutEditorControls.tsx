import { useState } from "react";
import { LayoutEditorControls } from "../../dashboard/components/LayoutEditorControls";
import { useFleet } from "../model/FleetProvider";
import { useVehiclePreferences } from "../model/VehiclePreferences";
import { CARD_PRESETS } from "../model/vehicle-layout";
import { VehicleSizeDialog } from "./VehicleSizeDialog";

export function VehicleLayoutEditorControls() {
  const f = useFleet();
  const p = useVehiclePreferences();
  const [sizing, setSizing] = useState(false);
  const visibleIds = f.list?.items.map((vehicle) => vehicle.id) ?? [];
  const enabled = p.editScope === "all" || p.selectedIds.length > 0;
  return (
    <div className="vehicle-layout-editor">
      <div className="vehicle-layout-actions">
        {p.editing && (
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
        )}
        <LayoutEditorControls
          title="Pojazdy"
          editing={p.editing}
          onEdit={p.start}
          onSave={p.save}
          onCancel={p.cancel}
          onReset={p.reset}
        />
      </div>
      {p.editing && (
        <>
          <div className="vehicle-layout-options">
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
            <select
              className="button button-secondary vehicle-size-picker"
              aria-label="Rozmiar kafelków"
              aria-describedby="vehicle-layout-status"
              disabled={!enabled}
              value=""
              onChange={(event) => {
                if (event.target.value === "custom") setSizing(true);
                else {
                  const preset = CARD_PRESETS.find(
                    (size) => size.name === event.target.value,
                  );
                  if (preset)
                    p.changeGroup({ width: preset.width, height: preset.height });
                }
              }}
            >
              <option value="" disabled>
                Rozmiar kafelków
              </option>
              {CARD_PRESETS.map(({ name }) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
              <option value="custom">Własny rozmiar…</option>
            </select>
          </div>
          <p
            className="vehicle-layout-status"
            id="vehicle-layout-status"
            role="status"
          >
            {p.editScope === "all"
              ? "Cała flota, również poza tą stroną i filtrami."
              : p.selectedIds.length
                ? `Wybrano: ${p.selectedIds.length}. Wybór pozostaje przy zmianie strony i filtrów.`
                : "Kliknij kafelki, które chcesz wspólnie dopasować."}
          </p>
        </>
      )}
      <VehicleSizeDialog
        open={p.editing && sizing}
        onClose={() => setSizing(false)}
      />
    </div>
  );
}
