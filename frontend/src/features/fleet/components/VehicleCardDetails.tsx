import { useEffect, useId, useState, type FormEvent } from "react";
import { api, ApiError } from "../../../shared/api/client";
import { useAuth } from "../../auth/AuthProvider";
import { useFleet } from "../model/FleetProvider";
import { measurementLabel, updateTime, type Vehicle } from "../model/types";
import { isVehicleCardNumberField, validateVehicleCardFields, vehicleCardNumberBounds } from "../model/vehicle-card-validation";
import { DatePicker } from "../../../shared/components/DatePicker";

const fields = [
  { key: "name", label: "Nazwa", max: 200 },
  { key: "license_plate", label: "Numer rejestracyjny", max: 100 },
  { key: "make", label: "Marka", max: 100 },
  { key: "model", label: "Model", max: 100 },
  { key: "year", label: "Rok produkcji", max: undefined },
  { key: "vin", label: "VIN", max: 100 },
  { key: "vehicle_type", label: "Typ pojazdu", max: 100 },
  { key: "ownership_category", label: "Kategoria", max: undefined },
  { key: "purchase_date", label: "Data wykupu leasingu", max: undefined },
  { key: "first_registration", label: "Pierwsza rejestracja", max: undefined },
  { key: "first_registration_poland", label: "Pierwsza rejestracja w Polsce", max: undefined },
  { key: "fuel_type", label: "Paliwo", max: 50 },
  { key: "engine_capacity_cc", label: "Pojemność silnika (cm³)", max: undefined },
  { key: "power_kw", label: "Moc (kW)", max: undefined },
  { key: "dmc_kg", label: "DMC (kg)", max: undefined },
  { key: "curb_weight_kg", label: "Masa własna (kg)", max: undefined },
  { key: "payload_kg", label: "Ładowność (kg)", max: undefined },
  { key: "seats", label: "Liczba miejsc", max: undefined },
  { key: "axles", label: "Liczba osi", max: undefined },
] as const;

type Field = typeof fields[number]["key"];
type Changes = Partial<Record<Field, string>>;
type Draft = { base: Vehicle; changes: Changes };

function fieldValue(vehicle: Vehicle, key: Field) {
  return String(vehicle[key] ?? "");
}

