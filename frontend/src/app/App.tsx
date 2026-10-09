import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Menu,
  PanelLeftClose,
  Search,
  Settings,
  X,
} from "lucide-react";
import { DashboardGrid } from "../features/dashboard/components/DashboardGrid";
import { useDashboardPreferences } from "./preferences";
import { useLayoutEditor } from "./useLayoutEditor";
import { LayoutEditorControls } from "../features/dashboard/components/LayoutEditorControls";
import { FleetMapPage } from "../features/fleet/components/FleetMapPage";
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

import { useAuth } from "../features/auth/AuthProvider";

const readSection = () => sectionFromHash(window.location.hash);

export function App() {
  const auth = useAuth();
  const [logoutError, setLogoutError] = useState(false);
  const settings = useDashboardPreferences();
  const backgroundMedia = useBackgroundImage();
  const wallpaper = backgroundSource(
    settings.preferences.background,
    backgroundMedia,
  );
  const editor = useLayoutEditor(settings);
  const effective = editor.effective;
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
  const editableView = isDashboard
    ? "dashboard"
    : section === "map"
      ? "map"
      : null;
  const draft = editableView ? editor.drafts[editableView] : undefined;
  const startEditing = () => {
    if (!editableView) return;
    editor.start(editableView);
    setQuery("");
    setSettingsOpen(false);
    setSidebarOpen(false);
  };
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
              <strong>{auth.user?.display_name}</strong>
              <button
                className="logout-button"
                onClick={() =>
                  void auth.logout().catch(() => setLogoutError(true))
                }
              >
                {logoutError ? "Ponów wylogowanie" : "Wyloguj się"}
              </button>
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
              Połączono z API
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
            <div className="page-heading-copy">
              <span className="eyebrow">
                FLEET-FLOW / {current.title.toLocaleUpperCase("pl")}
              </span>
              <h1>
                {current.title}
                <span className="heading-dot">.</span>
              </h1>
              <p>{current.description}</p>
            </div>
            {editableView && (
              <LayoutEditorControls
                title={current.title}
                editing={Boolean(draft)}
                onEdit={startEditing}
                onWidgets={isDashboard ? openSettings : undefined}
                onReset={() => editor.resetView(editableView)}
                onCancel={() => editor.cancel(editableView)}
                onSave={() => editor.save(editableView)}
              />
            )}
          </div>
          {isDashboard ? (
            <>
              <DashboardGrid
                section="dashboard"
                ids={visible}
                layouts={effective.layouts}
                editing={Boolean(draft)}
                onLayout={editor.update}
                onHide={editor.toggleWidget}
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
          ) : section === "map" ? (
            <FleetMapPage
              layouts={effective.layouts}
              editing={Boolean(draft)}
              onLayout={editor.update}
            />
          ) : (
            <WorkspacePage section={current} />
          )}
          <footer className="page-footer">
            <span>
              Fleet-Flow <span className="footer-dot">·</span> Twoja flota pod
              kontrolą
            </span>
            <span>Pomiary WEBFLEET · kierowcy wpisywani ręcznie</span>
          </footer>
        </main>
      </div>
      <AppSettingsPanel
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        preferences={effective}
        persistent={settings.persistent}
        editing={Boolean(editor.drafts.dashboard)}
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
        onToggle={editor.toggleWidget}
        onReset={editor.resetAll}
      />
    </div>
  );
}
