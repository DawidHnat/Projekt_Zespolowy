import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { X } from "lucide-react";
import { api, ApiError } from "../../../shared/api/client";
import type { DriverList } from "../../../shared/api/generated/contracts";
import { DatePicker } from "../../../shared/components/DatePicker";
import { trapDialogFocus } from "../../../shared/components/dialog-focus";
import type { Vehicle } from "../model/types";

import { vehicleCardFieldMessages } from "../model/vehicle-card-validation";

const LICENSE_CATEGORIES = [
  "AM", "A1", "A2", "A", "B1", "B", "B+E", "C1", "C1+E", "C", "C+E", "D1", "D1+E", "D", "D+E", "T",
] as const;

type ManualDraft = {
  name: string;
  license_plate: string;
  make: string;
  model: string;
  year: string;
  vin: string;
  vehicle_type: string;
  fuel_type: string;
  leasing_company: string;
  leasing_contract_no: string;
  leasing_end_on: string;
  inspection_due_on: string;
  insurance_due_on: string;
  manual_odometer_km: string;
  manual_odometer_date: string;
  gross_weight_kg: string;
  passenger_seats: string;
  tows_heavy_trailer: boolean;
  required_category_override: string;
  driver_id: string;
};

const emptyDraft = (): ManualDraft => ({
  name: "",
  license_plate: "",
  make: "",
  model: "",
  year: "",
  vin: "",
  vehicle_type: "",
  fuel_type: "",
  leasing_company: "",
  leasing_contract_no: "",
  leasing_end_on: "",
  inspection_due_on: "",
  insurance_due_on: "",
  manual_odometer_km: "",
  manual_odometer_date: "",
  gross_weight_kg: "",
  passenger_seats: "",
  tows_heavy_trailer: false,
  required_category_override: "",
  driver_id: "",
});

