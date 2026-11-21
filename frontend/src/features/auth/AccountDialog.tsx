import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { Mail, X } from "lucide-react";
import { ApiError, api } from "../../shared/api/client";
import {
  accountRoles,
  accountStatuses,
  type Account,
  type AccountRole,
  type AccountStatus,
} from "./accounts-model";

function draftFrom(account: Account | null) {
  return {
    first_name: account?.first_name ?? "",
    last_name: account?.last_name ?? "",
    username: account?.username ?? "",
    email: account?.email ?? "",
    role: account?.role ?? ("viewer" as AccountRole),
    status: account?.status ?? ("pending" as AccountStatus),
  };
}

export function AccountDialog({
  account,
  onClose,
  onSaved,
}: {
  account: Account | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [saved, setSaved] = useState(account);
  const [draft, setDraft] = useState(() => draftFrom(account));
  const [busy, setBusy] = useState<"save" | "send" | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stale, setStale] = useState(false);
  const original = draftFrom(saved);
  const dirty = Object.keys(draft).some((key) => {
    const field = key as keyof typeof draft;
    return draft[field] !== original[field];
  });

  useEffect(() => {
    const dialog = ref.current;
    const opener = document.activeElement;
    dialog?.showModal();
    return () => {
      dialog?.close();
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus();
    };
  }, []);

  const dismiss = () => {
    ref.current?.close();
    onClose();
  };

  const fail = (err: unknown) => {
    if (err instanceof ApiError && err.code === "ACCOUNT_VERSION_CONFLICT") {
      setStale(true);
      onSaved();
    }
    setError(err instanceof Error ? err.message : "Spróbuj ponownie.");
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (busy || stale) return;
    setNotice(null);
    setError(null);
    const values = {
      first_name: draft.first_name.trim() || null,
      last_name: draft.last_name.trim() || null,
      username: draft.username.trim(),
      email: draft.email.trim() || null,
      role: draft.role,
      status: draft.status,
    };
    if (values.first_name && values.last_name && values.first_name.length + values.last_name.length >= 120) {
      setError("Imię i nazwisko razem ze spacją mogą mieć najwyżej 120 znaków.");
      return;
    }
    const body: Record<string, string | number | null> = saved ? { version: saved.version } : {};
    for (const [key, value] of Object.entries(values)) {
      const field = key as keyof typeof values;
      if (saved ? value !== saved[field] : key !== "status") body[key] = value;
    }
    setBusy("save");
    try {
      const result = await api<Account>(saved ? `/admin/users/${saved.id}` : "/admin/users", {
        method: saved ? "PATCH" : "POST",
        body: JSON.stringify(body),
      });
      setSaved(result);
      setDraft(draftFrom(result));
      setNotice(saved ? "Zmiany zapisane." : "Konto utworzone. Wyślij zaproszenie do aktywacji.");
      onSaved();
    } catch (err) {
      fail(err);
    } finally {
      setBusy(null);
    }
  };

  const sendInvitation = async () => {
    if (!saved || !saved.email || busy || stale || dirty) return;
    setError(null);
    setNotice(null);
    setBusy("send");
    try {
      await api(`/admin/users/${saved.id}/activation`, {
        method: "POST",
        body: JSON.stringify({ version: saved.version }),
      });
      setNotice("Serwer pocztowy przyjął zaproszenie.");
    } catch (err) {
      fail(err);
    } finally {
      setBusy(null);
    }
  };

  const statuses: AccountStatus[] = saved?.needs_activation
    ? ["pending", "inactive", "blocked"]
    : ["active", "inactive", "blocked"];

  return (
    <dialog
      className="account-dialog"
      ref={ref}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) dismiss();
      }}
    >
      <header className="account-dialog-header">
        <h2 id={titleId}>{saved ? "Edytuj konto" : "Dodaj konto"}</h2>
        <button type="button" className="icon-button" aria-label="Zamknij" disabled={Boolean(busy)}
          onClick={dismiss}>
          <X size={19} aria-hidden="true" />
        </button>
      </header>
      <form className="account-form" onSubmit={save} aria-busy={Boolean(busy)}>
        <fieldset disabled={Boolean(busy) || stale}>
          <label>Imię
            <input value={draft.first_name} autoComplete="off" maxLength={60} autoFocus
              required={!saved || Boolean(saved.first_name)}
              onChange={(e) => setDraft({ ...draft, first_name: e.target.value })} />
          </label>
          <label>Nazwisko
            <input value={draft.last_name} autoComplete="off" maxLength={60}
              required={!saved || Boolean(saved.last_name)}
              onChange={(e) => setDraft({ ...draft, last_name: e.target.value })} />
          </label>
          <label>Login
            <input value={draft.username} autoComplete="off" maxLength={100} required
              onChange={(e) => setDraft({ ...draft, username: e.target.value })} />
          </label>
          <label>E-mail
            <input value={draft.email} type="email" autoComplete="off" maxLength={254} required={!saved}
              onChange={(e) => setDraft({ ...draft, email: e.target.value })} />
          </label>
          <label>Rola
            <select value={draft.role}
              onChange={(e) => setDraft({ ...draft, role: e.target.value as AccountRole })}>
              {Object.entries(accountRoles).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          {saved && <label>Status konta
            <select value={draft.status}
              onChange={(e) => setDraft({ ...draft, status: e.target.value as AccountStatus })}>
              {statuses.map((status) => <option key={status} value={status}>{accountStatuses[status]}</option>)}
            </select>
          </label>}
        </fieldset>
        {error && <p className="form-error" role="alert">{error}</p>}
        {notice && <p className="auth-notice" role="status">{notice}</p>}
        {saved?.status === "pending" && (
          <div className="account-invite">
            <div>
              <strong>Zaproszenie do aktywacji</strong>
              <p>{saved.email ?? "Dodaj adres e-mail, aby wysłać zaproszenie."}</p>
            </div>
            <button type="button" className="button button-secondary"
              disabled={!saved.email || dirty || stale || Boolean(busy)} onClick={() => void sendInvitation()}>
              <Mail size={16} aria-hidden="true" />
              {busy === "send" ? "Wysyłanie…" : "Wyślij zaproszenie"}
            </button>
          </div>
        )}
        <div className="account-dialog-actions">
          <button type="button" className="button button-secondary" disabled={Boolean(busy)}
            onClick={dismiss}>
            {saved && !dirty ? "Zamknij formularz" : "Anuluj"}
          </button>
          <button className="button button-primary" disabled={Boolean(busy) || stale || Boolean(saved && !dirty)}>
            {busy === "save" ? "Zapisywanie…" : saved ? "Zapisz zmiany" : "Utwórz konto"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
