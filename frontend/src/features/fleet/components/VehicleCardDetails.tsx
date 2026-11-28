import { useEffect, useId, useState, type FormEvent } from "react";
import { api, ApiError } from "../../../shared/api/client";
import { DatePicker } from "../../../shared/components/DatePicker";
import { displayCalendarDate } from "../../../shared/components/calendar-date";
import { useAuth } from "../../auth/AuthProvider";
import { useFleet } from "../model/FleetProvider";
import { measurementLabel, updateTime, type Vehicle } from "../model/types";

import { dateFields as validatedDates, vehicleCardFieldMessages, vehicleCardNumberBounds } from "../model/vehicle-card-validation";

const textFields = [
  { key: "name", label: "Nazwa", max: 200 },
  { key: "license_plate", label: "Numer rejestracyjny", max: 100 },
  { key: "make", label: "Marka", max: 100 },
  { key: "model", label: "Model", max: 100 },
  { key: "year", label: "Rok produkcji", max: undefined },
  { key: "vin", label: "VIN", max: 100 },
  { key: "vehicle_type", label: "Typ pojazdu", max: 100 },
  { key: "fuel_type", label: "Paliwo", max: 50 },
  { key: "leasing_company", label: "Firma leasingowa", max: 200 },
  { key: "leasing_contract_no", label: "Nr umowy leasingu", max: 100 },
] as const;

const OWNERSHIP_CATEGORIES = ["Firmowe", "Prywatne", "Leasing"] as const;
// Leasing data stays stored when the category changes; it is only shown for leasing.
const LEASING_KEYS = new Set<string>([
  "leasing_company", "leasing_contract_no", "leasing_end_on", "leasing_buyout_on",
]);

const LICENSE_CATEGORIES = [
  "AM", "A1", "A2", "A", "B1", "B", "B+E", "C1", "C1+E", "C", "C+E", "D1", "D1+E", "D", "D+E", "T",
] as const;

const dateFields = [
  { key: "first_registration_on", label: "Pierwsza rejestracja" },
  { key: "first_registration_pl_on", label: "Pierwsza rejestracja w Polsce" },
  { key: "leasing_end_on", label: "Koniec leasingu" },
  { key: "leasing_buyout_on", label: "Data wykupu" },
  { key: "inspection_due_on", label: "Następne badanie techniczne" },
  { key: "insurance_due_on", label: "Koniec ważności OC" },
] as const;

// DMC and passenger seats are the shared SCRUM-70 fields used by the licence check.
const numberFields = [
  { key: "engine_capacity_cc", label: "Pojemność silnika (cm³)", view: "Pojemność silnika", unit: "cm³", min: 1, max: 100000 },
  { key: "power_kw", label: "Moc (kW)", view: "Moc", unit: "kW", min: 1, max: 10000 },
  { key: "gross_weight_kg", label: "DMC w kg", view: "DMC", unit: "kg", min: 1, max: 120000 },
  { key: "curb_weight_kg", label: "Masa własna (kg)", view: "Masa własna", unit: "kg", min: 1, max: 120000 },
  { key: "payload_kg", label: "Ładowność (kg)", view: "Ładowność", unit: "kg", min: 1, max: 120000 },
  { key: "passenger_seats", label: "Miejsca pasażerskie (bez kierowcy)", view: "Miejsca pasażerskie (bez kierowcy)", unit: "", min: 0, max: 120 },
  { key: "axles", label: "Liczba osi", view: "Liczba osi", unit: "", min: 1, max: 20 },
] as const;
const NUMERIC_KEYS = new Set<string>(["year", ...numberFields.map(field => field.key)]);

type EditableKey =
  | typeof textFields[number]["key"]
  | typeof dateFields[number]["key"]
  | typeof numberFields[number]["key"]
  | "ownership_category"
  | "manual_odometer_km"
  | "manual_odometer_date"
  | "tows_heavy_trailer"
  | "required_category_override";
type Changes = Partial<Record<EditableKey, string>>;
type Draft = { base: Vehicle; changes: Changes };

