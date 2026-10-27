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
import {
  AppSettingsPage,
  type SettingsCategory,
} from "./components/AppSettingsPage";
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
import { ProfilePage } from "../features/auth/ProfilePage";
import { VehicleCardsPage } from "../features/fleet/components/VehicleCardsPage";
import { VehicleLayoutEditorControls } from "../features/fleet/components/VehicleLayoutEditorControls";
import { VehicleDetailsDialog } from "../features/fleet/components/VehicleDetailsDialog";

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
  const [settingsCategory, setSettingsCategory] =
    useState<SettingsCategory>("appearance");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const openSettings = (category: SettingsCategory = "appearance") => {
    setSettingsCategory(category);
    window.location.hash = "settings";
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
          {sections
            .filter((value) => value.id !== "settings" && value.id !== "profile")
            .map(({ id, title, icon: Icon }) => (
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
          <a
            className={`nav-item settings-nav-item ${section === "settings" ? "active" : ""}`}
            href="#settings"
            aria-current={section === "settings" ? "page" : undefined}
          >
            <Settings size={19} aria-hidden="true" />
            <span>Ustawienia</span>
          </a>
          <div className="workspace">
            <span className="workspace-avatar">FF</span>
            <div>
              <a href="#profile" className="workspace-profile" aria-label="Otwórz profil użytkownika"
                aria-current={section === "profile" ? "page" : undefined}>
                <strong>{auth.user?.display_name}</strong>
              </a>
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
            <a
              className="icon-button settings-shortcut"
              href="#settings"
              aria-label="Ustawienia aplikacji"
            >
              <Settings size={18} />
            </a>
          </div>
        </header>
        <main
          id="main-content"
          className={`main-content ${section === "map" ? "map-main-content" : ""}`}
          tabIndex={-1}
        >
          <div
            className={`page-heading ${section === "vehicles" ? "vehicles-page-heading" : ""}`}
          >
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
                onWidgets={
                  isDashboard ? () => openSettings("modules") : undefined
                }
                onReset={() => editor.resetView(editableView)}
                onCancel={() => editor.cancel(editableView)}
                onSave={() => editor.save(editableView)}
              />
            )}
            {section === "vehicles" && (
              <VehicleLayoutEditorControls />
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
                    onClick={() => openSettings("modules")}
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
          ) : section === "vehicles" ? (
            <VehicleCardsPage />
          ) : section === "profile" ? (
            <ProfilePage />
          ) : section === "settings" ? (
            <AppSettingsPage
              category={settingsCategory}
              onCategory={setSettingsCategory}
              preferences={effective}
              persistent={settings.persistent}
              editing={Boolean(editor.drafts.dashboard)}
              backgroundMedia={backgroundMedia}
              onBackgroundChange={(background) =>
                settings.setPreferences((previous) => ({
                  ...previous,
                  background,
                }))
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
          ) : (
            <WorkspacePage section={current} />
          )}
        </main>
      </div>
      <VehicleDetailsDialog />
    </div>
  );
}
