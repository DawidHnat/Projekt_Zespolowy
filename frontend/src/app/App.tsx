import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Menu,
  PanelLeftClose,
  Search,
  Settings,
  X,
  Check,
  Plus,
  RotateCcw,
  Grip,
} from "lucide-react";
import { defaultPreferences, type Arrangement } from "./preferences";
import { DashboardGrid } from "../features/dashboard/components/DashboardGrid";
import {
  mergeLayout,
  sameGeometry,
  defaultLayout,
} from "../features/dashboard/model/widget-layout";
import { useDashboardPreferences } from "./preferences";
import { AppSettingsPanel } from "./components/AppSettingsPanel";
import { sections, sectionFromHash } from "./navigation";
import { WorkspacePage } from "./WorkspacePage";
import { Brand } from "../shared/components/Brand";
import {
  DashboardBackground,
  backgroundSource,
} from "../features/dashboard/components/DashboardBackground";
import { useBackgroundImage } from "../features/dashboard/model/useBackgroundImage";
import { widgetRegistry } from "../features/dashboard/model/widget-registry";
import { WIDGET_IDS } from "../features/dashboard/model/widget-types";

const readSection = () => sectionFromHash(window.location.hash);

export function App() {
  const settings = useDashboardPreferences();
  const backgroundMedia = useBackgroundImage();
  const wallpaper = backgroundSource(
    settings.preferences.background,
    backgroundMedia,
  );
  const [draft, setDraft] = useState<Arrangement | null>(null);
  const effective = { ...settings.preferences, ...(draft ?? {}) };
  const startEditing = () => {
    if (!draft)
      setDraft(
        structuredClone({
          visibleWidgets: settings.preferences.visibleWidgets,
          layouts: settings.preferences.layouts,
        }),
      );
    setQuery("");
    setSettingsOpen(false);
    setSidebarOpen(false);
  };
  const toggleWidget = (id: (typeof WIDGET_IDS)[number]) => {
    if (!draft) {
      settings.toggleWidget(id);
      return;
    }
    setDraft({
      ...draft,
      visibleWidgets: draft.visibleWidgets.includes(id)
        ? draft.visibleWidgets.filter((value) => value !== id)
        : [...draft.visibleWidgets, id],
    });
  };
  const [section, setSection] = useState(readSection);
  const [query, setQuery] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const openSettings = () => {
    setSettingsOpen(true);
    setSidebarOpen(false);
  };
  useEffect(() => {
    const handleHash = () => {
      if (window.location.hash === "#main-content") return;
      setSection(readSection());
      setQuery("");
      setSidebarOpen(false);
      window.scrollTo({ top: 0 });
    };
    window.addEventListener("hashchange", handleHash);
    return () => window.removeEventListener("hashchange", handleHash);
  }, []);
  useEffect(() => {
    if (!sidebarOpen) return;
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSidebarOpen(false);
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [sidebarOpen]);
  const current = sections.find((value) => value.id === section)!;
  const SectionIcon = current.icon;
  const isDashboard = section === "dashboard";
  useEffect(() => {
    document.title = `${current.title} · Fleet-Flow`;
  }, [current.title]);
  const visible = WIDGET_IDS.filter(
    (id) =>
      effective.visibleWidgets.includes(id) &&
      widgetRegistry[id].title
        .toLocaleLowerCase("pl")
        .includes(query.trim().toLocaleLowerCase("pl")),
  );
  return (
    <div className="app-shell" data-background={Boolean(wallpaper)}>
      <DashboardBackground
        source={wallpaper}
        preferences={settings.preferences.background}
      />
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        Przejdź do treści
      </a>
      {sidebarOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="Zamknij menu"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside
        className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}
        aria-label="Menu główne"
      >
        <div className="sidebar-brand">
          <Brand />
          <button
            className="icon-button mobile-only"
            aria-label="Zamknij menu"
            onClick={() => setSidebarOpen(false)}
          >
            <PanelLeftClose size={20} />
          </button>
        </div>
        <span className="nav-label">PRZEGLĄD</span>
        <nav aria-label="Sekcje aplikacji">
          {sections.map(({ id, title, icon: Icon }) => (
            <a
              key={id}
              href={`#${id}`}
              className={`nav-item ${section === id ? "active" : ""}`}
              aria-current={section === id ? "page" : undefined}
            >
              <Icon size={19} aria-hidden="true" />
              <span>{title}</span>
              {section === id && <span className="nav-indicator" />}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button
            className="nav-item settings-nav-item"
            onClick={openSettings}
            aria-haspopup="dialog"
            aria-expanded={settingsOpen}
            aria-controls="app-settings"
          >
            <Settings size={19} aria-hidden="true" />
            <span>Ustawienia</span>
          </button>
          <div className="workspace">
            <span className="workspace-avatar">FF</span>
            <div>
              <strong>Zespół Fleet-Flow</strong>
              <small>Podgląd interfejsu</small>
            </div>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-start">
            <button
              className="icon-button mobile-only"
              aria-label="Otwórz menu"
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen(true)}
            >
              <Menu size={21} />
            </button>
            {isDashboard ? (
              <label className="module-search">
                <Search size={17} aria-hidden="true" />
                <input
                  type="search"
                  disabled={Boolean(draft)}
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Szukaj modułu…"
                  aria-label="Szukaj modułu"
                />
              </label>
            ) : (
              <span className="topbar-section">
                <SectionIcon size={17} aria-hidden="true" />
                {current.title}
              </span>
            )}
          </div>
          <div className="topbar-actions">
            <span className="preview-badge">
              <i />
              Podgląd interfejsu
            </span>
            <button
              className="icon-button settings-shortcut"
              onClick={openSettings}
              aria-label="Ustawienia aplikacji"
              aria-haspopup="dialog"
              aria-expanded={settingsOpen}
              aria-controls="app-settings"
            >
              <Settings size={18} />
            </button>
            <span className="topbar-divider" />
            <span className="topbar-avatar" aria-label="Przestrzeń zespołu">
              FF
            </span>
          </div>
        </header>
        <main
          id="main-content"
          className={`main-content ${section === "map" ? "map-main-content" : ""}`}
          tabIndex={-1}
        >
          <div className="page-heading">
            <div>
              <span className="eyebrow">
                FLEET-FLOW / {current.title.toLocaleUpperCase("pl")}
              </span>
              <h1>
                {current.title}
                <span className="heading-dot">.</span>
              </h1>
              <p>{current.description}</p>
            </div>
            {isDashboard && !draft && (
              <button
                className="button button-primary"
                onClick={startEditing}
              >
                <Grip size={17} />
                Edytuj układ
              </button>
            )}
          </div>
          {isDashboard ? (
            <>
              {draft && (
                <div
                  className="layout-edit-bar"
                  role="region"
                  aria-label="Edycja układu"
                >
                  <div className="edit-bar-intro">
                    <span className="edit-bar-icon">
                      <Grip size={19} />
                    </span>
                    <div>
                      <strong>Ułóż po swojemu</strong>
                      <p>
                        Przeciągnij uchwyt · rozciągnij narożnik · dopasuj rozmiar
                      </p>
                    </div>
                  </div>
                  <div className="edit-bar-actions">
                    <button
                      className="icon-button"
                      aria-label="Wybierz widgety"
                      title="Wybierz widgety"
                      onClick={openSettings}
                    >
                      <Plus size={19} />
                    </button>
                    <button
                      className="icon-button"
                      aria-label="Przywróć układ tego widoku"
                      title="Przywróć układ tego widoku"
                      onClick={() =>
                        setDraft({
                          ...draft,
                          layouts: {
                            ...draft.layouts,
                            dashboard: {
                              desktop: defaultLayout("dashboard", "desktop"),
                              compact: defaultLayout("dashboard", "compact"),
                            },
                          },
                        })
                      }
                    >
                      <RotateCcw size={17} />
                    </button>
                    <button
                      className="button button-secondary"
                      onClick={() => setDraft(null)}
                    >
                      Anuluj
                    </button>
                    <button
                      className="button button-primary"
                      onClick={() => {
                        settings.setPreferences({
                          ...settings.preferences,
                          ...draft,
                        });
                        setDraft(null);
                      }}
                    >
                      <Check size={16} />
                      Zapisz układ
                    </button>
                  </div>
                </div>
              )}
              <DashboardGrid
                section="dashboard"
                ids={visible}
                layouts={effective.layouts}
                editing={Boolean(draft)}
                onLayout={(view, profile, layout) =>
                  setDraft((previous) => {
                    if (!previous) return previous;
                    const merged = mergeLayout(
                      previous.layouts[view][profile],
                      layout,
                      profile,
                    );
                    if (sameGeometry(previous.layouts[view][profile], merged))
                      return previous;
                    return {
                      ...previous,
                      layouts: {
                        ...previous.layouts,
                        [view]: { ...previous.layouts[view], [profile]: merged },
                      },
                    };
                  })
                }
                onHide={toggleWidget}
              />
              {visible.length === 0 && (
                <div className="dashboard-empty">
                  <LayoutDashboard size={35} />
                  <h2>
                    {query
                      ? "Nie znaleziono modułu"
                      : "To miejsce jest gotowe na Twój widok"}
                  </h2>
                  <p>
                    {query
                      ? "Spróbuj innej nazwy lub włącz moduł w ustawieniach."
                      : "Wybierz moduły, które chcesz mieć pod ręką."}
                  </p>
                  {query && (
                    <button
                      className="button button-secondary"
                      onClick={() => setQuery("")}
                    >
                      <X size={16} />
                      Wyczyść wyszukiwanie
                    </button>
                  )}
                  <button
                    className="button button-primary"
                    onClick={openSettings}
                  >
                    Wybierz moduły
                  </button>
                </div>
              )}
            </>
          ) : (
            <WorkspacePage section={current} />
          )}
          <footer className="page-footer">
            <span>
              Fleet-Flow <span className="footer-dot">·</span> Twoja flota pod
              kontrolą
            </span>
            <span>Widok przygotowany do podłączenia danych</span>
          </footer>
        </main>
      </div>
      <AppSettingsPanel
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        preferences={effective}
        persistent={settings.persistent}
        editing={Boolean(draft)}
        backgroundMedia={backgroundMedia}
        onBackgroundChange={(background) =>
          settings.setPreferences((previous) => ({ ...previous, background }))
        }
        onChange={(next) =>
          settings.setPreferences({
            ...settings.preferences,
            theme: next.theme,
            accent: next.accent,
            material: next.material,
          })
        }
        onToggle={toggleWidget}
        onReset={() => {
          const next = defaultPreferences();
          if (draft) {
            settings.setPreferences({
              ...next,
              layouts: settings.preferences.layouts,
              visibleWidgets: settings.preferences.visibleWidgets,
            });
            setDraft({
              layouts: next.layouts,
              visibleWidgets: next.visibleWidgets,
            });
          } else settings.reset();
        }}
      />
    </div>
  );
}