export function VehicleCardDetails({ vehicle, onUnsaved }: {
  vehicle: Vehicle;
  onUnsaved: (value: boolean) => void;
}) {
  const { user } = useAuth();
  const fleet = useFleet();
  const id = useId();
  const [draft, setDraft] = useState<Draft | null>(null);
  const [saving, setSaving] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [lastSaved, setLastSaved] = useState<Vehicle | null>(null);
  const visible = lastSaved && (lastSaved.card_version ?? 0) > (vehicle.card_version ?? 0)
    ? lastSaved : vehicle;
  const dirty = !!draft && Object.keys(draft.changes).length > 0;
  const editable = user?.role === "admin" || user?.role === "editor";
  const path = `/fleet/vehicles/${encodeURIComponent(vehicle.id)}`;

  useEffect(() => {
    onUnsaved(dirty || saving);
    return () => onUnsaved(false);
  }, [dirty, saving, onUnsaved]);

  const change = (key: Field, value: string) => {
    if (!draft) return;
    const changes = { ...draft.changes };
    if (fieldValue(draft.base, key) === value) delete changes[key];
    else changes[key] = value;
    setDraft({ ...draft, changes });
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!draft || !dirty || !editable || saving || conflict) return;
    const validationErrors = validateVehicleCardFields({ ...draft.base, ...draft.changes });
    const invalidField = fields.find(({ key }) => Object.hasOwn(validationErrors, key));
    if (invalidField) {
      const message = validationErrors.first_registration_poland === "registration_order"
        && invalidField.key === "first_registration_poland"
        ? "Pierwsza rejestracja w Polsce nie może poprzedzać pierwszej rejestracji."
        : `Sprawdź wartość pola „${invalidField.label}”.`;
      setError(message);
      return;
    }
    const body = Object.fromEntries(Object.entries(draft.changes).map(([key, value]) =>
      [
        key,
        isVehicleCardNumberField(key)
          ? (value.trim() ? Number(value) : null)
          : value.trim() || null,
      ],
    ));
    if ("name" in body && !body.name) {
      setError("Podaj nazwę pojazdu.");
      return;
    }
    setSaving(true);
    setNotice("");
    setError("");
    try {
      const saved = await api<Vehicle>(path, {
        method: "PATCH",
        body: JSON.stringify({ ...body, card_version: draft.base.card_version }),
      });
      setDraft(null);
      setLastSaved(saved);
      setNotice("Zapisano kartotekę pojazdu.");
      fleet.refresh();
    } catch (failure) {
      const versionConflict = failure instanceof ApiError && failure.code === "VERSION_CONFLICT";
      setConflict(versionConflict);
      setError(versionConflict
        ? "Kartoteka zmieniła się podczas edycji. Twój szkic pozostał w formularzu."
        : "Zapis kartoteki nie powiódł się. Spróbuj ponownie.");
    } finally {
      setSaving(false);
    }
  };

  const readLatest = async () => {
    setSaving(true);
    try {
      const base = await api<Vehicle>(path);
      setDraft(current => current ? { ...current, base } : null);
      setConflict(false);
      setError("");
      setNotice("Wczytano aktualne dane i zachowano pola ze szkicu. Sprawdź je przed zapisem.");
    } catch {
      setError("Nie udało się wczytać aktualnych danych. Twój szkic jest nadal dostępny.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="vehicle-card-details">
      <h3>Szczegóły pojazdu</h3>
      {draft ? (
        <form aria-label="Kartoteka pojazdu" aria-busy={saving} onSubmit={submit}>
          <div className="vehicle-card-fields">
            {fields.map(({ key, label, max }) => (
              <label key={key} htmlFor={`${id}-${key}`}>
                {label}
                {key === "ownership_category" ? (
                  <select
                    id={`${id}-${key}`}
                    value={draft.changes[key] ?? fieldValue(draft.base, key)}
                    onChange={event => change(key, event.target.value)}
                    disabled={saving}
                  >
                    <option value="">Brak danych</option>
                    <option value="Firmowe">Firmowe</option>
                    <option value="Prywatne">Prywatne</option>
                    <option value="Leasing">Leasing</option>
                  </select>
                ) : key === "purchase_date" || key === "first_registration" || key === "first_registration_poland" ? (
                  <DatePicker
                    value={draft.changes[key] ?? fieldValue(draft.base, key)}
                    label={label}
                    maxDate={key === "purchase_date" ? undefined : new Date().toISOString().slice(0, 10)}
                    disabled={saving}
                    allowClear
                    onChange={value => change(key, value)}
                  />
                ) : (
                  <input
                    id={`${id}-${key}`}
                    value={draft.changes[key] ?? fieldValue(draft.base, key)}
                    onChange={event => change(key, event.target.value)}
                    type={isVehicleCardNumberField(key) ? "number" : "text"}
                    min={isVehicleCardNumberField(key) ? vehicleCardNumberBounds[key][0] : undefined}
                    max={isVehicleCardNumberField(key) ? vehicleCardNumberBounds[key][1] : undefined}
                    maxLength={max}
                    required={key === "name"}
                    readOnly={saving}
                  />
                )}
              </label>
            ))}
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="vehicle-card-actions">
            {conflict && <button type="button" className="button button-secondary" disabled={saving}
              onClick={readLatest}>Wczytaj bieżącą wersję</button>}
            <button className="button button-primary" disabled={!dirty || saving || conflict}>
              Zapisz kartotekę
            </button>
            <button type="button" className="button button-secondary" disabled={saving}
              onClick={() => { setDraft(null); setConflict(false); setError(""); setNotice(""); }}>
              Anuluj
            </button>
          </div>
        </form>
      ) : (
        <>
          <dl className="vehicle-card-fields">
            {fields.map(({ key, label }) => (
              <div key={key}><dt>{label}</dt><dd>{fieldValue(visible, key) || "Brak danych"}</dd></div>
            ))}
            <div><dt>Przebieg ze źródła</dt><dd>{measurementLabel(visible.odometer_km, "km", 1)}</dd></div>
            <div><dt>Ostatnia aktualizacja przebiegu</dt><dd>{updateTime(visible.received_at)}</dd></div>
          </dl>
          {editable && visible.card_version && (
            <button type="button" className="button button-secondary"
              onClick={() => { setNotice(""); setDraft({ base: visible, changes: {} }); }}>
              Edytuj kartotekę
            </button>
          )}
        </>
      )}
      {notice && <p role="status">{notice}</p>}
    </div>
  );
}
