import type { DataSource } from '../api/types'

export function SourceBadge({ source }: { source?: DataSource }) {
  if (!source) return null
  return (
    <span className={`source-badge source-${source}`}>
      <span className="status-dot" />
      {source === 'demo' ? 'Dane demonstracyjne' : 'WEBFLEET'}
    </span>
  )
}
