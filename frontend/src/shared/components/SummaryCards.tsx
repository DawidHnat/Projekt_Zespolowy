import { useQuery } from '@tanstack/react-query'
import { summaryQuery } from '../api/queries'
import { formatNumber } from '../lib/format'
import { Icon, type IconName } from './Icon'

export function SummaryCards() {
  const { data, isPending, isError } = useQuery(summaryQuery)
  const cards: {
    label: string
    value: number | undefined
    unit?: string
    icon: IconName
    note: string
  }[] = [
    {
      label: 'Pojazdy we flocie',
      value: data?.total_vehicles,
      icon: 'fleet',
      note: 'Wszystkie pojazdy',
    },
    {
      label: 'Pojazdy w ruchu',
      value: data?.driving_vehicles,
      icon: 'location',
      note: 'Według ostatniej pozycji',
    },
    {
      label: 'Przejechany dystans',
      value: data?.distance_km,
      unit: 'km',
      icon: 'distance',
      note: 'W dostępnej historii',
    },
    {
      label: 'Liczba przejazdów',
      value: data?.trips_count,
      icon: 'history',
      note: 'W dostępnej historii',
    },
  ]
  return (
    <div className="summary-grid" aria-label="Podsumowanie floty">
      {cards.map((card) => (
        <div className="summary-card" key={card.label}>
          <div className="summary-top">
            <span>{card.label}</span>
            <span className="summary-icon">
              <Icon name={card.icon} />
            </span>
          </div>
          <div className="summary-value">
            {isPending ? <span className="skeleton skeleton-value" /> : formatNumber(card.value)}
            {card.unit && <span>{card.unit}</span>}
          </div>
          <p>{isError ? 'Dane niedostępne' : card.note}</p>
        </div>
      ))}
    </div>
  )
}
