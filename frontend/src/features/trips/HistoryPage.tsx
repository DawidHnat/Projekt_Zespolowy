import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { tripsQuery, vehiclesQuery } from '../../shared/api/queries'
import { EmptyState, ErrorState, LoadingState } from '../../shared/components/Feedback'
import { SourceBadge } from '../../shared/components/SourceBadge'
import { StatusBadge } from '../../shared/components/StatusBadge'
import { Icon } from '../../shared/components/Icon'
import { formatNumber } from '../../shared/lib/format'
import { TripEditor } from './TripEditor'

export default function HistoryPage() {
  const [params, setParams] = useSearchParams()
  const vehicles = useQuery(vehiclesQuery())
  const vehicleId = params.get('vehicle') ?? vehicles.data?.items[0]?.id ?? ''
  const vehicle = vehicles.data?.items.find((item) => item.id === vehicleId)
  const trips = useQuery(tripsQuery(vehicleId))

  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <span className="eyebrow">KAŻDY PRZEJAZD MA SWÓJ CEL</span>
          <h1>
            Historia przejazdów<span className="heading-dot">.</span>
          </h1>
          <p>Przeglądaj trasy i uzupełniaj dane do ewidencji przebiegu.</p>
        </div>
      </div>
      <section className="panel history-vehicle">
        <div className="history-select">
          <label htmlFor="history-vehicle">WYBRANY POJAZD</label>
          <select
            id="history-vehicle"
            value={vehicleId}
            disabled={!vehicles.data?.items.length}
            onChange={(e) => setParams({ vehicle: e.target.value })}
          >
            {!vehicles.data?.items.length && <option value="">Wybierz pojazd</option>}
            {vehicles.data?.items.map((item) => (
              <option key={item.id} value={item.id}>
                {item.registration} · {item.name}
              </option>
            ))}
          </select>
        </div>
        {vehicle && (
          <>
            <StatusBadge status={vehicle.status} />
            <div className="history-mileage">
              <span>Przebieg pojazdu</span>
              <strong>
                {formatNumber(vehicle.odometer_km)} <small>km</small>
              </strong>
            </div>
          </>
        )}
        {vehicleId && (
          <button
            className="button button-secondary"
            disabled={trips.isFetching}
            onClick={() => void trips.refetch()}
          >
            <Icon name="refresh" size={18} />
            Odśwież
          </button>
        )}
      </section>
      {vehicles.isPending ? (
        <LoadingState />
      ) : vehicles.isError ? (
        <ErrorState error={vehicles.error} onRetry={() => void vehicles.refetch()} />
      ) : !vehicleId ? (
        <section className="panel">
          <EmptyState
            title="Nie ma jeszcze pojazdów"
            description="Historia będzie dostępna po dodaniu pojazdów do źródła danych."
          />
        </section>
      ) : (
        <>
          <div className="section-heading">
            <div>
              <h2>
                Przejazdy <span className="count-badge">{trips.data?.total ?? '—'}</span>
              </h2>
              <p>Dostępna historia wybranego pojazdu</p>
            </div>
            <SourceBadge source={trips.data?.source} />
          </div>
          {trips.isPending ? (
            <section className="panel">
              <LoadingState />
            </section>
          ) : trips.isError ? (
            <section className="panel">
              <ErrorState error={trips.error} onRetry={() => void trips.refetch()} />
            </section>
          ) : trips.data.items.length === 0 ? (
            <section className="panel">
              <EmptyState
                title="Brak przejazdów"
                description="Nie znaleziono historii przejazdów dla tego pojazdu."
              />
            </section>
          ) : (
            <div className="trip-list">
              {trips.data.items.map((trip) => (
                <TripEditor key={trip.id} trip={trip} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
