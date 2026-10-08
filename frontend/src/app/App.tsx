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
} from "lucide-react";
import { useDashboardPreferences } from "./preferences";
import { AppearancePanel } from "../features/dashboard/components/AppearancePanel";
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

function Brand() {
  return (
    <a className="brand" href="#dashboard" aria-label="Fleet-Flow — dashboard">
      <span className="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 32 32">
          <path
            d="M7 12h10l5-5h5l-9 9H8m-2 5h10l5-5h5l-9 9H7"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span>
        Fleet<span className="brand-dash">-</span>Flow
        <small>PRZESTRZEŃ ZESPOŁU</small>
      </span>
    </a>
  );
}

export function App() {
  const settings = useDashboardPreferences();
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
      settings.preferences.visibleWidgets.includes(id) &&
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
    <div className="app-shell">
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
            <p>Wybierz kolory i moduły, które są dla Ciebie ważne.</p>
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
          <div className="dashboard-grid">
            {visible.map((id) => {
              const Component = widgetRegistry[id].component;
              return (
                <div className={`widget-slot widget-slot-${id}`} key={id}>
                  <Component onHide={() => settings.toggleWidget(id)} />
                </div>
              );
            })}
          </div>
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
        preferences={settings.preferences}
        persistent={settings.persistent}
        onChange={settings.setPreferences}
        onToggle={settings.toggleWidget}
        onReset={settings.reset}
      />
    </div>
  );
}
