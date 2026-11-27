import { useEffect, useId, useState, type FormEvent } from "react";
import { api, ApiError } from "../../../shared/api/client";
import { useAuth } from "../../auth/AuthProvider";
import { useFleet } from "../model/FleetProvider";
import { updateTime, type Vehicle } from "../model/types";

const fields = [
  { key: "name", label: "Nazwa", max: 200 },
  { key: "license_plate", label: "Numer rejestracyjny", max: 100 },
  { key: "make", label: "Marka", max: 100 },
  { key: "model", label: "Model", max: 100 },
  { key: "year", label: "Rok produkcji", max: undefined },
  { key: "vin", label: "VIN", max: 100 },
  { key: "vehicle_type", label: "Typ pojazdu", max: 100 },
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
  const [archiving, setArchiving] = useState(false);
  const [archiveReason, setArchiveReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [error, setError] = useState("");
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

  const change = (key: Field, value: string) => {
    if (!draft) return;
    const changes = { ...draft.changes };
    if (fieldValue(draft.base, key) === value) delete changes[key];
    else changes[key] = value;
    setDraft({ ...draft, changes });
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!draft || !Object.keys(draft.changes).length || !editable || saving || conflict) return;
    const body = Object.fromEntries(Object.entries(draft.changes).map(([key, value]) =>
      [key, key === "year" && value ? Number(value) : value.trim() || null],
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
        : failure instanceof ApiError
          ? failure.message
          : "Zapis kartoteki nie powiódł się. Spróbuj ponownie.");
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
      setNotice(
        saved.source_active === false
          ? "Pojazd został przywrócony z archiwum. Nie jest obecnie aktywny w raporcie WEBFLEET — pozostaje dostępny w filtrze „Bieżące i archiwalne”."
          : "Pojazd został przywrócony do bieżącej floty.",
      );
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
      {!visible.archived && visible.source_active === false && (
        <section className="fleet-notice" aria-label="Stan pojazdu w źródle WEBFLEET">
          <div>
            <strong>Poza raportem WEBFLEET</strong>
            <p>
              Pojazd nie występuje obecnie w aktywnym raporcie źródła. Kartoteka oraz historia przejazdów pozostają dostępne w filtrze „Bieżące i archiwalne”.
            </p>
          </div>
        </section>
      )}
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
      {draft && !visible.archived ? (
        <form aria-label="Kartoteka pojazdu" aria-busy={saving} onSubmit={submit}>
          <div className="vehicle-card-fields">
            {fields.map(({ key, label, max }) => (
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
                  required={key === "name"}
                  readOnly={saving}
                />
              </label>
            ))}
          </div>
          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="vehicle-card-actions">
            {conflict && <button type="button" className="button button-secondary" disabled={saving}
              onClick={readLatest}>Wczytaj bieżącą wersję</button>}
            <button className="button button-primary" disabled={!Object.keys(draft.changes).length || saving || conflict}>
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
          </dl>
          {error && !archiving && <p className="form-error" role="alert">{error}</p>}
          {editable && visible.card_version && !visible.archived && !archiving && (
            <div className="vehicle-card-actions">
              <button type="button" className="button button-secondary"
                onClick={() => { setNotice(""); setError(""); setDraft({ base: visible, changes: {} }); }}>
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
