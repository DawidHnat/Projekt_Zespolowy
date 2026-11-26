import { useEffect, useId, useState, type FormEvent } from "react";
import { api, ApiError } from "../../../shared/api/client";
import { DatePicker } from "../../../shared/components/DatePicker";
import { displayCalendarDate } from "../../../shared/components/calendar-date";
import { useAuth } from "../../auth/AuthProvider";
import { useFleet } from "../model/FleetProvider";
import { measurementLabel, updateTime, type Vehicle } from "../model/types";

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

const LICENSE_CATEGORIES = [
  "AM", "A1", "A2", "A", "B1", "B", "B+E", "C1", "C1+E", "C", "C+E", "D1", "D1+E", "D", "D+E", "T",
] as const;

const dateFields = [
  { key: "leasing_end_on", label: "Koniec leasingu" },
  { key: "inspection_due_on", label: "Następne badanie techniczne" },
  { key: "insurance_due_on", label: "Koniec ważności OC" },
] as const;

type EditableKey =
  | typeof textFields[number]["key"]
  | typeof dateFields[number]["key"]
  | "manual_odometer_km"
  | "manual_odometer_date"
  | "gross_weight_kg"
  | "passenger_seats"
  | "tows_heavy_trailer"
  | "required_category_override";
type Changes = Partial<Record<EditableKey, string>>;
type Draft = { base: Vehicle; changes: Changes };

function fieldValue(vehicle: Vehicle, key: EditableKey) {
  if (key === "tows_heavy_trailer") return vehicle.tows_heavy_trailer ? "true" : "false";
  return String(vehicle[key] ?? "");
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
      if (key === "year" || key === "gross_weight_kg" || key === "passenger_seats")
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
            {textFields.map(({ key, label, max }) => (
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
            {dateFields.map(({ key, label }) => (
              <div key={key}>
                <span>{label}</span>
                <DatePicker
                  id={`${id}-${key}`}
                  label={label}
                  value={draft.changes[key] ?? fieldValue(draft.base, key)}
                  onChange={val => change(key, val)}
                  disabled={saving}
                  allowClear
                />
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
            <label htmlFor={`${id}-gross-weight-kg`}>
              DMC w kg
              <input
                id={`${id}-gross-weight-kg`}
                type="number"
                step="1"
                min={1}
                max={120000}
                value={draft.changes.gross_weight_kg ?? fieldValue(draft.base, "gross_weight_kg")}
                onChange={event => change("gross_weight_kg", event.target.value)}
                aria-invalid={Boolean(fieldErrors.gross_weight_kg)}
                readOnly={saving}
              />
              {fieldErrors.gross_weight_kg && (
                <span className="form-error">{fieldErrors.gross_weight_kg}</span>
              )}
            </label>
            <label htmlFor={`${id}-passenger-seats`}>
              Miejsca pasażerskie
              <input
                id={`${id}-passenger-seats`}
                type="number"
                step="1"
                min={0}
                max={120}
                value={draft.changes.passenger_seats ?? fieldValue(draft.base, "passenger_seats")}
                onChange={event => change("passenger_seats", event.target.value)}
                aria-invalid={Boolean(fieldErrors.passenger_seats)}
                readOnly={saving}
              />
              {fieldErrors.passenger_seats && (
                <span className="form-error">{fieldErrors.passenger_seats}</span>
              )}
            </label>
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
            {textFields.map(({ key, label }) => (
              <div key={key}><dt>{label}</dt><dd>{fieldValue(visible, key) || "Brak danych"}</dd></div>
            ))}
            {dateFields.map(({ key, label }) => (
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
            <div>
              <dt>DMC</dt>
              <dd>
                {visible.gross_weight_kg != null
                  ? `${visible.gross_weight_kg.toLocaleString("pl-PL")} kg`
                  : "Brak danych"}
              </dd>
            </div>
            <div>
              <dt>Miejsca pasażerskie</dt>
              <dd>{visible.passenger_seats != null ? String(visible.passenger_seats) : "Brak danych"}</dd>
            </div>
            <div>
              <dt>Przyczepa ciężka (+E)</dt>
              <dd>{visible.tows_heavy_trailer ? "Tak" : "Nie"}</dd>
            </div>
            <div>
              <dt>Wymagane prawo jazdy</dt>
              <dd>{formatLicenseRequirement(visible)}</dd>
            </div>
          </dl>
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
