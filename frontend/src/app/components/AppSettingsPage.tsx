import {
  Check,
  Monitor,
  Moon,
  RotateCcw,
  SlidersHorizontal,
  Sun,
  LayoutGrid,
  Sparkles,
  Image,
  ArrowUpRight,
} from "lucide-react";
import {
  ACCENT_PRESETS,
  type DashboardPreferences,
  type ThemeMode,
} from "../preferences";
import {
  WIDGET_IDS,
  type WidgetId,
} from "../../features/dashboard/model/widget-types";
import { widgetRegistry } from "../../features/dashboard/model/widget-registry";
import { BackgroundPicker } from "../../features/dashboard/components/BackgroundPicker";
import type { BackgroundPreferences } from "../../features/dashboard/model/background-model";
import type { BackgroundImageController } from "../../features/dashboard/model/useBackgroundImage";
import { AccountPreferenceNotice } from "../../shared/components/AccountPreferenceNotice";
import type { AccountPreference } from "../../shared/api/account-preferences";

type Props = {
  category: SettingsCategory;
  onCategory: (category: SettingsCategory) => void;
  preferences: DashboardPreferences;
  saving: boolean;
  onChange: (value: DashboardPreferences) => void;
  onToggle: (id: WidgetId) => void;
  onReset: () => void;
  modulesDisabled?: boolean;
  resetDisabled?: boolean;
  editing: boolean;
  backgroundMedia: BackgroundImageController;
  onBackgroundChange: (value: BackgroundPreferences) => void;
  controlsDisabled?: boolean;
  vehicleMigrationAvailable?: boolean;
  onImportVehiclePreferences?: () => void;
  vehiclePreferenceError?: string | null;
  vehiclePreferenceLoading?: boolean;
  vehiclePreferenceSaving?: boolean;
  vehiclePreferenceConflict?: AccountPreference<unknown> | null;
  onRetryVehiclePreferences?: () => void;
  onReloadVehiclePreferences?: () => void;
  onOverwriteVehiclePreferences?: () => void;
};
const modes = [
  { id: "light", label: "Jasny", icon: Sun },
  { id: "dark", label: "Ciemny", icon: Moon },
  { id: "system", label: "System", icon: Monitor },
] as const;

export type SettingsCategory = "appearance" | "background" | "modules";

const categories = [
  {
    id: "appearance",
    title: "Wygląd",
    description: "Motyw, szkło i kolor akcentu",
    icon: Sparkles,
  },
  {
    id: "background",
    title: "Tło",
    description: "Galeria i własne zdjęcia",
    icon: Image,
  },
  {
    id: "modules",
    title: "Układ i moduły",
    description: "Informacje widoczne na Pulpicie",
    icon: LayoutGrid,
  },
] as const;

