import { useEffect, useId, useState, type FormEvent } from "react";
import { api } from "../../../shared/api/client";
import { annotationDraft, annotationError, annotationValidation, type Annotation, type Trip } from "../model/annotations";

const modifiedTime = (value: string) => new Intl.DateTimeFormat("pl-PL", {
  timeZone: "Europe/Warsaw", dateStyle: "short", timeStyle: "short",
}).format(new Date(value));

export function TripAnnotationEditor({ trip, canEdit, onSaved, onDirty }: {
  trip: Trip;
  canEdit: boolean;
  onSaved: (value: Annotation) => void;
  onDirty: (value: boolean) => void;
}) {
  const id = useId();
  const [base, setBase] = useState(trip.annotation);
  const [draft, setDraft] = useState(() => annotationDraft(trip.annotation));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [conflict, setConflict] = useState(false);
  const [latest, setLatest] = useState<Annotation | null>(null);
  const dirty = draft.purpose !== (base.purpose ?? "") || draft.description !== (base.description ?? "");
  useEffect(() => {
    onDirty(dirty || busy);
    return () => onDirty(false);
  }, [dirty, busy, onDirty]);
  useEffect(() => {
    if (!dirty) return;
    const guard = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [dirty]);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const validation = annotationValidation(draft);
    if (validation) { setError(validation); return; }
    if (busy || !canEdit || conflict) return;
    setBusy(true); setError(null); setNotice(null);
    try {
      const saved = await api<Annotation>(`/trips/${encodeURIComponent(trip.id)}/annotation`, {
        method: "PATCH", body: JSON.stringify({ ...draft, version: base.version }),
      });
      setBase(saved); setDraft(annotationDraft(saved)); onSaved(saved);
      setNotice("Cel i opis zostały zapisane.");
    } catch (err) {
      setError(annotationError(err));
      if (err && typeof err === "object" && "code" in err && err.code === "VERSION_CONFLICT") {
        setConflict(true); setLatest(null);
      }
    } finally { setBusy(false); }
  };
  const readLatest = async () => {
    setBusy(true);
    try {
      const current = await api<Trip>(`/trips/${encodeURIComponent(trip.id)}`);
      setLatest(current.annotation);
    } catch (err) { setError(annotationError(err)); }
    finally { setBusy(false); }
  };
  return (
    <form className="trip-annotation-form" onSubmit={submit} aria-label="Cel i opis przejazdu" aria-busy={busy}>
      <h3>Cel i opis przejazdu</h3>
      {!canEdit && <p>Masz dostęp tylko do odczytu.</p>}
      <label htmlFor={`${id}-purpose`}>Cel przejazdu <span>do 200 znaków</span></label>
      <input id={`${id}-purpose`} maxLength={200} value={draft.purpose} readOnly={!canEdit || busy}
        onChange={e => { setDraft({ ...draft, purpose: e.target.value }); setNotice(null); }} />
      <label htmlFor={`${id}-description`}>Opis przejazdu <span>do 2000 znaków</span></label>
      <textarea id={`${id}-description`} rows={4} maxLength={2000} value={draft.description} readOnly={!canEdit || busy}
        onChange={e => { setDraft({ ...draft, description: e.target.value }); setNotice(null); }} />
      <small>Puste pole usuwa wcześniejszy wpis. Dane przejazdu pozostają bez zmian.</small>
      {base.updated_at && <small>Ostatnia zmiana: {base.updated_by?.display_name ?? "Użytkownik"} · {modifiedTime(base.updated_at)}</small>}
      {error && <p className="form-error" role="alert">{error}</p>}
      {notice && <p className="auth-notice" role="status">{notice}</p>}
      {conflict && <section className="trip-conflict" aria-label="Konflikt edycji">
        <button className="button button-secondary" type="button" onClick={readLatest} disabled={busy}>Sprawdź bieżącą wersję</button>
        {latest && <>
          <h4>Bieżąca wersja w bazie</h4>
          <dl><dt>Cel</dt><dd>{latest.purpose || "Brak celu"}</dd><dt>Opis</dt><dd>{latest.description || "Brak opisu"}</dd></dl>
          <small>{latest.updated_by?.display_name} · {latest.updated_at && modifiedTime(latest.updated_at)}</small>
          <p>Porównaj ją ze swoim tekstem powyżej. Możesz go poprawić przed zapisem.</p>
          <button className="button button-secondary" type="button" disabled={busy} onClick={() => {
            setBase(latest); setLatest(null); setConflict(false); setError(null);
            setNotice("Zachowano Twój tekst. Przejrzyj go i zapisz, aby zastąpić bieżącą wersję.");
          }}>Kontynuuj z moim tekstem</button>
        </>}
      </section>}
      {canEdit && <div className="trip-annotation-actions">
        <button className="button button-primary" disabled={!dirty || busy || conflict}>{busy ? "Proszę czekać…" : "Zapisz cel i opis"}</button>
        <button className="button button-secondary" type="button" disabled={busy || !dirty} onClick={() => {
          const value = latest ?? base;
          setBase(value); setDraft(annotationDraft(value)); onSaved(value);
          setConflict(false); setLatest(null); setError(null); setNotice("Odrzucono niezapisane zmiany.");
        }}>Anuluj zmiany</button>
      </div>}
    </form>
  );
}
