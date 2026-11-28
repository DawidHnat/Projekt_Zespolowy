import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { LockKeyhole, ArrowRight } from "lucide-react";
import { Brand } from "../../shared/components/Brand";
import { useDashboardPreferences } from "../../app/preferences";
import { useAuth } from "./AuthProvider";
import { PasswordResetForm } from "./PasswordResetForm";
import { EmailChangeConfirmation } from "./EmailChangeConfirmation";
import { activationTokenFromHash, emailTokenFromHash, resetTokenFromHash } from "./reset-model";
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
  const [activated, setActivated] = useState(false);
  const [emailConfirmed, setEmailConfirmed] = useState(false);
  const [emailToken, setEmailToken] = useState(() => emailTokenFromHash(window.location.hash));
  const [activationToken, setActivationToken] = useState(() =>
    activationTokenFromHash(window.location.hash),
  );
  const [resetToken, setResetToken] = useState(() =>
    resetTokenFromHash(window.location.hash),
  );
  useEffect(() => {
    const read = () => {
      const nextEmailToken = emailTokenFromHash(window.location.hash);
      setResetToken(resetTokenFromHash(window.location.hash));
      setActivationToken(activationTokenFromHash(window.location.hash));
      setEmailToken(nextEmailToken);
      setActivated(false);
      setEmailConfirmed(false);
      if (nextEmailToken !== null) {
        setForgot(false);
        setNotice(null);
        setError(null);
      }
    };
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
    setActivationToken(null);
  };
  if (activationToken !== null)
    return (
      <PasswordResetForm
        key={activationToken}
        activation
        token={activationToken}
        onCancel={leaveReset}
        onDone={() => {
          leaveReset();
          setForgot(false);
          setError(null);
          setNotice("Konto zostało aktywowane. Zaloguj się ustawionym hasłem.");
          setActivated(Boolean(auth.user));
        }}
      />
    );
  if (activated)
    return (
      <main className="login-page">
        <section className="login-card">
          <Brand />
          <h1>Konto zostało aktywowane</h1>
          <p role="status">Nowe konto ma już własne hasło.</p>
          <button className="button button-primary" onClick={() => setActivated(false)}>
            Wróć do aplikacji
          </button>
        </section>
      </main>
    );
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
  if (auth.user && (emailToken !== null || emailConfirmed)) {
    const clearEmailLink = () => {
      history.replaceState(
        history.state,
        "",
        window.location.pathname + window.location.search + "#profile",
      );
      setEmailToken(null);
    };
    return (
      <EmailChangeConfirmation
        key={emailToken ?? "confirmed"}
        token={emailToken}
        onConfirmed={() => {
          auth.credentialsChanged();
          clearEmailLink();
          setEmailConfirmed(true);
        }}
        onBack={() => {
          clearEmailLink();
          setEmailConfirmed(false);
        }}
      />
    );
  }
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
    <main className="login-page login-page-composed">
      <div className="login-layout">
        <div className="login-intro">
          <Brand />
          <div className="login-intro-copy">
            <p className="login-eyebrow">Zarządzanie flotą, prościej</p>
            <h1>Twoja flota, pod kontrolą.</h1>
            <p>
              Ważne informacje o pojazdach i ich użytkowaniu — w jednym
              przejrzystym miejscu.
            </p>
          </div>
          <svg
            className="login-art"
            viewBox="0 0 640 320"
            fill="none"
            aria-hidden="true"
            focusable="false"
          >
            <defs>
              <pattern
                id="login-grid"
                width="28"
                height="28"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M28 0H0V28"
                  stroke="var(--border)"
                  strokeOpacity=".7"
                />
              </pattern>
              <linearGradient
                id="login-route"
                gradientUnits="userSpaceOnUse"
                x1="120"
                y1="250"
                x2="526"
                y2="70"
              >
                <stop stopColor="var(--accent)" stopOpacity=".4" />
                <stop offset="1" stopColor="var(--brand-wordmark)" />
              </linearGradient>
            </defs>
            <rect
              x="1"
              y="1"
              width="638"
              height="318"
              rx="24"
              fill="var(--surface)"
              stroke="var(--border)"
            />
            <rect
              x="1"
              y="1"
              width="638"
              height="318"
              rx="24"
              fill="url(#login-grid)"
            />
            <path
              d="M74 247C139 247 148 193 213 193S292 249 350 201 426 111 482 133 531 94 570 74"
              stroke="var(--border)"
              strokeWidth="18"
              strokeLinecap="round"
            />
            <path
              d="M74 247C139 247 148 193 213 193S292 249 350 201 426 111 482 133 531 94 570 74"
              stroke="url(#login-route)"
              strokeWidth="4"
              strokeLinecap="round"
              strokeDasharray="1 11"
            />
            <circle
              cx="74"
              cy="247"
              r="13"
              fill="var(--surface)"
              stroke="var(--accent)"
              strokeWidth="4"
            />
            <circle
              cx="350"
              cy="201"
              r="13"
              fill="var(--surface)"
              stroke="var(--brand-wordmark)"
              strokeWidth="4"
            />
            <circle
              cx="570"
              cy="74"
              r="13"
              fill="var(--surface)"
              stroke="var(--accent)"
              strokeWidth="4"
            />
            <circle cx="570" cy="74" r="4" fill="var(--accent)" />
          </svg>
        </div>
        <section className="login-card">
          <span className="login-symbol">
            <LockKeyhole size={24} />
          </span>
          <p className="login-form-eyebrow">
            {forgot ? "Odzyskiwanie dostępu" : "Witamy z powrotem"}
          </p>
          <h2>
            {forgot
              ? "Nie pamiętasz hasła?"
              : emailToken !== null
                ? "Zaloguj się, aby potwierdzić e-mail"
                : "Zaloguj się"}
          </h2>
          <p className="login-form-description">
            {forgot
              ? "Podaj login swojego konta."
              : emailToken !== null
                ? "Użyj dotychczasowego loginu lub adresu e-mail."
                : "Zaloguj się za pomocą loginu lub adresu e-mail."}
          </p>
          {notice && (
            <p className="auth-notice" role="status">
              {notice}
            </p>
          )}
          {auth.loading ? (
            <p className="login-loading" role="status">Sprawdzanie sesji…</p>
          ) : (
            <form onSubmit={submit} aria-busy={busy}>
              <label>
                Login
                <input
                  autoComplete="username"
                  required
                  maxLength={forgot ? 100 : 254}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
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
      </div>
    </main>
  );
}
