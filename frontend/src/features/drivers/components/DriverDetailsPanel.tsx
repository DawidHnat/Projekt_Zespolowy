import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { X } from "lucide-react";
import { api } from "../../../shared/api/client";
import type { DriverProfile } from "../../../shared/api/generated/contracts";
import { trapDialogFocus } from "../../../shared/components/dialog-focus";
import { useAuth } from "../../auth/AuthProvider";
import { useDrivers } from "../model/DriverContext";
import { DriverForm } from "./DriverForm";
import { DriverAssignments } from "./DriverAssignments";

export type DriverPanel = {
  id: string | null;
  mode: "view" | "edit" | "assignments" | "create";
};
export function DriverDetailsPanel({
  panel,
  onClose,
}: {
  panel: DriverPanel;
  onClose: () => void;
}) {
  const titleId = useId();
  const dialog = useRef<HTMLDialogElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const section = useRef<HTMLElement>(null);
  const { user } = useAuth();
  const { refresh } = useDrivers();
  const canEdit = user?.role === "admin" || user?.role === "editor";
  const [mode, setMode] = useState(panel.mode);
  const [profile, setProfile] = useState<DriverProfile | null>(null);
  const [loading, setLoading] = useState(!!panel.id);
  const [error, setError] = useState(false);
  const [revision, setRevision] = useState(0);
  const [formDirty, setFormDirty] = useState(false);
  const [assignmentDirty, setAssignmentDirty] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  useLayoutEffect(() => {
    const node = dialog.current;
    node?.showModal();
    return () => node?.close();
  }, []);
  useEffect(() => {
    if (!panel.id) return;
    const controller = new AbortController();
    setLoading(true);
    setError(false);
    api<DriverProfile>(`/drivers/${panel.id}`, { signal: controller.signal })
      .then((value) => {
        if (!controller.signal.aborted) setProfile(value);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError(true);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [panel.id, revision]);
  useEffect(() => {
    if (mode === "assignments" && profile)
      section.current?.scrollIntoView({ block: "start" });
  }, [mode, profile?.id]);
  useEffect(() => {
    if (mode === "view" && profile) heading.current?.focus();
  }, [mode, profile?.id]);
  const close = () => {
    if (
      (!formDirty && !assignmentDirty) ||
      window.confirm(
        "Masz niezapisane dane kierowcy lub wybór pojazdu. Odrzucić zmiany?",
      )
    )
      onClose();
  };
  const updated = useCallback(
    (value: DriverProfile) => {
      setProfile(value);
      refresh();
    },
    [refresh],
  );
  const saved = (value: DriverProfile) => {
    updated(value);
    setMode("view");
    setFormDirty(false);
    setNotice("Dane kierowcy zostały zapisane.");
  };
  return (
    <dialog
      ref={dialog}
      className="widget-settings-dialog driver-details-dialog"
      aria-labelledby={titleId}
      onKeyDown={trapDialogFocus}
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
    >
      <header className="panel-header">
        <div>
          <span className="eyebrow">KIEROWCA</span>
          <h2 ref={heading} tabIndex={-1} id={titleId}>
            {profile?.display_name ||
              (mode === "create" ? "Nowy kierowca" : "Dane kierowcy")}
          </h2>
        </div>
        <button
          className="icon-button"
          aria-label="Zamknij panel kierowcy"
          onClick={close}
        >
          <X size={20} aria-hidden="true" />
        </button>
      </header>
      <div className="driver-panel-content">
        {notice && <p role="status">{notice}</p>}
        {loading && <p role="status">Pobieranie danych kierowcy…</p>}
        {error && (
          <div role="alert">
            <p>Nie można pobrać kierowcy. Nie pokazujemy danych innej osoby.</p>
            <button
              className="button button-secondary"
              onClick={() => setRevision((value) => value + 1)}
            >
              Ponów kierowcę
            </button>
          </div>
        )}
        {((mode === "create" && !panel.id) || (mode === "edit" && profile)) &&
        canEdit ? (
          <DriverForm
            key={profile?.id || "new"}
            profile={profile}
            onDirty={setFormDirty}
            onSaved={saved}
            onCancel={() => {
              setFormDirty(false);
              if (profile) setMode("view");
              else onClose();
            }}
          />
        ) : (
          profile && (
            <>
              <p>
                {profile.active ? "Aktywny" : "Nieaktywny"}
                {profile.needs_completion ? " · Dane do uzupełnienia" : ""}
              </p>
              <dl className="driver-profile-fields">
                <div>
                  <dt>Imię</dt>
                  <dd>{profile.first_name || "Do uzupełnienia"}</dd>
                </div>
                <div>
                  <dt>Nazwisko</dt>
                  <dd>{profile.last_name || "Do uzupełnienia"}</dd>
                </div>
                <div>
                  <dt>Identyfikator</dt>
                  <dd>{profile.identifier || "Do uzupełnienia"}</dd>
                </div>
                <div>
                  <dt>Telefon</dt>
                  <dd>
                    {profile.phone ? (
                      <a href={`tel:${profile.phone.replace(/[^+0-9]/g, "")}`}>
                        {profile.phone}
                      </a>
                    ) : (
                      "Nie podano"
                    )}
                  </dd>
                </div>
                <div>
                  <dt>E-mail</dt>
                  <dd>
                    {profile.email ? (
                      <a href={`mailto:${encodeURIComponent(profile.email)}`}>
                        {profile.email}
                      </a>
                    ) : (
                      "Nie podano"
                    )}
                  </dd>
                </div>
                <div>
                  <dt>Wpisane kategorie</dt>
                  <dd>
                    {profile.categories.join(", ") ||
                      "Brak wpisanych kategorii"}
                  </dd>
                </div>
              </dl>
              <p>
                Kategorie są wpisane ręcznie. Ocena zgodności z pojazdem nie
                jest jeszcze dostępna.
              </p>
              {canEdit && (
                <button
                  className="button button-primary"
                  onClick={() => {
                    if (
                      assignmentDirty &&
                      !window.confirm(
                        "Masz niezapisany wybór pojazdu. Odrzucić zmiany?",
                      )
                    )
                      return;
                    setMode("edit");
                    setNotice(null);
                  }}
                >
                  Edytuj kierowcę
                </button>
              )}
              <section ref={section}>
                <DriverAssignments
                  profile={profile}
                  canEdit={canEdit}
                  onProfile={updated}
                  onDirty={setAssignmentDirty}
                />
              </section>
            </>
          )
        )}
      </div>
    </dialog>
  );
}
