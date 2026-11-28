import { useEffect, useRef, useState, type FormEvent } from "react";
import { Mail } from "lucide-react";
import { ApiError, api } from "../../shared/api/client";

export function ProfileEmailForm() {
  const [editing, setEditing] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const restoreFocus = useRef(false);

  useEffect(() => {
    if (editing) input.current?.focus();
    else if (restoreFocus.current) {
      trigger.current?.focus();
      restoreFocus.current = false;
    }
  }, [editing]);

  const close = () => {
    restoreFocus.current = true;
    setEditing(false);
    setEmail("");
    setPassword("");
    setError(null);
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (busy) return;
    const newEmail = email.trim();
    setBusy(true);
    setNotice(null);
    setError(null);
    try {
      await api("/auth/email/change/request", {
        method: "POST",
        body: JSON.stringify({ new_email: newEmail, current_password: password }),
      });
      close();
      setNotice(`Link potwierdzający został wysłany na ${newEmail}. Jest ważny przez 20 minut.`);
    } catch (err) {
      if (err instanceof ApiError && err.code === "VALIDATION_ERROR") {
        setError("Sprawdź format nowego adresu e-mail.");
      } else {
        setError(err instanceof Error ? err.message : "Nie udało się wysłać linku.");
      }
    } finally {
      setPassword("");
      setBusy(false);
    }
  };

  return (
    <div className="profile-email">
      <p className={notice ? "profile-success" : "sr-only"} role="status">{notice}</p>
      {editing ? (
        <form onSubmit={submit} aria-label="Zmiana adresu e-mail" aria-busy={busy}>
          <p>Adres zostanie zapisany po potwierdzeniu linku na nowej skrzynce.</p>
          <label>
            Nowy adres e-mail
            <input
              ref={input}
              value={email}
              inputMode="email"
              autoComplete="email"
              spellCheck={false}
              required
              maxLength={254}
              disabled={busy}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label>
            Aktualne hasło
            <input
              value={password}
              type="password"
              autoComplete="current-password"
              required
              maxLength={1024}
              disabled={busy}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>
          {error && <p className="profile-error" role="alert">{error}</p>}
          <div className="profile-actions">
            <button className="button button-primary" disabled={busy}>
              {busy ? "Wysyłanie…" : "Wyślij link potwierdzający"}
            </button>
            <button type="button" className="button button-secondary" onClick={close} disabled={busy}>
              Anuluj
            </button>
          </div>
        </form>
      ) : (
        <button
          ref={trigger}
          className="button button-secondary"
          onClick={() => { setNotice(null); setEditing(true); }}
        >
          <Mail size={16} aria-hidden="true" /> Zmień adres e-mail
        </button>
      )}
    </div>
  );
}
