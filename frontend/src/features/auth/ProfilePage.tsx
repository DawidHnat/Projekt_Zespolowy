import { useEffect, useId, useState, type FormEvent } from "react";
import { KeyRound, LogOut, UserRound } from "lucide-react";
import { api } from "../../shared/api/client";
import { useAuth } from "./AuthProvider";
import { passwordChangeValidation, profileError, profileRole, type Profile } from "./profile-model";

export function ProfilePage() {
  const auth = useAuth();
  const id = useId();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [revision, setRevision] = useState(0);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [confirmLogout, setConfirmLogout] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setLoadError(false);
    api<Profile>("/auth/profile", { signal: controller.signal })
      .then(value => { if (!controller.signal.aborted) setProfile(value); })
      .catch(() => { if (!controller.signal.aborted) setLoadError(true); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [revision]);
  const changePassword = async (event: FormEvent) => {
    event.preventDefault();
    const validation = passwordChangeValidation(current, next, confirmation);
    setNotice(null); setError(validation);
    if (validation || busy) return;
    setBusy(true);
    try {
      await api("/auth/password/change", {
        method: "POST", body: JSON.stringify({ current_password: current, new_password: next }),
      });
      setNotice("Hasło zostało zmienione. Pozostałe sesje wylogowano; na tym urządzeniu możesz dalej pracować.");
    } catch (err) { setError(profileError(err)); }
    finally {
      setCurrent(""); setNext(""); setConfirmation(""); setBusy(false);
    }
  };
  const logoutAll = async () => {
    if (busy) return;
    setBusy(true); setLogoutError(null);
    try { await auth.logoutAll(); }
    catch (err) { setLogoutError(profileError(err)); setBusy(false); }
  };
  if (loading) return <section className="widget profile-card" role="status">Pobieranie profilu…</section>;
  if (loadError || !profile) return <section className="widget profile-card" role="alert">
    <p>Nie można pobrać profilu.</p>
    <button className="button button-secondary" onClick={() => setRevision(v => v + 1)}>Spróbuj ponownie</button>
  </section>;
  return <div className="profile-page">
    <section className="widget profile-card profile-identity" aria-labelledby={`${id}-identity`}>
      <h2 id={`${id}-identity`}><UserRound size={20} aria-hidden="true" /> Dane konta</h2>
      <dl>
        <div><dt>Imię i nazwisko</dt><dd>{profile.display_name}</dd></div>
        <div><dt>Login</dt><dd>{profile.username}</dd></div>
        <div><dt>E-mail</dt><dd>{profile.email || "Nie ustawiono"}</dd></div>
        <div><dt>Rola</dt><dd>{profileRole(profile.role)}</dd></div>
      </dl>
    </section>
    <section className="widget profile-card" aria-labelledby={`${id}-password`}>
      <h2 id={`${id}-password`}><KeyRound size={20} aria-hidden="true" /> Zmiana hasła</h2>
      <p>Nowe hasło musi mieć od 12 do 1024 znaków. Zmiana wyloguje pozostałe urządzenia.</p>
      <form onSubmit={changePassword} aria-label="Zmiana hasła" aria-busy={busy}>
        <label htmlFor={`${id}-current`}>Aktualne hasło</label>
        <input id={`${id}-current`} type="password" autoComplete="current-password" required maxLength={1024}
          disabled={busy} value={current} onChange={e => setCurrent(e.target.value)} />
        <label htmlFor={`${id}-new`}>Nowe hasło</label>
        <input id={`${id}-new`} type="password" autoComplete="new-password" required minLength={12} maxLength={1024}
          disabled={busy} value={next} onChange={e => setNext(e.target.value)} />
        <label htmlFor={`${id}-confirm`}>Powtórz nowe hasło</label>
        <input id={`${id}-confirm`} type="password" autoComplete="new-password" required minLength={12} maxLength={1024}
          disabled={busy} value={confirmation} onChange={e => setConfirmation(e.target.value)} />
        {error && <p className="profile-error" role="alert">{error}</p>}
        {notice && <p className="profile-success" role="status">{notice}</p>}
        <button className="button button-primary" disabled={busy}>{busy ? "Proszę czekać…" : "Zmień hasło"}</button>
      </form>
    </section>
    <section className="widget profile-card" aria-labelledby={`${id}-sessions`}>
      <h2 id={`${id}-sessions`}><LogOut size={20} aria-hidden="true" /> Aktywne sesje</h2>
      <p>Wyloguj wszystkie urządzenia, także to, z którego teraz korzystasz. Do kolejnego logowania będzie potrzebne hasło.</p>
      {logoutError && <p className="profile-error" role="alert">{logoutError}</p>}
      {confirmLogout ? <div className="profile-confirm" aria-label="Potwierdzenie wylogowania wszystkich sesji">
        <p>Czy wylogować wszystkie sesje tego konta?</p>
        <div className="profile-actions">
          <button className="button button-primary" disabled={busy} onClick={() => void logoutAll()}>Potwierdź wylogowanie wszystkich sesji</button>
          <button className="button button-secondary" disabled={busy} onClick={() => setConfirmLogout(false)}>Anuluj</button>
        </div>
      </div> : <button className="button button-secondary" disabled={busy} onClick={() => setConfirmLogout(true)}>Wyloguj wszystkie urządzenia</button>}
    </section>
  </div>;
}
