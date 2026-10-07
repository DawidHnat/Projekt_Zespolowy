import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { alertsQuery, summaryQuery, vehiclesQuery } from '../../shared/api/queries'
import { SummaryCards } from '../../shared/components/SummaryCards'
import { SourceBadge } from '../../shared/components/SourceBadge'
import { EmptyState, ErrorState, LoadingState } from '../../shared/components/Feedback'
import { Icon } from '../../shared/components/Icon'
import { formatNumber } from '../../shared/lib/format'

export default function AnalyticsPage() {
  const summary = useQuery(summaryQuery)
  const alerts = useQuery(alertsQuery)
  const vehicles = useQuery(vehiclesQuery())
  const movingShare = summary.data?.total_vehicles
    ? (summary.data.driving_vehicles / summary.data.total_vehicles) * 100
    : 0
  const refresh = () => {
    void summary.refetch()
    void alerts.refetch()
    void vehicles.refetch()
  }

  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <span className="eyebrow">DANE, KTÓRE POMAGAJĄ DECYDOWAĆ</span>
          <h1>
            Analityka i alerty<span className="heading-dot">.</span>
          </h1>
          <p>Najważniejsze liczby i zdarzenia w Twojej flocie.</p>
        </div>
        <button
          className="button button-secondary"
          disabled={summary.isFetching || alerts.isFetching}
          onClick={refresh}
        >
          <Icon name="refresh" />
          Odśwież
        </button>
      </div>
      <SummaryCards />
      <div className="analytics-grid">
        <section className="panel utilization-panel">
          <div className="panel-header">
            <div>
              <h2>Aktywność floty</h2>
              <p>Według ostatniego statusu pojazdów</p>
            </div>
            <Icon name="analytics" />
          </div>
          {summary.isPending ? (
            <LoadingState />
          ) : summary.isError ? (
            <ErrorState error={summary.error} onRetry={() => void summary.refetch()} />
          ) : (
            <div className="utilization-content">
              <div className="activity-value">
                {formatNumber(movingShare)}
                <span>%</span>
              </div>
              <p>pojazdów ma status „W ruchu”</p>
              <div
                className="activity-bar"
                aria-label={`${formatNumber(movingShare)}% pojazdów w ruchu`}
              >
                <span style={{ width: `${Math.min(100, movingShare)}%` }} />
              </div>
              <div className="activity-legend">
                <span>
                  <i />W ruchu <strong>{summary.data.driving_vehicles}</strong>
                </span>
                <span>
                  <i />
                  Pozostałe{' '}
                  <strong>
                    {Math.max(0, summary.data.total_vehicles - summary.data.driving_vehicles)}
                  </strong>
                </span>
              </div>
              <div className="analysis-note">
                <Icon name="location" size={18} />
                <span>
                  Udział pojazdów w ruchu opisuje ostatnie znane statusy. Nie jest wskaźnikiem
                  wykorzystania w czasie.
                </span>
              </div>
            </div>
          )}
        </section>
        <section className="panel alerts-panel">
          <div className="panel-header">
            <div>
              <h2>
                Alerty <span className="count-badge">{alerts.data?.total ?? '—'}</span>
              </h2>
              <p>Zdarzenia wymagające Twojej uwagi</p>
            </div>
            <SourceBadge source={alerts.data?.source} />
          </div>
          {alerts.isPending ? (
            <LoadingState />
          ) : alerts.isError ? (
            <ErrorState error={alerts.error} onRetry={() => void alerts.refetch()} />
          ) : alerts.data.items.length === 0 ? (
            <EmptyState
              title="Brak alertów"
              description="W bieżących danych nie znaleziono alertów."
            />
          ) : (
            <div className="alert-list">
              {alerts.data.items.map((alert) => (
                <article className={`alert-item alert-${alert.severity}`} key={alert.id}>
                  <span className="alert-icon">
                    <Icon name={alert.severity === 'warning' ? 'alert' : 'location'} size={19} />
                  </span>
                  <div>
                    <div className="alert-title">
                      <h3>{alert.title}</h3>
                      <span>{alert.severity === 'warning' ? 'Uwaga' : 'Informacja'}</span>
                    </div>
                    <p>{alert.description}</p>
                    <Link to={`/history?vehicle=${encodeURIComponent(alert.vehicle_id)}`}>
                      {vehicles.data?.items.find((v) => v.id === alert.vehicle_id)?.registration ??
                        'Historia pojazdu'}
                      <Icon name="arrow" size={14} />
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
