import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { request } from '../../shared/api/client'
import type { Trip, TripUpdate } from '../../shared/api/types'
import { formatDate, formatNumber } from '../../shared/lib/format'
import { Icon } from '../../shared/components/Icon'

export function TripEditor({ trip }: { trip: Trip }) {
  const [editing, setEditing] = useState(false)
  const [saved, setSaved] = useState(false)
  const [purpose, setPurpose] = useState(trip.purpose)
  const [notes, setNotes] = useState(trip.notes)
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn: (update: TripUpdate) =>
      request<Trip>(`/trips/${encodeURIComponent(trip.id)}`, {
        method: 'PATCH',
        body: JSON.stringify(update),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['trips', trip.vehicle_id] })
      setEditing(false)
      setSaved(true)
    },
  })

  return (
    <article className="trip-card">
      <div className="trip-summary">
        <div className="trip-route-mark">
          <span />
          <i />
          <span />
        </div>
        <div className="trip-route">
          <div>
            <strong>{trip.start_address || 'Nieznane miejsce rozpoczęcia'}</strong>
            <time dateTime={trip.started_at}>{formatDate(trip.started_at)}</time>
          </div>
          <div>
            <strong>{trip.end_address || 'Nieznane miejsce zakończenia'}</strong>
            <time dateTime={trip.ended_at ?? undefined}>{formatDate(trip.ended_at)}</time>
          </div>
        </div>
        <div className="trip-distance">
          <strong>{formatNumber(trip.distance_km)}</strong>
          <span>km</span>
        </div>
        <button
          className="button button-secondary button-small"
          disabled={mutation.isPending}
          onClick={() => {
            setPurpose(trip.purpose)
            setNotes(trip.notes)
            setEditing(!editing)
            setSaved(false)
            mutation.reset()
          }}
        >
          <Icon name="edit" size={16} />
          {editing ? 'Zamknij' : trip.purpose ? 'Edytuj' : 'Uzupełnij cel'}
        </button>
      </div>
      {editing ? (
        <form
          className="trip-edit-form"
          onSubmit={(e) => {
            e.preventDefault()
            mutation.mutate({ purpose: purpose.trim(), notes: notes.trim() })
          }}
        >
          <label>
            Cel przejazdu
            <input
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              placeholder="np. Dostawa do klienta"
              maxLength={200}
            />
          </label>
          <label>
            Dodatkowy opis
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Dodaj informacje przydatne w ewidencji"
              rows={3}
              maxLength={2000}
            />
          </label>
          <div className="form-actions">
            <span>
              {mutation.isError && (
                <span className="form-error" role="alert">
                  {mutation.error.message}
                </span>
              )}
            </span>
            <button className="button button-primary" type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Zapisywanie…' : 'Zapisz zmiany'}
              <Icon name="check" size={16} />
            </button>
          </div>
        </form>
      ) : (
        <div className="trip-notes">
          <div>
            <span>CEL PRZEJAZDU</span>
            <p>{trip.purpose || <span className="missing-text">Nie uzupełniono</span>}</p>
          </div>
          <div>
            <span>OPIS</span>
            <p>{trip.notes || '—'}</p>
          </div>
          {saved && (
            <span className="save-message" role="status">
              <Icon name="check" size={15} />
              Zapisano zmiany
            </span>
          )}
        </div>
      )}
    </article>
  )
}
