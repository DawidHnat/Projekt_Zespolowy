import { useEffect, useId, useRef, useState } from "react";
import { api, ApiError } from "../../../shared/api/client";
import type { DriverProfile } from "../../../shared/api/generated/contracts";
import { useDrivers } from "../model/DriverContext";

function draftOf(profile: DriverProfile | null) {
  return {
    first_name: profile?.first_name ?? "",
    last_name: profile?.last_name ?? "",
    identifier: profile?.identifier ?? "",
    phone: profile?.phone ?? "",
    email: profile?.email ?? "",
    active: profile?.active ?? true,
    categories: profile?.categories ?? [],
  };
}
export function DriverForm({
  profile,
  onDirty,
  onSaved,
  onCancel,
}: {
  profile: DriverProfile | null;
  onDirty: (value: boolean) => void;
  onSaved: (profile: DriverProfile) => void;
  onCancel: () => void;
}) {
  const { catalog, catalogError, retryCatalog } = useDrivers();
  const id = useId();
  const [base] = useState(() => draftOf(profile));
  const [draft, setDraft] = useState(base);
  const [version, setVersion] = useState(profile?.version ?? 1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [conflict, setConflict] = useState(false);
  const [latest, setLatest] = useState<DriverProfile | null>(null);
  const request = useRef<AbortController | null>(null);
  const firstInput = useRef<HTMLInputElement>(null);
  const form = useRef<HTMLFormElement>(null);
  const dirty = JSON.stringify(base) !== JSON.stringify(draft);
  useEffect(() => {
    firstInput.current?.focus();
    return () => request.current?.abort();
  }, []);
  useEffect(() => {
    onDirty(dirty || busy);
    return () => onDirty(false);
  }, [dirty, busy, onDirty]);
  useEffect(() => {
    if (!dirty) return;
    const guard = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, [dirty]);
  const save = async () => {
    if (busy || conflict || !catalog) return;
    const invalid: Record<string, string> = {};
    for (const field of ["first_name", "last_name", "identifier"] as const) {
      if (!draft[field].trim()) invalid[field] = "Uzupełnij to pole.";
      else if (/[\u0000-\u001f]/.test(draft[field]))
        invalid[field] = "Usuń znaki sterujące.";
    }
    if (
      draft.phone.trim() &&
      !/^\+?[0-9]{7,20}$/.test(draft.phone.trim().replace(/[(). \-]/g, ""))
    )
      invalid.phone = "Wpisz od 7 do 20 cyfr, opcjonalnie + na początku.";
    const email = form.current?.elements.namedItem(
      "email",
    ) as HTMLInputElement | null;
    if (email?.validity.typeMismatch)
      invalid.email = "Wpisz poprawny adres e-mail.";
    setFieldErrors(invalid);
    if (Object.keys(invalid).length) {
      (
        form.current?.elements.namedItem(
          Object.keys(invalid)[0],
        ) as HTMLInputElement | null
      )?.focus();
      return;
    }
    const controller = new AbortController();
    request.current = controller;
    setBusy(true);
    setError(null);
    try {
      const saved = await api<DriverProfile>(
        profile ? `/drivers/${profile.id}` : "/drivers",
        {
          method: profile ? "PATCH" : "POST",
          signal: controller.signal,
          body: JSON.stringify({
            ...draft,
            phone: draft.phone.trim() || null,
            email: draft.email.trim() || null,
            ...(profile ? { version } : {}),
          }),
        },
      );
      if (!controller.signal.aborted) {
        onDirty(false);
        onSaved(saved);
      }
    } catch (err) {
      if (controller.signal.aborted) return;
      if (err instanceof ApiError && err.status === 409) {
        setError(
          profile
            ? "Dane zmieniły się lub identyfikator jest już używany. Twój formularz pozostał na ekranie."
            : "Identyfikator jest już używany. Podaj inny identyfikator; formularz został zachowany.",
        );
        setConflict(!!profile);
        setLatest(null);
        if (!profile)
          setFieldErrors({ identifier: "Ten identyfikator jest już używany." });
      } else
        setError(
          err instanceof ApiError && err.status === 403
            ? "Brak uprawnień do zapisu danych kierowcy."
            : "Nie zapisano danych. Sprawdź pola i ponów zapis. Formularz został zachowany.",
        );
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  };
  const readLatest = async () => {
    if (!profile) return;
    setBusy(true);
    const controller = new AbortController();
    request.current = controller;
    try {
      const value = await api<DriverProfile>(`/drivers/${profile.id}`, {
        signal: controller.signal,
      });
      if (!controller.signal.aborted) setLatest(value);
    } catch {
      if (!controller.signal.aborted)
        setError(
          "Nie można odczytać bieżącej wersji. Formularz pozostał na ekranie.",
        );
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  };
  return (
    <form
      ref={form}
      noValidate
      className="driver-form"
      aria-label={profile ? "Edycja kierowcy" : "Nowy kierowca"}
      aria-busy={busy}
      onSubmit={(event) => {
        event.preventDefault();
        void save();
      }}
    >
      <h3>{profile ? "Edytuj dane kierowcy" : "Dodaj kierowcę ręcznie"}</h3>
      {profile?.needs_completion && (
        <p>
          Uzupełnij osobne imię, nazwisko i identyfikator. Dotychczasowa nazwa:{" "}
          {profile.display_name}.
        </p>
      )}
      {(
        [
          ["first_name", "Imię"],
          ["last_name", "Nazwisko"],
          ["identifier", "Identyfikator kierowcy"],
          ["phone", "Telefon"],
          ["email", "E-mail"],
        ] as const
      ).map(([field, label]) => (
        <label key={field} htmlFor={`${id}-${field}`}>
          <span id={`${id}-${field}-label`}>
            {label}
            {(field === "phone" || field === "email") && (
              <span> · opcjonalnie</span>
            )}
          </span>
          <input
            ref={field === "first_name" ? firstInput : undefined}
            id={`${id}-${field}`}
            name={field}
            value={draft[field]}
            type={
              field === "email" ? "email" : field === "phone" ? "tel" : "text"
            }
            aria-labelledby={`${id}-${field}-label`}
            aria-invalid={!!fieldErrors[field]}
            aria-describedby={
              fieldErrors[field] ? `${id}-${field}-error` : undefined
            }
            required={field !== "phone" && field !== "email"}
            maxLength={field === "phone" ? 50 : field === "email" ? 254 : 100}
            disabled={busy}
            onChange={(event) => {
              setDraft((value) => ({ ...value, [field]: event.target.value }));
              setFieldErrors((value) => ({ ...value, [field]: "" }));
            }}
          />
          {fieldErrors[field] && (
            <span id={`${id}-${field}-error`} className="form-error">
              {fieldErrors[field]}
            </span>
          )}
        </label>
      ))}
      <label className="driver-checkbox">
        <input
          type="checkbox"
          checked={draft.active}
          disabled={busy}
          onChange={(event) =>
            setDraft((value) => ({ ...value, active: event.target.checked }))
          }
        />
        Kierowca aktywny
      </label>
      <small>
        Dezaktywacja kończy bieżące przypisania. Historia pozostaje dostępna.
      </small>
      <fieldset disabled={busy}>
        <legend>Wpisane kategorie prawa jazdy</legend>
        <p>
          Dane wpisujesz ręcznie. Lista nie potwierdza uprawnień do konkretnego
          pojazdu.
        </p>
        {!catalog &&
          (catalogError ? (
            <div role="alert">
              <p>Nie można pobrać kategorii.</p>
              <button
                type="button"
                className="button button-secondary"
                onClick={retryCatalog}
              >
                Ponów kategorie
              </button>
            </div>
          ) : (
            <p role="status">Pobieranie kategorii…</p>
          ))}
        <div className="driver-categories">
          {catalog?.items.map((category) => (
            <label key={category.id} className="driver-checkbox">
              <input
                type="checkbox"
                checked={draft.categories.includes(category.id)}
                onChange={(event) =>
                  setDraft((value) => ({
                    ...value,
                    categories: event.target.checked
                      ? [...value.categories, category.id]
                      : value.categories.filter((item) => item !== category.id),
                  }))
                }
              />
              {category.label}
            </label>
          ))}
        </div>
      </fieldset>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      {conflict && (
        <section
          className="driver-conflict"
          aria-label="Konflikt danych kierowcy"
        >
          <button
            type="button"
            className="button button-secondary"
            disabled={busy}
            onClick={() => void readLatest()}
          >
            Sprawdź bieżące dane kierowcy
          </button>
          {latest && (
            <>
              <h4>Bieżące dane na serwerze</h4>
              <p>
                {latest.display_name} ·{" "}
                {latest.identifier || "Brak identyfikatora"} ·{" "}
                {latest.active ? "Aktywny" : "Nieaktywny"}
              </p>
              <p>
                {latest.phone || "Brak telefonu"} ·{" "}
                {latest.email || "Brak e-maila"}
              </p>
              <p>
                Kategorie: {latest.categories.join(", ") || "Brak wpisanych"}
              </p>
              <button
                type="button"
                className="button button-secondary"
                disabled={busy}
                onClick={() => {
                  setVersion(latest.version);
                  setConflict(false);
                  setLatest(null);
                  setError(null);
                }}
              >
                Kontynuuj z moim formularzem
              </button>
            </>
          )}
        </section>
      )}
      <div className="driver-actions">
        <button
          className="button button-primary"
          disabled={busy || conflict || !catalog}
        >
          {busy ? "Zapisywanie…" : "Zapisz kierowcę"}
        </button>
        <button
          type="button"
          className="button button-secondary"
          disabled={busy}
          onClick={onCancel}
        >
          Anuluj dane kierowcy
        </button>
      </div>
    </form>
  );
}
