import mapboxgl from "mapbox-gl";
import type { FleetFeature } from "../model/types";
import { statusLabels } from "../model/types";
import { vehiclesAtPoint } from "../model/marker-model";

export const VEHICLE_FALLBACK = `${import.meta.env.BASE_URL}brand/vehicle-fallback.svg`;

// Reconcile by stable vehicle ID; refreshes do not recreate markers or move the camera.
export class VehicleMarkers {
  private entries = new Map<
    string,
    {
      marker: mapboxgl.Marker;
      button: HTMLButtonElement;
      image: HTMLImageElement;
      label: HTMLSpanElement;
    }
  >();
  private features: FleetFeature[] = [];
  private editing = false;
  constructor(
    private map: mapboxgl.Map,
    private choose: (ids: string[]) => void,
  ) {}
  update(
    features: FleetFeature[],
    photos: Record<string, string>,
    selected: string | null,
    editing: boolean,
  ) {
    this.features = features;
    this.editing = editing;
    const ids = new Set(features.map((f) => f.properties.id));
    for (const [id, entry] of this.entries)
      if (!ids.has(id)) {
        entry.marker.remove();
        this.entries.delete(id);
      }
    for (const feature of features) {
      const { id, name, status } = feature.properties;
      let entry = this.entries.get(id);
      if (!entry) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "fleet-map-marker";
        const image = document.createElement("img");
        image.alt = "";
        image.draggable = false;
        image.onerror = () => {
          if (image.getAttribute("src") !== VEHICLE_FALLBACK) {
            image.src = VEHICLE_FALLBACK;
            button.classList.remove("has-photo");
          }
        };
        const label = document.createElement("span");
        label.className = "fleet-marker-label";
        const statusDot = document.createElement("span");
        statusDot.className = "fleet-marker-status";
        statusDot.setAttribute("aria-hidden", "true");
        button.append(image, statusDot, label);
        button.onclick = (e) => {
          e.stopPropagation();
          if (this.editing) return;
          const current = this.features.find((f) => f.properties.id === id);
          if (!current) return;
          const point = this.map.project(current.geometry.coordinates);
          const nearby = vehiclesAtPoint(
            this.features.map((f) => ({
              id: f.properties.id,
              ...this.map.project(f.geometry.coordinates),
            })),
            point,
          );
          this.choose(e.detail === 0 ? [id] : nearby);
        };
        entry = {
          marker: new mapboxgl.Marker({ element: button, anchor: "center" })
            .setLngLat(feature.geometry.coordinates)
            .addTo(this.map),
          button,
          image,
          label,
        };
        // Mapbox assigns role="img" to custom elements; retain native interaction semantics.
        button.setAttribute("role", "button");
        this.entries.set(id, entry);
      }
      entry.marker.setLngLat(feature.geometry.coordinates);
      entry.button.classList.remove(
        "marker-moving",
        "marker-stopped",
        "marker-offline",
        "marker-unknown",
      );
      entry.button.classList.add(`marker-${status}`);
      entry.button.classList.toggle("has-photo", Boolean(photos[id]));
      entry.button.classList.toggle("selected", selected === id);
      entry.button.style.zIndex = selected === id ? "2" : "1";
      entry.button.setAttribute(
        "aria-label",
        `Pojazd ${name} · ${statusLabels[status]}`,
      );
      entry.button.setAttribute("aria-pressed", String(selected === id));
      entry.button.disabled = editing;
      entry.label.textContent = name;
      const src = photos[id] || VEHICLE_FALLBACK;
      if (entry.image.getAttribute("src") !== src) entry.image.src = src;
    }
  }
  remove() {
    for (const entry of this.entries.values()) entry.marker.remove();
    this.entries.clear();
  }
}
