import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  ChartNoAxesCombined,
  LayoutDashboard,
  Menu,
  Moon,
  PanelLeftClose,
  Route,
  Search,
  SlidersHorizontal,
  Sun,
  Truck,
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
import { AppearancePanel } from "../features/dashboard/components/AppearancePanel";
import { Brand } from "../shared/components/Brand";
import {
  DashboardBackground,
  backgroundSource,
} from "../features/dashboard/components/DashboardBackground";
import { useBackgroundImage } from "../features/dashboard/model/useBackgroundImage";
import { widgetRegistry } from "../features/dashboard/model/widget-registry";
import {
  WIDGET_IDS,
  type SectionId,
} from "../features/dashboard/model/widget-types";

const sections = [
  {
    id: "dashboard",
    title: "Dashboard",
    icon: LayoutDashboard,
    description:
      "Twoja flota, Twój widok. Najważniejsze informacje w jednym miejscu.",
  },
  {
    id: "fleet",
    title: "Flota",
    icon: Truck,
    description: "Lista pojazdów i ich pozycje. Wszystko pod ręką.",
  },
  {
    id: "trips",
    title: "Przejazdy",
    icon: Route,
    description: "Historia tras i informacje potrzebne do ewidencji przebiegu.",
  },
  {
    id: "analytics",
    title: "Analityka",
    icon: ChartNoAxesCombined,
    description: "Wskaźniki, wykorzystanie pojazdów i zdarzenia z floty.",
  },
] as const;
function readSection(): SectionId {
  const hash = window.location.hash.slice(1);
  return sections.find((section) => section.id === hash)?.id ?? "dashboard";
}

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
    setAppearanceOpen(false);
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
  const [appearanceOpen, setAppearanceOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
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
  const visible = WIDGET_IDS.filter(
    (id) =>
      effective.visibleWidgets.includes(id) &&
      widgetRegistry[id].sections.includes(section) &&
      widgetRegistry[id].title
        .toLocaleLowerCase("pl")
        .includes(query.trim().toLocaleLowerCase("pl")),
  );
  const toggleTheme = () =>
    settings.setPreferences({
      ...settings.preferences,
      theme: settings.resolvedTheme === "light" ? "dark" : "light",
    });

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
        <nav>
          {sections.map(({ id, title, icon: Icon }) => (
            <a
              key={id}
              href={`#${id}`}
              className={`nav-item ${section === id ? "active" : ""}`}
              aria-current={section === id ? "page" : undefined}
            >
              <Icon size={19} />
              <span>{title}</span>
              {section === id && <span className="nav-indicator" />}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-tip">
            <span className="tip-icon">
              <SlidersHorizontal size={19} />
            </span>
            <strong>Dashboard po Twojemu</strong>
            <p>Wybierz wygląd, ułóż moduły i zrób miejsce na to, co ważne.</p>
            <button onClick={() => setAppearanceOpen(true)}>
              Dopasuj widok <ArrowUpRight size={16} />
            </button>
          </div>
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
          </div>
          <div className="topbar-actions">
            <span className="preview-badge">
              <i />
              Podgląd interfejsu
            </span>
            <button
              className="icon-button theme-toggle"
              onClick={toggleTheme}
              aria-label={
                settings.resolvedTheme === "light"
                  ? "Włącz ciemny motyw"
                  : "Włącz jasny motyw"
              }
            >
              {settings.resolvedTheme === "light" ? (
                <Moon size={18} />
              ) : (
                <Sun size={18} />
              )}
            </button>
            <span className="topbar-divider" />
            <span className="topbar-avatar" aria-label="Przestrzeń zespołu">
              FF
            </span>
          </div>
        </header>
        <main id="main-content" className="main-content" tabIndex={-1}>
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
            <button
              className="button button-primary"
              onClick={() => setAppearanceOpen(true)}
            >
              <SlidersHorizontal size={17} />
              Dopasuj widok
            </button>
          </div>
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
                  onClick={() => setAppearanceOpen(true)}
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
                        [section]: {
                          desktop: defaultLayout(section, "desktop"),
                          compact: defaultLayout(section, "compact"),
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
            section={section}
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
                onClick={() => setAppearanceOpen(true)}
              >
                Wybierz moduły
              </button>
            </div>
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
      <AppearancePanel
        open={appearanceOpen}
        onClose={() => setAppearanceOpen(false)}
        preferences={effective}
        persistent={settings.persistent}
        editing={Boolean(draft)}
        backgroundMedia={backgroundMedia}
        onBackgroundChange={(background) =>
          settings.setPreferences((previous) => ({ ...previous, background }))
        }
        onEdit={startEditing}
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