function fieldValue(vehicle: Vehicle, key: EditableKey) {
  if (key === "tows_heavy_trailer") return vehicle.tows_heavy_trailer ? "true" : "false";
  return String(vehicle[key] ?? "");
}

/** Leasing fields show for the leasing category, or for older cards that already hold them. */
function showsLeasing(category: string, stored: Vehicle) {
  if (category) return category === "Leasing";
  return [...LEASING_KEYS].some(key => fieldValue(stored, key as EditableKey) !== "");
}

function hidesStoredLeasing(category: string, stored: Vehicle) {
  return !showsLeasing(category, stored) &&
    [...LEASING_KEYS].some(key => fieldValue(stored, key as EditableKey) !== "");
}

function formatNumber(value: number | null | undefined, unit: string) {
  if (value == null) return "Brak danych";
  const text = value.toLocaleString("pl-PL");
  return unit ? `${text} ${unit}` : text;
}

function formatLicenseRequirement(vehicle: Vehicle): string {
  const req = vehicle.license_requirement;
  if (!req) return "Brak danych";
  if (req.status === "determined" && req.required_category) {
    const srcLabel =
      req.source === "override"
        ? "wyjątek kartoteki"
        : req.source === "passenger_seats"
          ? "liczba miejsc"
          : req.source === "vehicle_type"
            ? "typ pojazdu"
            : "DMC";
    return `Kat. ${req.required_category} (${srcLabel})`;
  }
  if (req.reason === "missing_vehicle_dmc") return "Niezweryfikowane (brak DMC w kg)";
  if (req.reason === "missing_passenger_seats") return "Niezweryfikowane (brak liczby miejsc)";
  if (req.reason === "missing_vehicle_requirements") return "Niezweryfikowane (wymagany wyjątek kategorii)";
  return "Niezweryfikowane";
}

