import type { AccountPreference } from "../api/account-preferences";

type Props<T> = {
  title: string;
  loading: boolean;
  error: string | null;
  saving?: boolean;
  migrationAvailable: boolean;
  conflict: AccountPreference<T> | null;
  onImport?: () => void;
  onRetry?: () => void;
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
  onRetry,
  onReload,
  onOverwrite,
}: Props<T>) {
  return (
    <div className="account-preference-notice">
      {loading && <p role="status">Pobieranie zapisanych ustawień: {title}…</p>}
      {saving && <p role="status">Zapisywanie ustawień {title} na koncie…</p>}
      {error && (
        <div role="alert">
          <p>{error}</p>
          {onRetry && !conflict && (
            <button type="button" onClick={onRetry} disabled={saving}>
              Ponów zapis
            </button>
          )}
        </div>
      )}
      {migrationAvailable && (
        <section aria-label={`Migracja ustawień: ${title}`}>
          <p>
            Znaleziono stare ustawienia {title} z tej przeglądarki. Możesz
            zaimportować je jednorazowo; istniejące ustawienia konta nie zostaną
            nadpisane.
          </p>
          {onImport && (
            <button type="button" onClick={onImport} disabled={saving || loading}>
              Importuj stare ustawienia
            </button>
          )}
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