export function AppSettingsPage({
  category,
  onCategory,
  preferences,
  saving,
  onChange,
  onToggle,
  onReset,
  modulesDisabled = false,
  resetDisabled = false,
  editing,
  backgroundMedia,
  onBackgroundChange,
  controlsDisabled = false,
  vehicleMigrationAvailable = false,
  onImportVehiclePreferences,
  vehiclePreferenceError = null,
  vehiclePreferenceLoading = false,
  vehiclePreferenceSaving = false,
  vehiclePreferenceConflict = null,
  onRetryVehiclePreferences,
  onReloadVehiclePreferences,
  onOverwriteVehiclePreferences,
}: Props) {
  const setTheme = (theme: ThemeMode) => onChange({ ...preferences, theme });
  return (
    <section className="settings-page" aria-label="Konfiguracja aplikacji">
      <nav className="settings-categories" aria-label="Kategorie ustawień">
        {categories.map(({ id, title, description, icon: Icon }) => (
          <button
            key={id}
            aria-pressed={category === id}
            onClick={() => onCategory(id)}
          >
            <Icon size={20} aria-hidden="true" />
            <span>
              <strong>{title}</strong>
              <small>{description}</small>
            </span>
          </button>
        ))}
      </nav>
      <div className="settings-card widget">
        <header className="settings-header">
          <h2>{categories.find((value) => value.id === category)!.title}</h2>
          <p>
            Wygląd, tło, układy i zapisane filtry są powiązane z Twoim kontem
            i odtwarzane na innych urządzeniach.
          </p>
        </header>
        <div className="panel-content settings-content">
          {backgroundMedia.error && (
            <p role="alert" className="background-error">
              {backgroundMedia.error}
            </p>
          )}
          {category === "appearance" && (
            <>
              <fieldset>
                <legend>Styl powierzchni</legend>
                <p>Szkło z połyskiem lub klasyczna, jednolita powierzchnia.</p>
                <div className="material-options">
                  {[
                    { id: "glass", label: "Szkło", icon: Sparkles },
                    { id: "solid", label: "Klasyczny", icon: LayoutGrid },
                  ].map(({ id, label, icon: Icon }) => (
                    <button
                      key={id}
                      aria-pressed={preferences.material === id}
                      className={preferences.material === id ? "selected" : ""}
                      disabled={controlsDisabled}
                      onClick={() =>
                        onChange({
                          ...preferences,
                          material: id as DashboardPreferences["material"],
                        })
                      }
                    >
                      <span
                        className={`material-preview material-preview-${id}`}
                      >
                        <Icon size={22} />
                      </span>
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              </fieldset>
              <fieldset>
                <legend>Motyw</legend>
                <p>Wybierz jasne lub ciemne powierzchnie.</p>
                <div className="theme-options">
                  {modes.map(({ id, label, icon: Icon }) => (
                    <button
                      key={id}
                      className={preferences.theme === id ? "selected" : ""}
                      aria-pressed={preferences.theme === id}
                      disabled={controlsDisabled}
                      onClick={() => setTheme(id)}
                    >
                      <Icon size={21} />
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              </fieldset>
              <fieldset>
                <legend>Kolor akcentu</legend>
                <p>Jeden kolor spójnie zmienia cały interfejs.</p>
                <div className="accent-options">
                  {ACCENT_PRESETS.map((accent) => (
                    <button
                      key={accent.value}
                      className="accent-swatch"
                      style={{ background: accent.value }}
                      aria-label={`Akcent: ${accent.name}`}
                      aria-pressed={
                        preferences.accent.toLowerCase() === accent.value
                      }
                      title={accent.name}
                      disabled={controlsDisabled}
                      onClick={() =>
                        onChange({ ...preferences, accent: accent.value })
                      }
                    >
                      {preferences.accent.toLowerCase() === accent.value && (
                        <Check size={18} />
                      )}
                    </button>
                  ))}
                </div>
                <label className="custom-color">
                  <span>
                    Własny kolor
                    <small>{preferences.accent.toUpperCase()}</small>
                  </span>
                  <input
                    type="color"
                    aria-label="Własny kolor akcentu"
                    value={preferences.accent}
                    disabled={controlsDisabled}
                    onChange={(event) =>
                      onChange({
                        ...preferences,
                        accent: event.currentTarget.value,
                      })
                    }
                  />
                </label>
              </fieldset>
              <div className="typography-note">
                <span className="font-sample">Aa</span>
                <div>
                  <strong>Inter</strong>
                  <p>Jedna czcionka. Spójny rytm całej aplikacji.</p>
                </div>
              </div>
            </>
          )}
          {category === "background" && (
            <BackgroundPicker
              value={preferences.background}
              onChange={onBackgroundChange}
              media={backgroundMedia}
              disabled={controlsDisabled}
            />
          )}
          {category === "modules" && (
            <>
              <fieldset>
                <legend>
                  Moduły Pulpitu{" "}
                  <span className="module-count">
                    {preferences.visibleWidgets.length}/{WIDGET_IDS.length}
                  </span>
                </legend>
                <p>Włącz informacje, które chcesz widzieć na Pulpicie.</p>
                <div className="module-options">
                  {WIDGET_IDS.map((id) => {
                    const widget = widgetRegistry[id];
                    const Icon = widget.icon;
                    return (
                      <label className="module-option" key={id}>
                        <Icon size={19} aria-hidden="true" />
                        <span>
                          {widget.title}
                          <small>{widget.description}</small>
                        </span>
                        <input
                          type="checkbox"
                          checked={preferences.visibleWidgets.includes(id)}
                          onChange={() => onToggle(id)}
                          disabled={modulesDisabled || controlsDisabled}
                          aria-label={`Pokaż moduł: ${widget.title}`}
                        />
                        <span className="switch-track" aria-hidden="true" />
                      </label>
                    );
                  })}
                </div>
              </fieldset>
              <div className="settings-layout-links">
                <h3>Rozmiar i położenie kafelków</h3>
                <p>
                  Otwórz wybrany widok i wybierz „Edytuj układ”. Zmiany
                  zapiszesz lub anulujesz w tym widoku.
                </p>
                {[
                  ["dashboard", "Pulpit"],
                  ["map", "Mapa"],
                  ["vehicles", "Pojazdy"],
                ].map(([id, title]) => (
                  <a
                    className="button button-secondary"
                    key={id}
                    href={`#${id}`}
                  >
                    {title}
                    <ArrowUpRight size={16} />
                  </a>
                ))}
              </div>
              {vehicleMigrationAvailable && (
                <section className="settings-local-import">
                  <h3>Stare ustawienia pojazdów</h3>
                  <p>
                    Ustawienia zapisane wcześniej w tej przeglądarce można
                    jednorazowo zaimportować na to konto.
                  </p>
                  <button
                    className="button button-secondary"
                    type="button"
                    onClick={onImportVehiclePreferences}
                    disabled={controlsDisabled}
                  >
                    Importuj ustawienia pojazdów
                  </button>
                </section>
              )}
              {(vehiclePreferenceLoading ||
                vehiclePreferenceError ||
                vehiclePreferenceConflict) && (
                <AccountPreferenceNotice
                  title="Pojazdy"
                  loading={vehiclePreferenceLoading}
                  saving={vehiclePreferenceSaving}
                  error={vehiclePreferenceError}
                  migrationAvailable={false}
                  conflict={vehiclePreferenceConflict ?? null}
                  onRetry={onRetryVehiclePreferences}
                  onReload={onReloadVehiclePreferences ?? (() => undefined)}
                  onOverwrite={onOverwriteVehiclePreferences ?? (() => undefined)}
                />
              )}
            </>
          )}
        </div>
        <footer className="panel-footer">
          <p>
            <SlidersHorizontal size={13} />
            {editing
              ? "Zapisz lub anuluj edycję układu na Pulpicie"
              : saving
                ? "Zapisywanie preferencji na koncie…"
                : "Preferencje zapisują się automatycznie na koncie"}
          </p>
          <button
            className="button button-secondary"
            onClick={onReset}
            disabled={backgroundMedia.busy || resetDisabled}
          >
            <RotateCcw size={16} />
            Przywróć domyślne
          </button>
          <small className="settings-reset-note">
            Przywraca wygląd, tło oraz układ Pulpitu i Mapy. Zdjęcia pojazdów
            pozostają zachowane.
          </small>
        </footer>
      </div>
    </section>
  );
}
