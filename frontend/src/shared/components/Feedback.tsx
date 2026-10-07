import { Icon } from './Icon'

export function LoadingState({ label = 'Wczytywanie danych…' }: { label?: string }) {
  return (
    <div className="feedback-state" role="status">
      <span className="spinner" />
      {label}
    </div>
  )
}

export function ErrorState({ error, onRetry }: { error: Error | null; onRetry?: () => void }) {
  return (
    <div className="feedback-state error-state" role="alert">
      <Icon name="alert" size={28} />
      <strong>Nie udało się wczytać danych</strong>
      <p>{error?.message ?? 'Spróbuj ponownie za chwilę.'}</p>
      {onRetry && (
        <button className="button button-secondary" onClick={onRetry}>
          Spróbuj ponownie
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="feedback-state">
      <span className="empty-icon">
        <Icon name="fleet" size={28} />
      </span>
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  )
}
