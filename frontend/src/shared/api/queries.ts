import { queryOptions } from '@tanstack/react-query'
import { request } from './client'
import type { AlertList, Summary, TripList, Vehicle, VehicleList } from './types'

export const vehiclesQuery = (query = '', status = '') =>
  queryOptions({
    queryKey: ['vehicles', { query, status }],
    queryFn: ({ signal }) => {
      const params = new URLSearchParams()
      if (query) params.set('query', query)
      if (status) params.set('status', status)
      return request<VehicleList>(`/vehicles${params.size ? `?${params}` : ''}`, { signal })
    },
  })

export const vehicleQuery = (id: string) =>
  queryOptions({
    queryKey: ['vehicle', id],
    queryFn: ({ signal }) => request<Vehicle>(`/vehicles/${encodeURIComponent(id)}`, { signal }),
    enabled: !!id,
  })

export const tripsQuery = (vehicleId: string) =>
  queryOptions({
    queryKey: ['trips', vehicleId],
    queryFn: ({ signal }) =>
      request<TripList>(`/vehicles/${encodeURIComponent(vehicleId)}/trips`, { signal }),
    enabled: !!vehicleId,
  })

export const summaryQuery = queryOptions({
  queryKey: ['analytics', 'summary'],
  queryFn: ({ signal }) => request<Summary>('/analytics/summary', { signal }),
})

export const alertsQuery = queryOptions({
  queryKey: ['analytics', 'alerts'],
  queryFn: ({ signal }) => request<AlertList>('/analytics/alerts', { signal }),
})
