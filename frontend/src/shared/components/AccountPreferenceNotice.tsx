import type { AccountPreference } from "../api/account-preferences";

type Props<T> = {
  title: string;
  loading: boolean;
  error: string | null;
  saving?: boolean;
  migrationAvailable: boolean;
  conflict: AccountPreference<T> | null;
  onImport: () => void;
  onDefaults: () => void;
  onReload: () => void;
  onOverwrite: () => void;
};

export function AccountPreferenceNotice<T>({
  title,
  loading,
  error,
  saving = false,
  migrationAvailable,
  conflict,
  onImport,
  onDefaults,
  onReload,
  onOverwrite,
}: Props<T>) {
  return (
    <div className="account-preference-notice">
      {loading && <p role="status">Pobieranie zapisanych ustawień: {title}…</p>}
      {error && <p role="alert">{error}</p>}
      {migrationAvailable && (
        <section aria-label={`Migracja ustawień: ${title}`}>
          <p>
            Znaleziono ustawienia {title} zapisane w tej przeglądarce. Wybierz,
            czy przenieść je na konto, czy zacząć od ustawień domyślnych.
          </p>
          <button type="button" onClick={onImport} disabled={saving}>
            Przenieś z tej przeglądarki
          </button>
          <button type="button" onClick={onDefaults} disabled={saving}>
            Użyj domyślnych konta
          </button>
        </section>
      )}
      {conflict && (
        <section role="alert">
          <p>
            Ustawienia {title} zmieniły się na innym urządzeniu. Twoje zmiany
            są zachowane; wybierz, czy wczytać wersję {conflict.version}, czy
            zapisać swoje zmiany na jej podstawie.
          </p>
          <button type="button" onClick={onReload} disabled={saving}>
            Wczytaj wersję z konta
          </button>
          <button type="button" onClick={onOverwrite} disabled={saving}>
            Zapisz moje zmiany
          </button>
        </section>
      )}
    </div>
  );
}
