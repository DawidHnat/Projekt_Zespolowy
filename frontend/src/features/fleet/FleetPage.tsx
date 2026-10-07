import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { vehiclesQuery } from '../../shared/api/queries'
import { formatDate, formatNumber } from '../../shared/lib/format'
import { useDebouncedValue } from '../../shared/lib/useDebouncedValue'
import { SummaryCards } from '../../shared/components/SummaryCards'
import { StatusBadge } from '../../shared/components/StatusBadge'
import { SourceBadge } from '../../shared/components/SourceBadge'
import { EmptyState, ErrorState, LoadingState } from '../../shared/components/Feedback'
import { Icon } from '../../shared/components/Icon'
import { FleetMap } from './FleetMap'

export default function FleetPage() {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [selectedId, setSelectedId] = useState<string>()
  const query = useDebouncedValue(search)
  const queryClient = useQueryClient()
  const vehicles = useQuery(vehiclesQuery(query, status))
  const selected = vehicles.data?.items.find((vehicle) => vehicle.id === selectedId)
  const refresh = () => {
    void vehicles.refetch()
    void queryClient.invalidateQueries({ queryKey: ['analytics', 'summary'] })
  }

  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <span className="eyebrow">TWOJA FLOTA, JEDEN WIDOK</span>
          <h1>
            Flota i mapa<span className="heading-dot">.</span>
          </h1>
          <p>Sprawdź, gdzie są Twoje pojazdy i co się z nimi dzieje.</p>
        </div>
        <button
          className="button button-secondary"
          disabled={vehicles.isFetching}
          onClick={refresh}
        >
          <Icon name="refresh" />
          Odśwież
        </button>
      </div>
      <SummaryCards />
      <div className="fleet-workspace">
        <section className="panel fleet-panel">
          <div className="panel-header">
            <div className="panel-title-line">
              <h2>Pojazdy</h2>
              <span className="count-badge">{vehicles.data?.total ?? '—'}</span>
            </div>
            <SourceBadge source={vehicles.data?.source} />
          </div>
          <div className="fleet-filters">
            <label className="search-field">
              <Icon name="search" />
              <input
                type="search"
                placeholder="Szukaj pojazdu lub rejestracji"
                aria-label="Szukaj pojazdu lub rejestracji"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </label>
            <select
              aria-label="Status pojazdu"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">Wszystkie statusy</option>
              <option value="driving">W ruchu</option>
              <option value="parked">Postój</option>
              <option value="offline">Offline</option>
              <option value="unknown">Brak statusu</option>
            </select>
          </div>
          {vehicles.isPending ? (
            <LoadingState />
          ) : vehicles.isError ? (
            <ErrorState error={vehicles.error} onRetry={() => void vehicles.refetch()} />
          ) : vehicles.data.items.length === 0 ? (
            <EmptyState
              title="Brak pojazdów"
              description={
                search || status
                  ? 'Zmień wyszukiwanie lub wybrany status.'
                  : 'Brak pojazdów w bieżącym źródle danych.'
              }
            />
          ) : (
            <div className="table-scroll">
              <table className="fleet-table">
                <thead>
                  <tr>
                    <th>Pojazd</th>
                    <th>Status</th>
                    <th>Prędkość</th>
                    <th aria-label="Wybierz pojazd" />
                  </tr>
                </thead>
                <tbody>
                  {vehicles.data.items.map((vehicle) => (
                    <tr
                      key={vehicle.id}
                      className={selectedId === vehicle.id ? 'selected-row' : ''}
                    >
                      <td>
                        <button
                          className="vehicle-button"
                          onClick={() => setSelectedId(vehicle.id)}
                          aria-pressed={selectedId === vehicle.id}
                        >
                          <span className={`vehicle-icon vehicle-${vehicle.status}`}>
                            <Icon name="fleet" />
                          </span>
                          <span>
                            <strong>{vehicle.registration}</strong>
                            <small>{vehicle.name}</small>
                          </span>
                        </button>
                      </td>
                      <td>
                        <StatusBadge status={vehicle.status} />
                      </td>
                      <td className="table-number">
                        {formatNumber(vehicle.speed_kmh)}
                        <span> km/h</span>
                      </td>
                      <td>
                        <button
                          className="icon-button"
                          aria-label={`Szczegóły ${vehicle.registration}`}
                          onClick={() => setSelectedId(vehicle.id)}
                        >
                          <Icon name="chevron" size={17} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="table-footer">
            <span>
              {vehicles.isFetching && !vehicles.isPending
                ? 'Aktualizowanie…'
                : 'Pozycje według ostatniej aktualizacji źródła'}
            </span>
            <span>{vehicles.data?.total != null ? `Łącznie: ${vehicles.data.total}` : ''}</span>
          </div>
        </section>
        <FleetMap
          vehicles={vehicles.data?.items ?? []}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />
      </div>
      {selected && (
        <section
          className="panel vehicle-detail"
          aria-label={`Dane pojazdu ${selected.registration}`}
        >
          <div className="vehicle-detail-title">
            <span className="vehicle-icon">
              <Icon name="fleet" size={24} />
            </span>
            <div>
              <h2>{selected.registration}</h2>
              <p>{selected.name}</p>
            </div>
            <StatusBadge status={selected.status} />
          </div>
          <dl>
            <div>
              <dt>Przebieg</dt>
              <dd>{formatNumber(selected.odometer_km)} km</dd>
            </div>
            <div>
              <dt>Ostatnia aktualizacja</dt>
              <dd>{formatDate(selected.updated_at)}</dd>
            </div>
            <div>
              <dt>Pozycja GPS</dt>
              <dd>
                {selected.latitude != null && selected.longitude != null
                  ? `${selected.latitude.toFixed(4)}, ${selected.longitude.toFixed(4)}`
                  : 'Brak pozycji'}
              </dd>
            </div>
          </dl>
          <Link
            className="button button-primary"
            to={`/history?vehicle=${encodeURIComponent(selected.id)}`}
          >
            Historia pojazdu
            <Icon name="arrow" size={17} />
          </Link>
        </section>
      )}
    </div>
  )
}
