import { lazy, Suspense } from 'react'
import type { Vehicle } from '../../shared/api/types'
import { Icon } from '../../shared/components/Icon'
import { LoadingState } from '../../shared/components/Feedback'

const MapboxMap = lazy(() => import('./MapboxMap'))

export function FleetMap({
  vehicles,
  selectedId,
  onSelect,
}: {
  vehicles: Vehicle[]
  selectedId?: string
  onSelect: (id: string) => void
}) {
  const token = import.meta.env.VITE_MAPBOX_TOKEN?.trim()
  return (
    <section className="panel map-panel" aria-label="Mapa floty">
      <div className="panel-header">
        <div>
          <h2>Położenie floty</h2>
          <p>Ostatnie dostępne pozycje GPS</p>
        </div>
        <span className="map-label">
          <Icon name="location" size={15} />
          Mapa
        </span>
      </div>
      {token ? (
        <Suspense fallback={<LoadingState label="Wczytywanie mapy…" />}>
          <MapboxMap
            vehicles={vehicles}
            selectedId={selectedId}
            onSelect={onSelect}
            token={token}
          />
        </Suspense>
      ) : (
        <div className="map-unavailable">
          <div className="map-placeholder-icon">
            <Icon name="location" size={36} />
          </div>
          <strong>Widok mapy jest teraz niedostępny</strong>
          <p>Informacje o pojazdach znajdziesz na liście obok.</p>
          <span className="map-placeholder-caption">Lista floty działa niezależnie od mapy</span>
        </div>
      )}
    </section>
  )
}