export function VehicleCreateDialog({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (vehicle: Vehicle) => void;
}) {
  const id = useId();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [draft, setDraft] = useState<ManualDraft>(emptyDraft);
  const [drivers, setDrivers] = useState<Array<{ id: string; display_name: string }>>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [sourceConflict, setSourceConflict] = useState(false);

  const dirty = Object.entries(draft).some(([key, v]) =>
    key === "tows_heavy_trailer" ? Boolean(v) : String(v).trim().length > 0,
  );

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      setDraft(emptyDraft());
      setError("");
      setFieldErrors({});
      setSourceConflict(false);
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    api<DriverList>("/drivers?active=true&page_size=100", { signal: controller.signal })
      .then((res) => {
        if (!controller.signal.aborted)
          setDrivers(res.items.map((item) => ({ id: item.id, display_name: item.display_name })));
      })
      .catch(() => {
        if (!controller.signal.aborted) setDrivers([]);
      });
    return () => controller.abort();
  }, [open]);

  const requestClose = () => {
    if (saving) return;
    if (!dirty || window.confirm("Masz niezapisane dane nowego pojazdu. Odrzucić zmiany?")) {
      onClose();
    }
  };

  const setField = <K extends keyof ManualDraft>(key: K, value: ManualDraft[K]) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => ({ ...prev, [key]: "" }));
    if (key === "license_plate" || key === "vin") setSourceConflict(false);
  };

  const submit = async (event: FormEvent, allowSourceDuplicate = false) => {
    event.preventDefault();
    if (saving) return;
    const invalid = vehicleCardFieldMessages(draft);
    if (!draft.name.trim()) invalid.name = "Podaj nazwę pojazdu.";
    if (!draft.license_plate.trim()) invalid.license_plate = "Podaj numer rejestracyjny.";
    if ((draft.manual_odometer_km.trim() !== "") !== (draft.manual_odometer_date !== "")) {
      if (!draft.manual_odometer_km.trim())
        invalid.manual_odometer_km = "Podaj przebieg dla wybranej daty odczytu.";
      else invalid.manual_odometer_date = "Wybierz datę ręcznego odczytu przebiegu.";
    } else if (draft.manual_odometer_km.trim()) {
      const km = Number(draft.manual_odometer_km.replace(",", "."));
      if (!Number.isFinite(km) || km < 0 || km > 9999999.9)
        invalid.manual_odometer_km = "Podaj poprawny przebieg (0–9 999 999,9 km).";
    }
    setFieldErrors(invalid);
    if (Object.keys(invalid).length > 0) return;

    setSaving(true);
    setError("");
    try {
      const created = await api<Vehicle>("/fleet/vehicles", {
        method: "POST",
        body: JSON.stringify({
          name: draft.name.trim(),
          license_plate: draft.license_plate.trim(),
          make: draft.make.trim() || null,
          model: draft.model.trim() || null,
          year: draft.year.trim() ? Number(draft.year) : null,
          vin: draft.vin.trim() || null,
          vehicle_type: draft.vehicle_type.trim() || null,
          fuel_type: draft.fuel_type.trim() || null,
          leasing_company: draft.leasing_company.trim() || null,
          leasing_contract_no: draft.leasing_contract_no.trim() || null,
          leasing_end_on: draft.leasing_end_on || null,
          inspection_due_on: draft.inspection_due_on || null,
          insurance_due_on: draft.insurance_due_on || null,
          manual_odometer_km: draft.manual_odometer_km.trim()
            ? Number(draft.manual_odometer_km.replace(",", "."))
            : null,
          manual_odometer_date: draft.manual_odometer_date || null,
          gross_weight_kg: draft.gross_weight_kg.trim()
            ? Number(draft.gross_weight_kg)
            : null,
          passenger_seats: draft.passenger_seats.trim()
            ? Number(draft.passenger_seats)
            : null,
          tows_heavy_trailer: draft.tows_heavy_trailer,
          required_category_override: draft.required_category_override || null,
          driver_id: draft.driver_id || null,
          allow_source_duplicate: allowSourceDuplicate,
        }),
      });
      onCreated(created);
    } catch (failure) {
      if (failure instanceof ApiError) {
        if (Object.keys(failure.fields).length) setFieldErrors(failure.fields);
        setSourceConflict(failure.code === "SOURCE_VEHICLE_EXISTS");
        setError(failure.message);
      } else {
        setError("Nie udało się utworzyć pojazdu ręcznego. Spróbuj ponownie.");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className="widget-settings-dialog vehicle-details-dialog"
      aria-labelledby={`${id}-title`}
      onKeyDown={trapDialogFocus}
      onCancel={(event) => {
        event.preventDefault();
        requestClose();
      }}
    >
      {open && (
        <>
          <header className="panel-header">
            <div>
              <span className="eyebrow">NOWY POJAZD RĘCZNY</span>
              <h2 id={`${id}-title`}>Dodaj pojazd bez lokalizatora</h2>
            </div>
            <button
              type="button"
              className="icon-button"
              aria-label="Zamknij formularz nowego pojazdu"
              onClick={requestClose}
            >
              <X size={20} aria-hidden="true" />
            </button>
          </header>
          <form
            noValidate
            className="vehicle-card-details"
            aria-label="Formularz nowego pojazdu ręcznego"
            aria-busy={saving}
            onSubmit={(event) => void submit(event, false)}
          >
            <p>
              Pojazd ręczny otrzymuje stabilny identyfikator aplikacji bez fikcyjnej telemetrii GPS.
            </p>
            <div className="vehicle-card-fields">
              {(
                [
                  ["name", "Nazwa pojazdu", 200, true],
                  ["license_plate", "Numer rejestracyjny", 100, true],
                  ["make", "Marka", 100, false],
                  ["model", "Model", 100, false],
                  ["year", "Rok produkcji", undefined, false],
                  ["vin", "VIN", 100, false],
                  ["vehicle_type", "Typ pojazdu", 100, false],
                  ["fuel_type", "Paliwo", 50, false],
                  ["leasing_company", "Firma leasingowa", 200, false],
                  ["leasing_contract_no", "Nr umowy leasingu", 100, false],
                ] as const
              ).map(([key, label, max, req]) => (
                <label key={key} htmlFor={`${id}-${key}`}>
                  {label}
                  <input
                    id={`${id}-${key}`}
                    name={key}
                    type={key === "year" ? "number" : "text"}
                    min={key === "year" ? 1900 : undefined}
                    max={key === "year" ? 2100 : undefined}
                    maxLength={max}
                    required={req}
                    value={draft[key]}
                    aria-invalid={Boolean(fieldErrors[key])}
                    aria-describedby={fieldErrors[key] ? `${id}-${key}-err` : undefined}
                    readOnly={saving}
                    onChange={(event) => setField(key, event.target.value)}
                  />
                  {fieldErrors[key] && (
                    <span id={`${id}-${key}-err`} className="form-error">
                      {fieldErrors[key]}
                    </span>
                  )}
                </label>
              ))}
              <div>
                <span>Koniec leasingu (opcjonalnie)</span>
                <DatePicker
                  id={`${id}-leasing-end`}
                  label="Koniec leasingu"
                  value={draft.leasing_end_on}
                  onChange={(val) => setField("leasing_end_on", val)}
                  disabled={saving}
                  allowClear
                />
              </div>
              <div>
                <span>Następne badanie techniczne (opcjonalnie)</span>
                <DatePicker
                  id={`${id}-inspection`}
                  label="Następne badanie techniczne"
                  value={draft.inspection_due_on}
                  onChange={(val) => setField("inspection_due_on", val)}
                  disabled={saving}
                  allowClear
                />
              </div>
              <div>
                <span>Koniec ważności OC (opcjonalnie)</span>
                <DatePicker
                  id={`${id}-insurance`}
                  label="Koniec ważności OC"
                  value={draft.insurance_due_on}
                  onChange={(val) => setField("insurance_due_on", val)}
                  disabled={saving}
                  allowClear
                />
              </div>
              <label htmlFor={`${id}-odometer-km`}>
                Przebieg ręczny w km (opcjonalnie)
                <input
                  id={`${id}-odometer-km`}
                  type="number"
                  step="0.1"
                  min={0}
                  max={9999999.9}
                  value={draft.manual_odometer_km}
                  aria-invalid={Boolean(fieldErrors.manual_odometer_km)}
                  aria-describedby={fieldErrors.manual_odometer_km ? `${id}-odo-err` : undefined}
                  readOnly={saving}
                  onChange={(event) => setField("manual_odometer_km", event.target.value)}
                />
                {fieldErrors.manual_odometer_km && (
                  <span id={`${id}-odo-err`} className="form-error">
                    {fieldErrors.manual_odometer_km}
                  </span>
                )}
              </label>
              <div>
                <span>Data odczytu przebiegu</span>
                <DatePicker
                  id={`${id}-odometer-date`}
                  label="Data odczytu przebiegu"
                  value={draft.manual_odometer_date}
                  onChange={(val) => setField("manual_odometer_date", val)}
                  disabled={saving}
                  allowClear
                />
                {fieldErrors.manual_odometer_date && (
                  <span className="form-error">{fieldErrors.manual_odometer_date}</span>
                )}
              </div>
              <label htmlFor={`${id}-dmc`}>
                DMC w kg (opcjonalnie)
                <input
                  id={`${id}-dmc`}
                  type="number"
                  aria-invalid={Boolean(fieldErrors.gross_weight_kg)}
                  aria-describedby={fieldErrors.gross_weight_kg ? `${id}-dmc-error` : undefined}
                  step="1"
                  min={1}
                  max={120000}
                  value={draft.gross_weight_kg}
                  readOnly={saving}
                  onChange={(event) => setField("gross_weight_kg", event.target.value)}
                />
              </label>
              {fieldErrors.gross_weight_kg && (
                <span id={`${id}-dmc-error`} className="form-error">{fieldErrors.gross_weight_kg}</span>
              )}
              <label htmlFor={`${id}-seats`}>
                Miejsca pasażerskie (opcjonalnie)
                <input
                  id={`${id}-seats`}
                  type="number"
                  aria-invalid={Boolean(fieldErrors.passenger_seats)}
                  aria-describedby={fieldErrors.passenger_seats ? `${id}-seats-error` : undefined}
                  step="1"
                  min={0}
                  max={120}
                  value={draft.passenger_seats}
                  readOnly={saving}
                  onChange={(event) => setField("passenger_seats", event.target.value)}
                />
              </label>
              {fieldErrors.passenger_seats && (
                <span id={`${id}-seats-error`} className="form-error">{fieldErrors.passenger_seats}</span>
              )}
              <label htmlFor={`${id}-cat-override`}>
                Wymagana kategoria — wyjątek (opcjonalnie)
                <select
                  id={`${id}-cat-override`}
                  value={draft.required_category_override}
                  disabled={saving}
                  onChange={(event) => setField("required_category_override", event.target.value)}
                >
                  <option value="">Wg DMC / liczby miejsc</option>
                  {LICENSE_CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </label>
              <label htmlFor={`${id}-trailer`} className="driver-checkbox">
                <input
                  id={`${id}-trailer`}
                  type="checkbox"
                  checked={draft.tows_heavy_trailer}
                  disabled={saving}
                  onChange={(event) => setField("tows_heavy_trailer", event.target.checked)}
                />
                Przyczepa ciężka (+E)
              </label>
              <label htmlFor={`${id}-driver`}>
                Przypisz kierowcę (opcjonalnie)
                <select
                  id={`${id}-driver`}
                  value={draft.driver_id}
                  disabled={saving}
                  onChange={(event) => setField("driver_id", event.target.value)}
                >
                  <option value="">Bez przypisania</option>
                  {drivers.map((drv) => (
                    <option key={drv.id} value={drv.id}>
                      {drv.display_name}
                    </option>
                  ))}
                </select>
                {fieldErrors.driver_id && (
                  <span className="form-error">{fieldErrors.driver_id}</span>
                )}
              </label>
            </div>
            {error && (
              <p className="form-error" role="alert">
                {error}
              </p>
            )}
            {sourceConflict && (
              <div className="fleet-notice" role="region" aria-label="Rozstrzygnięcie konfliktu ze źródłem WEBFLEET">
                <span>
                  Jeśli to tymczasowo odrębny wpis przed jawnym połączeniem ze źródłem WEBFLEET, możesz potwierdzić jego utworzenie.
                </span>
                <button
                  type="button"
                  className="button button-secondary"
                  disabled={saving}
                  onClick={(event) => void submit(event as unknown as FormEvent, true)}
                >
                  Utwórz mimo istnienia w WEBFLEET
                </button>
              </div>
            )}
            <div className="vehicle-card-actions">
              <button className="button button-primary" disabled={saving}>
                {saving ? "Zapisywanie…" : "Utwórz pojazd"}
              </button>
              <button
                type="button"
                className="button button-secondary"
                disabled={saving}
                onClick={requestClose}
              >
                Anuluj
              </button>
            </div>
          </form>
        </>
      )}
    </dialog>
  );
}
