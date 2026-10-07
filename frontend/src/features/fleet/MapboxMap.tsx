import { useEffect, useRef, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import type { Vehicle } from '../../shared/api/types'
import { Icon } from '../../shared/components/Icon'

function hasCoordinates(
  vehicle: Vehicle,
): vehicle is Vehicle & { latitude: number; longitude: number } {
  return (
    vehicle.latitude != null &&
    vehicle.longitude != null &&
    Number.isFinite(vehicle.latitude) &&
    Math.abs(vehicle.latitude) <= 90 &&
    Number.isFinite(vehicle.longitude) &&
    Math.abs(vehicle.longitude) <= 180
  )
}

export default function MapboxMap({
  vehicles,
  selectedId,
  onSelect,
  token,
}: {
  vehicles: Vehicle[]
  selectedId?: string
  onSelect: (id: string) => void
  token: string
}) {
  const container = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const select = useRef(onSelect)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    select.current = onSelect
  }, [onSelect])

  useEffect(() => {
    if (!container.current) return
    let instance: mapboxgl.Map
    try {
      instance = new mapboxgl.Map({
        container: container.current,
        accessToken: token,
        style: 'mapbox://styles/mapbox/light-v11',
        center: [19.1451, 52.237],
        zoom: 5.2,
        attributionControl: true,
      })
    } catch {
      const timer = window.setTimeout(() => setFailed(true), 0)
      return () => window.clearTimeout(timer)
    }
    map.current = instance
    instance.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'top-right')
    instance.on('error', () => setFailed(true))
    return () => {
      instance.remove()
      map.current = null
    }
  }, [token])

  useEffect(() => {
    const instance = map.current
    if (!instance) return
    const positions = vehicles.filter(hasCoordinates)
    const markers = positions.map((vehicle) => {
      const button = document.createElement('button')
      button.className = `vehicle-marker ${vehicle.id === selectedId ? 'is-selected' : ''}`
      button.textContent = vehicle.registration
      button.title = `${vehicle.name} · ${vehicle.registration}`
      button.setAttribute('aria-label', `Wybierz ${vehicle.registration}`)
      button.addEventListener('click', () => select.current(vehicle.id))
      return new mapboxgl.Marker({ element: button })
        .setLngLat([vehicle.longitude, vehicle.latitude])
        .addTo(instance)
    })
    if (positions.length) {
      const bounds = new mapboxgl.LngLatBounds()
      positions.forEach((v) => bounds.extend([v.longitude, v.latitude]))
      instance.fitBounds(bounds, { padding: 55, maxZoom: 12, duration: 400 })
    }
    return () => markers.forEach((marker) => marker.remove())
  }, [vehicles, selectedId])

  return (
    <div className="map-content">
      <div ref={container} className="map-canvas" />
      {failed && (
        <div className="map-message" role="status">
          <Icon name="alert" />
          Nie udało się wczytać mapy.
        </div>
      )}
      {!vehicles.some(hasCoordinates) && !failed && (
        <div className="map-message" role="status">
          Brak dostępnych pozycji GPS.
        </div>
      )}
    </div>
  )
}
