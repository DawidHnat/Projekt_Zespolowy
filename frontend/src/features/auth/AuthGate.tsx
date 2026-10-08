import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { LockKeyhole, ArrowRight } from "lucide-react";
import { Brand } from "../../shared/components/Brand";
import { useDashboardPreferences } from "../../app/preferences";
import { useAuth } from "./AuthProvider";
import { PasswordResetForm } from "./PasswordResetForm";
import { resetTokenFromHash } from "./reset-model";
import { api } from "../../shared/api/client";

export function AuthGate({ children }: { children: ReactNode }) {
  const auth = useAuth();
  useDashboardPreferences();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forgot, setForgot] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [resetToken, setResetToken] = useState(() =>
    resetTokenFromHash(window.location.hash),
  );
  useEffect(() => {
    const read = () => setResetToken(resetTokenFromHash(window.location.hash));
    window.addEventListener("hashchange", read);
    return () => window.removeEventListener("hashchange", read);
  }, []);
  const leaveReset = () => {
    history.replaceState(
      null,
      "",
      window.location.pathname + window.location.search + "#dashboard",
    );
    setResetToken(null);
  };
  if (resetToken !== null)
    return (
      <PasswordResetForm
        token={resetToken}
        onCancel={leaveReset}
        onDone={() => {
          leaveReset();
          setNotice("Hasło zostało zmienione. Zaloguj się nowym hasłem.");
        }}
      />
    );
  if (auth.user) return children;
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (forgot) {
        await api(
          "/auth/password/request",
          { method: "POST", body: JSON.stringify({ username }) },
          false,
        );
        setNotice(
          "Jeśli konto ma skonfigurowany adres e-mail, otrzymasz link do zmiany hasła.",
        );
      } else await auth.login(username, password);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Logowanie nie powiodło się.",
      );
    } finally {
      setPassword("");
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
        <h1>
          {forgot ? "Nie pamiętasz hasła?" : "Twoja flota, pod kontrolą."}
        </h1>
        <p>
          {forgot
            ? "Podaj login swojego konta."
            : "Zaloguj się do przestrzeni Fleet-Flow."}
        </p>
        {notice && (
          <p className="auth-notice" role="status">
            {notice}
          </p>
        )}
        {auth.loading ? (
          <p role="status">Sprawdzanie sesji…</p>
        ) : (
          <form onSubmit={submit}>
            <label>
              Login
              <input
                autoComplete="username"
                required
                maxLength={100}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
              />
            </label>
            {!forgot && (
              <label>
                Hasło
                <input
                  type="password"
                  autoComplete="current-password"
                  required
                  maxLength={1024}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
            )}
            {(error || auth.error) && (
              <p className="form-error" role="alert">
                {error || auth.error}
              </p>
            )}
            <button className="button button-primary" disabled={busy}>
              {busy ? "Proszę czekać…" : forgot ? "Wyślij link" : "Zaloguj się"}
              <ArrowRight size={18} />
            </button>
            <button
              type="button"
              className="logout-button"
              onClick={() => {
                setForgot(!forgot);
                setError(null);
                setNotice(null);
                setPassword("");
              }}
            >
              {forgot ? "Wróć do logowania" : "Nie pamiętam hasła"}
            </button>
            {auth.error && (
              <button
                type="button"
                className="button button-secondary"
                onClick={auth.retry}
              >
                Sprawdź połączenie
              </button>
            )}
          </form>
        )}
        <small>Dostęp nadaje administrator zespołu.</small>
      </section>
    </main>
  );
}
