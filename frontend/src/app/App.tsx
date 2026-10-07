import { lazy, Suspense } from 'react'
import { Navigate, NavLink, Outlet, Route, Routes } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { summaryQuery } from '../shared/api/queries'
import { Icon } from '../shared/components/Icon'
import { SourceBadge } from '../shared/components/SourceBadge'
import { LoadingState } from '../shared/components/Feedback'

const FleetPage = lazy(() => import('../features/fleet/FleetPage'))
const HistoryPage = lazy(() => import('../features/trips/HistoryPage'))
const AnalyticsPage = lazy(() => import('../features/analytics/AnalyticsPage'))

function AppLayout() {
  const { data } = useQuery(summaryQuery)
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Przejdź do treści
      </a>
      <aside className="sidebar">
        <NavLink className="brand" to="/fleet" aria-label="Fleet-Flow — strona główna">
          <span className="brand-mark">
            F<span />
          </span>
          <span>
            Fleet<span className="brand-light">Flow</span>
            <small>PRZESTRZEŃ TWOJEJ FLOTY</small>
          </span>
        </NavLink>
        <div className="workspace-label">PRZEGLĄD</div>
        <nav aria-label="Nawigacja główna">
          <NavLink to="/fleet" aria-label="Flota i mapa">
            <Icon name="fleet" />
            <span>Flota i mapa</span>
            <Icon name="chevron" size={15} />
          </NavLink>
          <NavLink to="/history" aria-label="Historia przejazdów">
            <Icon name="history" />
            <span>Historia przejazdów</span>
            <Icon name="chevron" size={15} />
          </NavLink>
          <NavLink to="/analytics" aria-label="Analityka i alerty">
            <Icon name="analytics" />
            <span>Analityka i alerty</span>
            <Icon name="chevron" size={15} />
          </NavLink>
        </nav>
        <div className="sidebar-footer">
          <span className="sidebar-footer-icon">
            <Icon name="fleet" size={22} />
          </span>
          <strong>Wszystko w jednym miejscu</strong>
          <p>Twój codzienny widok na flotę.</p>
          <span className="version-label">Fleet-Flow · MVP</span>
        </div>
      </aside>
      <div className="app-body">
        <header className="topbar">
          <span className="topbar-title">
            Przestrzeń zespołu <span className="topbar-divider">/</span> Zarządzanie flotą
          </span>
          <div className="topbar-actions">
            <SourceBadge source={data?.source} />
            <span className="avatar" title="Kierownik floty" aria-label="Kierownik floty">
              KF
            </span>
          </div>
        </header>
        <main id="main-content">
          <Suspense fallback={<LoadingState label="Wczytywanie widoku…" />}>
            <Outlet />
          </Suspense>
        </main>
        <footer className="page-footer">
          <span>Fleet-Flow</span>
          <span>Czytelny widok. Sprawne zarządzanie.</span>
        </footer>
      </div>
    </div>
  )
}

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/fleet" replace />} />
        <Route path="fleet" element={<FleetPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route
          path="*"
          element={
            <div className="feedback-state">
              <h1>Nie znaleziono strony</h1>
              <NavLink className="button button-primary" to="/fleet">
                Wróć do floty
              </NavLink>
            </div>
          }
        />
      </Route>
    </Routes>
  )
}
