import { useEffect, useRef } from "react";
import {
  Check,
  Monitor,
  Moon,
  RotateCcw,
  SlidersHorizontal,
  Sun,
  X,
  LayoutGrid,
  Sparkles,
} from "lucide-react";
import {
  ACCENT_PRESETS,
  type DashboardPreferences,
  type ThemeMode,
} from "../../../app/preferences";
import { WIDGET_IDS, type WidgetId } from "../model/widget-types";
import { widgetRegistry } from "../model/widget-registry";

type Props = {
  open: boolean;
  onClose: () => void;
  preferences: DashboardPreferences;
  persistent: boolean;
  onChange: (value: DashboardPreferences) => void;
  onToggle: (id: WidgetId) => void;
  onReset: () => void;
  onEdit: () => void;
  editing: boolean;
};
const modes = [
  { id: "light", label: "Jasny", icon: Sun },
  { id: "dark", label: "Ciemny", icon: Moon },
  { id: "system", label: "System", icon: Monitor },
] as const;

export function AppearancePanel({
  open,
  onClose,
  preferences,
  persistent,
  onChange,
  onToggle,
  onReset,
  onEdit,
  editing,
}: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = dialogRef.current;
    if (open && dialog && !dialog.open) dialog.showModal();
    if (!open && dialog?.open) dialog.close();
  }, [open]);
  const setTheme = (theme: ThemeMode) => onChange({ ...preferences, theme });
  return (
    <dialog
      ref={dialogRef}
      className="appearance-panel"
      onClose={onClose}
      aria-labelledby="appearance-title"
      onClick={(event) => {
        const bounds = event.currentTarget.getBoundingClientRect();
        if (
          event.target === event.currentTarget &&
          (event.clientX < bounds.left ||
            event.clientX > bounds.right ||
            event.clientY < bounds.top ||
            event.clientY > bounds.bottom)
        )
          onClose();
      }}
    >
      <header className="panel-header">
        <div>
          <span className="eyebrow">TWÓJ WIDOK</span>
          <h2 id="appearance-title">Dopasuj dashboard</h2>
        </div>
        <button
          className="icon-button"
          aria-label="Zamknij personalizację"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </header>
      <div className="panel-content">
        <div className="layout-entry">
          <span className="layout-entry-icon">
            <LayoutGrid size={23} />
          </span>
          <h3>Każdy moduł na swoim miejscu</h3>
          <p>
            Przesuwaj widgety i dopasuj ich rozmiar do swojego sposobu pracy.
          </p>
          <button className="button button-primary" onClick={onEdit}>
            <LayoutGrid size={16} />
            {editing ? "Wróć do edycji układu" : "Edytuj układ"}
          </button>
        </div>
        <fieldset>
          <legend>Styl powierzchni</legend>
          <p>Subtelne szkło lub klasyczna, jednolita powierzchnia.</p>
          <div className="material-options">
            {[
              { id: "glass", label: "Szkło", icon: Sparkles },
              { id: "solid", label: "Klasyczny", icon: LayoutGrid },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                aria-pressed={preferences.material === id}
                className={preferences.material === id ? "selected" : ""}
                onClick={() =>
                  onChange({
                    ...preferences,
                    material: id as DashboardPreferences["material"],
                  })
                }
              >
                <span className={`material-preview material-preview-${id}`}>
                  <Icon size={22} />
                </span>
                <span>{label}</span>
              </button>
            ))}
          </div>
        </fieldset>
        <fieldset>
          <legend>Motyw</legend>
          <p>Wybierz tło wygodne dla Twoich oczu.</p>
          <div className="theme-options">
            {modes.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                className={preferences.theme === id ? "selected" : ""}
                aria-pressed={preferences.theme === id}
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
                aria-pressed={preferences.accent.toLowerCase() === accent.value}
                title={accent.name}
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
              Własny kolor<small>{preferences.accent.toUpperCase()}</small>
            </span>
            <input
              type="color"
              aria-label="Własny kolor akcentu"
              value={preferences.accent}
              onInput={(event) =>
                onChange({ ...preferences, accent: event.currentTarget.value })
              }
            />
          </label>
        </fieldset>
        <fieldset>
          <legend>
            Moduły dashboardu{" "}
            <span className="module-count">
              {preferences.visibleWidgets.length}/{WIDGET_IDS.length}
            </span>
          </legend>
          <p>Włącz informacje, z których korzystasz.</p>
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
                    aria-label={`Pokaż moduł: ${widget.title}`}
                  />
                  <span className="switch-track" aria-hidden="true" />
                </label>
              );
            })}
          </div>
        </fieldset>
        <div className="typography-note">
          <span className="font-sample">Aa</span>
          <div>
            <strong>Inter</strong>
            <p>Jedna czcionka. Spójny rytm całej aplikacji.</p>
          </div>
        </div>
      </div>
      <footer className="panel-footer">
        <p>
          <SlidersHorizontal size={13} />
          {editing
            ? "Układ czeka na zapisanie w trybie edycji"
            : persistent
              ? "Ustawienia zapisane na tym urządzeniu"
              : "Ustawienia działają w tej sesji"}
        </p>
        <button className="button button-secondary" onClick={onReset}>
          <RotateCcw size={16} />
          Przywróć domyślne
        </button>
      </footer>
    </dialog>
  );
}
