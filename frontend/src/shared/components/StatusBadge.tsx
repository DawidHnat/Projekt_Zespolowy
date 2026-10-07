import type { Vehicle } from '../api/types'

const statuses = {
  driving: 'W ruchu',
  parked: 'Postój',
  offline: 'Offline',
  unknown: 'Brak statusu',
}

export function StatusBadge({ status }: { status: Vehicle['status'] }) {
  return (
    <span className={`status-badge status-${status}`}>
      <span className="status-dot" />
      {statuses[status]}
    </span>
  )
}
