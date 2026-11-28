import { useEffect, useRef, useState, type FormEvent } from "react";
import { MailCheck } from "lucide-react";
import { api } from "../../shared/api/client";
import { Brand } from "../../shared/components/Brand";
import { validResetToken } from "./reset-model";

export function EmailChangeConfirmation({
  token,
  onConfirmed,
  onBack,
}: {
  token: string | null;
  onConfirmed: () => void;
  onBack: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(false);
  const title = useRef<HTMLHeadingElement>(null);
  const valid = token !== null && validResetToken(token);

  useEffect(() => {
    mounted.current = true;
    title.current?.focus();
    return () => { mounted.current = false; };
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!valid || busy) return;
    setError(null);
    setBusy(true);
    try {
      await api("/auth/email/change/confirm", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      if (mounted.current) onConfirmed();
    } catch (err) {
      if (mounted.current)
        setError(err instanceof Error ? err.message : "Nie udało się potwierdzić adresu e-mail.");
    } finally {
      if (mounted.current) setBusy(false);
    }
  };

  return (
    <main className="login-page">
      <section className="login-card">
        <Brand />
        <span className="login-symbol"><MailCheck size={28} aria-hidden="true" /></span>
        <h1 ref={title} tabIndex={-1}>
          {token === null ? "Adres e-mail został zmieniony" : "Potwierdź zmianę e-maila"}
        </h1>
        {token === null ? (
          <p role="status">Od teraz możesz logować się nowym adresem. Pozostałe sesje zostały wylogowane.</p>
        ) : valid ? (
          <form onSubmit={submit} aria-busy={busy}>
            <p>Potwierdź, aby przypisać nowy adres do zalogowanego konta.</p>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="button button-primary" disabled={busy}>
              {busy ? "Potwierdzanie…" : "Potwierdź zmianę adresu"}
            </button>
          </form>
        ) : (
          <p role="alert">Link jest niepoprawny. Poproś o nowy link w Profilu.</p>
        )}
        <button className="button button-secondary" disabled={busy} onClick={onBack}>
          Wróć do profilu
        </button>
      </section>
    </main>
  );
}