export function VehicleCardDetails({ vehicle, onUnsaved }: {
  vehicle: Vehicle;
  onUnsaved: (value: boolean) => void;
}) {
  const { user } = useAuth();
  const fleet = useFleet();
  const id = useId();
  const [draft, setDraft] = useState<Draft | null>(null);
  const [archiving, setArchiving] = useState(false);
  const [archiveReason, setArchiveReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState("");
  const [lastSaved, setLastSaved] = useState<Vehicle | null>(null);
  const visible = lastSaved && (lastSaved.card_version ?? 0) > (vehicle.card_version ?? 0)
    ? lastSaved : vehicle;
  const dirty = (!!draft && Object.keys(draft.changes).length > 0) || (archiving && archiveReason.trim().length > 0);
  const editable = user?.role === "admin" || user?.role === "editor";
  const path = `/fleet/vehicles/${encodeURIComponent(vehicle.id)}`;
  const draftCategory = draft
    ? draft.changes.ownership_category ?? fieldValue(draft.base, "ownership_category")
    : "";
  const draftLeasing = draft ? showsLeasing(draftCategory, draft.base) : false;
  const visibleLeasing = showsLeasing(visible.ownership_category ?? "", visible);

  useEffect(() => {
    onUnsaved(dirty || saving);
    return () => onUnsaved(false);
  }, [dirty, saving, onUnsaved]);

  const change = (key: EditableKey, value: string) => {
    if (!draft) return;
    const changes = { ...draft.changes };
    if (fieldValue(draft.base, key) === value) delete changes[key];
    else changes[key] = value;
    setDraft({ ...draft, changes });
    setFieldErrors(current => ({ ...current, [key]: "" }));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!draft || !Object.keys(draft.changes).length || !editable || saving || conflict) return;
    const effectiveValues = Object.fromEntries(
      [...Object.keys(vehicleCardNumberBounds), ...validatedDates].map(key => [
        key, draft.changes[key as EditableKey] ?? fieldValue(draft.base, key as EditableKey),
      ]),
    );
    const validationErrors = vehicleCardFieldMessages(effectiveValues);
    if (Object.keys(validationErrors).length) {
      setFieldErrors(validationErrors);
      return;
    }
    const nextOdoKm = draft.changes.manual_odometer_km ?? fieldValue(draft.base, "manual_odometer_km");
    const nextOdoDate = draft.changes.manual_odometer_date ?? fieldValue(draft.base, "manual_odometer_date");
    if ((nextOdoKm.trim() !== "") !== (nextOdoDate.trim() !== "")) {
      setFieldErrors({
        [nextOdoKm.trim() === "" ? "manual_odometer_km" : "manual_odometer_date"]:
          "Przebieg ręczny wymaga podania wartości oraz daty odczytu.",
      });
      return;
    }
    const body = Object.fromEntries(Object.entries(draft.changes).map(([key, value]) => {
      if (NUMERIC_KEYS.has(key))
        return [key, value.trim() ? Number(value) : null];
      if (key === "tows_heavy_trailer")
        return [key, value === "true"];
      if (key === "manual_odometer_km")
        return [key, value.trim() ? Number(value.replace(",", ".")) : null];
      return [key, value.trim() || null];
    }));
    if ("name" in body && !body.name) {
      setFieldErrors({ name: "Podaj nazwę pojazdu." });
      return;
    }
    if (visible.origin === "manual" && "license_plate" in body && !body.license_plate) {
      setFieldErrors({ license_plate: "Numer rejestracyjny pojazdu ręcznego jest wymagany." });
      return;
    }
    setSaving(true);
    setNotice("");
    setError("");
    setFieldErrors({});
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
      if (failure instanceof ApiError && Object.keys(failure.fields).length)
        setFieldErrors(failure.fields);
      setConflict(versionConflict);
      setError(versionConflict
        ? "Kartoteka zmieniła się podczas edycji. Twój szkic pozostał w formularzu."
        : failure instanceof ApiError
          ? failure.message
          : "Zapis kartoteki nie powiódł się. Spróbuj ponownie.");
    } finally {
      setSaving(false);
    }
  };

  const submitLinkSource = async (sourceVehicleId: string) => {
    if (!editable || saving || !visible.card_version) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const saved = await api<Vehicle>(`${path}/link-source`, {
        method: "POST",
        body: JSON.stringify({
          card_version: visible.card_version,
          source_vehicle_id: sourceVehicleId,
        }),
      });
      setLastSaved(saved);
      setDraft(null);
      setNotice("Pojazd ręczny został jawnie połączony ze źródłem WEBFLEET z zachowaniem kartoteki i historii.");
      fleet.refresh();
    } catch (failure) {
      setError(
        failure instanceof ApiError
          ? failure.message
          : "Nie udało się połączyć pojazdu ze źródłem WEBFLEET.",
      );
    } finally {
      setSaving(false);
    }
  };

  const submitArchive = async (event: FormEvent) => {
    event.preventDefault();
    if (!editable || saving || !visible.card_version) return;
    if (/[\u0000-\u001f]/.test(archiveReason)) {
      setError("Powód archiwizacji zawiera niedozwolone znaki sterujące.");
      return;
    }
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const saved = await api<Vehicle>(`${path}/archive`, {
        method: "POST",
        body: JSON.stringify({
          card_version: visible.card_version,
          reason: archiveReason.trim() || null,
        }),
      });
      setArchiving(false);
      setArchiveReason("");
      setDraft(null);
      setConflict(false);
      setLastSaved(saved);
      setNotice("Pojazd został przeniesiony do archiwum. Historia przejazdów i przypisań pozostaje dostępna.");
      fleet.refresh();
    } catch (failure) {
      setError(
        failure instanceof ApiError && failure.code === "VERSION_CONFLICT"
          ? "Stan pojazdu zmienił się w międzyczasie. Odśwież dane przed ponowieniem."
          : failure instanceof ApiError
            ? failure.message
            : "Archiwizacja pojazdu nie powiodła się. Spróbuj ponownie.",
      );
    } finally {
      setSaving(false);
    }
  };

  const submitRestore = async () => {
    if (!editable || saving || !visible.card_version) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const saved = await api<Vehicle>(`${path}/restore`, {
        method: "POST",
        body: JSON.stringify({ card_version: visible.card_version }),
      });
      setLastSaved(saved);
      setConflict(false);
      setNotice("Pojazd został przywrócony do bieżącej floty.");
      fleet.refresh();
    } catch (failure) {
      setError(
        failure instanceof ApiError && failure.code === "VERSION_CONFLICT"
          ? "Stan pojazdu zmienił się w międzyczasie. Odśwież dane przed ponowieniem."
          : failure instanceof ApiError
            ? failure.message
            : "Przywrócenie pojazdu nie powiodło się. Spróbuj ponownie.",
      );
    } finally {
      setSaving(false);
    }
  };

  const readLatest = async () => {
    setSaving(true);
    try {
      const base = await api<Vehicle>(path);
      setLastSaved(base);
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
      {visible.archived && visible.archive && (
        <section className="fleet-notice" aria-label="Stan archiwizacji pojazdu">
          <div>
            <strong>Pojazd w archiwum</strong>
            <p>
              Zarchiwizowano: {updateTime(visible.archive.archived_at)}
              {visible.archive.archived_by
                ? ` · Autor: ${visible.archive.archived_by.display_name}`
                : ""}
            </p>
            {visible.archive.reason && <p>Powód: {visible.archive.reason}</p>}
            <small>
              Historyczne przejazdy i przypisania są zachowane. Nowe przypisania wymagają przywrócenia pojazdu.
            </small>
          </div>
          {editable && visible.card_version && (
            <button
              type="button"
              className="button button-primary"
              disabled={saving}
              onClick={() => void submitRestore()}
            >
              Przywróć pojazd
            </button>
          )}
        </section>
      )}
      {visible.origin === "manual" && !visible.archived && (visible.link_candidates?.length ?? 0) > 0 && (
        <section className="fleet-notice" aria-label="Wykryty pojazd źródłowy WEBFLEET">
          <div>
            <strong>Wykryto pasujący pojazd w WEBFLEET</strong>
            <p>
              Synchronizacja nie scala pojazdów automatycznie. Możesz jawnie połączyć ten wpis ze źródłem, zachowując identyfikator, kartotekę i historię.
            </p>
            {visible.link_candidates!.map(candidate => (
              <div key={candidate.id} className="vehicle-card-actions">
                <span>
                  {candidate.name}
                  {candidate.license_plate ? ` · ${candidate.license_plate}` : ""}
                  {candidate.vin ? ` · VIN ${candidate.vin}` : ""}
                </span>
                {editable && (
                  <button
                    type="button"
                    className="button button-primary"
                    disabled={saving}
                    onClick={() => void submitLinkSource(candidate.id)}
                  >
                    Połącz z pojazdem WEBFLEET
                  </button>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
      {draft && !visible.archived ? (
        <form noValidate aria-label="Kartoteka pojazdu" aria-busy={saving} onSubmit={submit}>
          <div className="vehicle-card-fields">
            <label htmlFor={`${id}-ownership-category`}>
              Kategoria pojazdu
              <select
                id={`${id}-ownership-category`}
                value={draftCategory}
                disabled={saving}
                aria-invalid={Boolean(fieldErrors.ownership_category)}
                onChange={event => change("ownership_category", event.target.value)}
              >
                <option value="">Brak danych</option>
                {OWNERSHIP_CATEGORIES.map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
              {fieldErrors.ownership_category && (
                <span className="form-error">{fieldErrors.ownership_category}</span>
              )}
            </label>
            {textFields.filter(({ key }) => draftLeasing || !LEASING_KEYS.has(key)).map(({ key, label, max }) => (
              <label key={key} htmlFor={`${id}-${key}`}>
                {label}
                <input
                  id={`${id}-${key}`}
                  value={draft.changes[key] ?? fieldValue(draft.base, key)}
                  onChange={event => change(key, event.target.value)}
                  type={key === "year" ? "number" : "text"}
                  min={key === "year" ? 1900 : undefined}
                  max={key === "year" ? 2100 : undefined}
                  maxLength={max}
                  required={key === "name" || (visible.origin === "manual" && key === "license_plate")}
                  aria-invalid={Boolean(fieldErrors[key])}
                  readOnly={saving}
                />
                {fieldErrors[key] && <span className="form-error">{fieldErrors[key]}</span>}
              </label>
            ))}
            {dateFields.filter(({ key }) => draftLeasing || !LEASING_KEYS.has(key)).map(({ key, label }) => (
              <div key={key}>
                {/* DatePicker names its button itself; the caption is not a second <label>. */}
                <span aria-hidden="true">{label}</span>
                <DatePicker
                  id={`${id}-${key}`}
                  label={label}
                  value={draft.changes[key] ?? fieldValue(draft.base, key)}
                  onChange={val => change(key, val)}
                  disabled={saving}
                  allowClear
                />
                {fieldErrors[key] && <span className="form-error">{fieldErrors[key]}</span>}
              </div>
            ))}
            <label htmlFor={`${id}-manual-odometer-km`}>
              Przebieg ręczny (km)
              <input
                id={`${id}-manual-odometer-km`}
                type="number"
                step="0.1"
                min={0}
                max={9999999.9}
                value={draft.changes.manual_odometer_km ?? fieldValue(draft.base, "manual_odometer_km")}
                onChange={event => change("manual_odometer_km", event.target.value)}
                aria-invalid={Boolean(fieldErrors.manual_odometer_km)}
                readOnly={saving}
              />
              {fieldErrors.manual_odometer_km && (
                <span className="form-error">{fieldErrors.manual_odometer_km}</span>
              )}
            </label>
            <div>
              <span>Data odczytu przebiegu</span>
              <DatePicker
                id={`${id}-manual-odometer-date`}
                label="Data odczytu przebiegu"
                value={draft.changes.manual_odometer_date ?? fieldValue(draft.base, "manual_odometer_date")}
                onChange={val => change("manual_odometer_date", val)}
                disabled={saving}
                allowClear
              />
              {fieldErrors.manual_odometer_date && (
                <span className="form-error">{fieldErrors.manual_odometer_date}</span>
              )}
            </div>
            {numberFields.map(({ key, label, min, max }) => (
              <label key={key} htmlFor={`${id}-${key}`}>
                {label}
                <input
                  id={`${id}-${key}`}
                  type="number"
                  inputMode="numeric"
                  step="1"
                  min={min}
                  max={max}
                  value={draft.changes[key] ?? fieldValue(draft.base, key)}
                  onChange={event => change(key, event.target.value)}
                  aria-invalid={Boolean(fieldErrors[key])}
                  readOnly={saving}
                />
                {fieldErrors[key] && <span className="form-error">{fieldErrors[key]}</span>}
              </label>
            ))}
            <label htmlFor={`${id}-required-category-override`}>
              Wymagana kategoria (wyjątek)
              <select
                id={`${id}-required-category-override`}
                value={
                  draft.changes.required_category_override ??
                  fieldValue(draft.base, "required_category_override")
                }
                disabled={saving}
                onChange={event => change("required_category_override", event.target.value)}
              >
                <option value="">Wg DMC / liczby miejsc</option>
                {LICENSE_CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </label>
            <label htmlFor={`${id}-tows-heavy-trailer`} className="driver-checkbox">
              <input
                id={`${id}-tows-heavy-trailer`}
                type="checkbox"
                checked={
                  (draft.changes.tows_heavy_trailer ??
                    fieldValue(draft.base, "tows_heavy_trailer")) === "true"
                }
                disabled={saving}
                onChange={event =>
                  change("tows_heavy_trailer", event.target.checked ? "true" : "false")
                }
              />
              Przyczepa ciężka (+E)
            </label>
          </div>
          {hidesStoredLeasing(draftCategory, draft.base) && (
            <small>Dane leasingu pozostają zapisane i są ukryte, dopóki kategoria pojazdu nie jest „Leasing”.</small>
          )}
          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="vehicle-card-actions">
            {conflict && <button type="button" className="button button-secondary" disabled={saving}
              onClick={readLatest}>Wczytaj bieżącą wersję</button>}
            <button className="button button-primary" disabled={!Object.keys(draft.changes).length || saving || conflict}>
              Zapisz kartotekę
            </button>
            <button type="button" className="button button-secondary" disabled={saving}
              onClick={() => { setDraft(null); setConflict(false); setError(""); setFieldErrors({}); setNotice(""); }}>
              Anuluj
            </button>
          </div>
        </form>
      ) : (
        <>
          <dl className="vehicle-card-fields">
            <div>
              <dt>Pochodzenie</dt>
              <dd>{visible.origin === "manual" ? "Ręczny (bez lokalizatora WEBFLEET)" : "WEBFLEET"}</dd>
            </div>
            <div>
              <dt>Kategoria pojazdu</dt>
              <dd>{visible.ownership_category ?? "Brak danych"}</dd>
            </div>
            {textFields.filter(({ key }) => visibleLeasing || !LEASING_KEYS.has(key)).map(({ key, label }) => (
              <div key={key}><dt>{label}</dt><dd>{fieldValue(visible, key) || "Brak danych"}</dd></div>
            ))}
            {dateFields.filter(({ key }) => visibleLeasing || !LEASING_KEYS.has(key)).map(({ key, label }) => (
              <div key={key}>
                <dt>{label}</dt>
                <dd>{displayCalendarDate(fieldValue(visible, key)) || "Brak danych"}</dd>
              </div>
            ))}
            <div>
              <dt>Przebieg ręczny</dt>
              <dd>
                {visible.manual_odometer_km != null
                  ? `${measurementLabel(visible.manual_odometer_km, "km")}${
                      visible.manual_odometer_date
                        ? ` (${displayCalendarDate(visible.manual_odometer_date)})`
                        : ""
                    }`
                  : "Brak danych"}
              </dd>
            </div>
            {numberFields.map(({ key, view, unit }) => (
              <div key={key}><dt>{view}</dt><dd>{formatNumber(visible[key], unit)}</dd></div>
            ))}
            <div>
              <dt>Przyczepa ciężka (+E)</dt>
              <dd>{visible.tows_heavy_trailer ? "Tak" : "Nie"}</dd>
            </div>
            <div>
              <dt>Wymagane prawo jazdy</dt>
              <dd>{formatLicenseRequirement(visible)}</dd>
            </div>
          </dl>
          {hidesStoredLeasing(visible.ownership_category ?? "", visible) && (
            <small>Dane leasingu pozostają zapisane i są ukryte, dopóki kategoria pojazdu nie jest „Leasing”.</small>
          )}
          {error && !archiving && <p className="form-error" role="alert">{error}</p>}
          {editable && visible.card_version && !visible.archived && !archiving && (
            <div className="vehicle-card-actions">
              <button type="button" className="button button-secondary"
                onClick={() => { setNotice(""); setError(""); setFieldErrors({}); setDraft({ base: visible, changes: {} }); }}>
                Edytuj kartotekę
              </button>
              <button type="button" className="button button-secondary"
                onClick={() => { setNotice(""); setError(""); setArchiving(true); }}>
                Archiwizuj pojazd
              </button>
            </div>
          )}
          {editable && visible.card_version && !visible.archived && archiving && (
            <form aria-label="Archiwizacja pojazdu" aria-busy={saving} onSubmit={submitArchive}>
              <label htmlFor={`${id}-archive-reason`}>
                Powód archiwizacji (opcjonalnie)
                <input
                  id={`${id}-archive-reason`}
                  type="text"
                  maxLength={500}
                  placeholder="Np. sprzedaż lub wycofanie z eksploatacji"
                  value={archiveReason}
                  onChange={event => setArchiveReason(event.target.value)}
                  readOnly={saving}
                />
              </label>
              <small>
                Bieżące przypisania kierowców zostaną zakończone z zachowaniem historii. Kolejna synchronizacja WEBFLEET nie przywróci pojazdu.
              </small>
              {error && <p className="form-error" role="alert">{error}</p>}
              <div className="vehicle-card-actions">
                <button className="button button-primary" disabled={saving}>
                  Potwierdź archiwizację
                </button>
                <button
                  type="button"
                  className="button button-secondary"
                  disabled={saving}
                  onClick={() => { setArchiving(false); setArchiveReason(""); setError(""); }}
                >
                  Anuluj archiwizację
                </button>
              </div>
            </form>
          )}
        </>
      )}
      {notice && <p role="status">{notice}</p>}
    </div>
  );
}
