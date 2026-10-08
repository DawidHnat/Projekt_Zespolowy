import { useState, type FormEvent } from "react";
import { LockKeyhole } from "lucide-react";
import { api } from "../../shared/api/client";
import { Brand } from "../../shared/components/Brand";
import { validResetToken } from "./reset-model";
import { useAuth } from "./AuthProvider";

export function PasswordResetForm({
  token,
  onDone,
  onCancel,
}: {
  token: string;
  onDone: () => void;
  onCancel: () => void;
}) {
  const auth = useAuth();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const valid = validResetToken(token);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Hasła muszą być identyczne.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api(
        "/auth/password/confirm",
        { method: "POST", body: JSON.stringify({ token, password }) },
        false,
      );
      auth.clearSession();
      onDone();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nie udało się zmienić hasła.");
    } finally {
      setPassword("");
      setConfirm("");
      setBusy(false);
    }
  };
  return (
    <main className="login-page">
      <section className="login-card">
        <Brand />
        <span className="login-symbol">
          <LockKeyhole size={28} />
        </span>
        <h1>Ustaw nowe hasło.</h1>
        <p>Link działa jeden raz i jest ważny przez 20 minut.</p>
        {valid ? (
          <form onSubmit={submit}>
            <label>
              Nowe hasło
              <input
                type="password"
                autoComplete="new-password"
                required
                minLength={12}
                maxLength={1024}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
            <label>
              Powtórz hasło
              <input
                type="password"
                autoComplete="new-password"
                required
                minLength={12}
                maxLength={1024}
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
              />
            </label>
            <small>
              Co najmniej 12 znaków. Po zmianie wszystkie wcześniejsze sesje
              wygasną.
            </small>
            {error && (
              <p role="alert" className="form-error">
                {error}
              </p>
            )}
            <button className="button button-primary" disabled={busy}>
              {busy ? "Zapisywanie…" : "Zapisz nowe hasło"}
            </button>
          </form>
        ) : (
          <p role="alert">
            Ten link jest niepoprawny. Poproś o nowy na ekranie logowania.
          </p>
        )}
        <button className="button button-secondary" onClick={onCancel}>
          Wróć
        </button>
      </section>
    </main>
  );
}
