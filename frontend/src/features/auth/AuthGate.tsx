import { useState, type FormEvent, type ReactNode } from "react";
import { LockKeyhole, ArrowRight } from "lucide-react";
import { Brand } from "../../shared/components/Brand";
import { useDashboardPreferences } from "../../app/preferences";
import { useAuth } from "./AuthProvider";

export function AuthGate({ children }: { children: ReactNode }) {
  const auth = useAuth();
  useDashboardPreferences();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (auth.user) return children;
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await auth.login(username, password);
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
        <h1>Twoja flota, pod kontrolą.</h1>
        <p>Zaloguj się do przestrzeni Fleet-Flow.</p>
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
            {(error || auth.error) && (
              <p className="form-error" role="alert">
                {error || auth.error}
              </p>
            )}
            <button className="button button-primary" disabled={busy}>
              {busy ? "Logowanie…" : "Zaloguj się"}
              <ArrowRight size={18} />
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
