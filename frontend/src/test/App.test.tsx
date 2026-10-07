import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { App } from '../app/App'
import type { Trip, Vehicle } from '../shared/api/types'

const vehicles: Vehicle[] = [
  {
    id: 'van-1',
    registration: 'GD 123AB',
    name: 'Dostawczy 01',
    status: 'driving',
    speed_kmh: 55,
    odometer_km: 41000,
    latitude: 54.35,
    longitude: 18.65,
    updated_at: '2026-10-07T10:00:00Z',
  },
  {
    id: 'van-2',
    registration: 'WA 456CD',
    name: 'Dostawczy 02',
    status: 'unknown',
    speed_kmh: null,
    odometer_km: null,
    latitude: null,
    longitude: null,
    updated_at: '2026-10-07T10:00:00Z',
  },
]
const initialTrip: Trip = {
  id: 'trip-1',
  vehicle_id: 'van-1',
  started_at: '2026-10-07T09:00:00Z',
  ended_at: '2026-10-07T10:00:00Z',
  distance_km: 22,
  start_address: 'Gdańsk, biuro',
  end_address: 'Sopot, klient',
  purpose: '',
  notes: '',
}
let trip: Trip
let requests: { url: URL; options?: RequestInit }[]
let failVehicles: boolean

function renderApp(path = '/fleet') {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeAll(async () => {
  await Promise.all([
    import('../features/fleet/FleetPage'),
    import('../features/trips/HistoryPage'),
    import('../features/analytics/AnalyticsPage'),
  ])
}, 30_000)

beforeEach(() => {
  trip = { ...initialTrip }
  requests = []
  failVehicles = false
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, options?: RequestInit) => {
      const url = new URL(input, 'http://localhost')
      requests.push({ url, options })
      if (url.pathname === '/api/v1/vehicles') {
        if (failVehicles) return Response.json({ detail: 'unavailable' }, { status: 503 })
        const query = url.searchParams.get('query')?.toLowerCase() ?? ''
        const status = url.searchParams.get('status')
        const items = vehicles.filter(
          (v) =>
            `${v.name} ${v.registration}`.toLowerCase().includes(query) &&
            (!status || status === v.status),
        )
        return Response.json({ items, total: items.length, source: 'demo' })
      }
      if (url.pathname === '/api/v1/analytics/summary')
        return Response.json({
          total_vehicles: 2,
          driving_vehicles: 1,
          distance_km: 22,
          trips_count: 1,
          source: 'demo',
        })
      if (url.pathname === '/api/v1/analytics/alerts')
        return Response.json({
          items: [
            {
              id: 'a1',
              vehicle_id: 'van-2',
              severity: 'warning',
              title: 'Brak aktualnej pozycji',
              description: 'Sprawdź połączenie pojazdu.',
            },
          ],
          total: 1,
          source: 'demo',
        })
      if (url.pathname === '/api/v1/vehicles/van-1/trips')
        return Response.json({ items: [trip], total: 1, source: 'demo' })
      if (url.pathname === '/api/v1/vehicles/van-2/trips')
        return Response.json({ items: [], total: 0, source: 'demo' })
      if (url.pathname === '/api/v1/trips/trip-1' && options?.method === 'PATCH') {
        trip = { ...trip, ...JSON.parse(options.body as string) }
        return Response.json(trip)
      }
      return Response.json({ detail: 'not found' }, { status: 404 })
    }),
  )
})

describe('Fleet-Flow user flows', () => {
  it('filters the backend fleet list and opens the selected vehicle history', async () => {
    const user = userEvent.setup()
    renderApp()
    expect(await screen.findByText('GD 123AB')).toBeVisible()
    expect(within(screen.getByRole('table')).getByText('Brak statusu')).toBeVisible()
    expect(screen.getAllByText('Dane demonstracyjne').length).toBeGreaterThan(0)
    await user.type(screen.getByRole('searchbox'), 'GD 123')
    await waitFor(() => expect(screen.queryByText('WA 456CD')).not.toBeInTheDocument())
    expect(requests.some(({ url }) => url.searchParams.get('query') === 'GD 123')).toBe(true)
    await user.selectOptions(screen.getByLabelText('Status pojazdu'), 'parked')
    expect(await screen.findByText('Brak pojazdów')).toBeVisible()
    await user.selectOptions(screen.getByLabelText('Status pojazdu'), 'driving')
    await user.click(await screen.findByRole('button', { name: /GD 123AB Dostawczy 01/ }))
    await user.click(screen.getByRole('link', { name: 'Historia pojazdu' }))
    expect(await screen.findByText('Gdańsk, biuro')).toBeVisible()
    expect(screen.getByLabelText('WYBRANY POJAZD')).toHaveValue('van-1')
  })

  it('persists trip purpose and notes through the API, then shows them in the refreshed history', async () => {
    const user = userEvent.setup()
    renderApp('/history?vehicle=van-1')
    await user.click(await screen.findByRole('button', { name: 'Uzupełnij cel' }))
    await user.type(screen.getByLabelText('Cel przejazdu'), 'Spotkanie z klientem')
    await user.type(screen.getByLabelText('Dodatkowy opis'), 'Dostawa dokumentów')
    await user.click(screen.getByRole('button', { name: 'Zapisz zmiany' }))
    expect(await screen.findByText('Zapisano zmiany')).toBeVisible()
    expect(screen.getByText('Spotkanie z klientem')).toBeVisible()
    expect(screen.getByText('Dostawa dokumentów')).toBeVisible()
    const patch = requests.find(({ options }) => options?.method === 'PATCH')
    expect(JSON.parse(patch!.options!.body as string)).toEqual({
      purpose: 'Spotkanie z klientem',
      notes: 'Dostawa dokumentów',
    })
    await user.selectOptions(screen.getByLabelText('WYBRANY POJAZD'), 'van-2')
    expect(await screen.findByText('Brak przejazdów')).toBeVisible()
  })

  it('lets the user recover from a server error without reloading the app', async () => {
    const user = userEvent.setup()
    failVehicles = true
    renderApp()
    const alert = await screen.findByRole('alert')
    expect(within(alert).getByText('Nie udało się wczytać danych')).toBeVisible()
    failVehicles = false
    await user.click(within(alert).getByRole('button', { name: 'Spróbuj ponownie' }))
    expect(await screen.findByText('GD 123AB')).toBeVisible()
  })

  it('shows backend analytics and links an alert to its vehicle history', async () => {
    const user = userEvent.setup()
    renderApp('/analytics')
    expect(await screen.findByText('Brak aktualnej pozycji')).toBeVisible()
    expect(screen.getByLabelText('50% pojazdów w ruchu')).toBeVisible()
    await user.click(await screen.findByRole('link', { name: 'WA 456CD' }))
    expect(await screen.findByText('Brak przejazdów')).toBeVisible()
    expect(screen.getByLabelText('WYBRANY POJAZD')).toHaveValue('van-2')
  })
})
