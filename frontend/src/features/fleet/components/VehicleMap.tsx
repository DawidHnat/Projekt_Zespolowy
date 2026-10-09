import { useContext, useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { MapPin, Scan, X } from "lucide-react";
import { useFleet } from "../model/FleetProvider";
import { boundsForFeatures, validFeatures } from "../model/map-model";
import { positionTime, statusLabels } from "../model/types";
import { LayoutEditingContext } from "../../../shared/components/LayoutEditingContext";
import { EmptyState } from "../../../shared/components/EmptyState";
import { VehicleMarkers } from "./vehicle-markers";
import { useVehiclePreferences } from "../model/VehiclePreferences";

const token = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;
const style = () =>
  document.documentElement.dataset.theme === "dark"
    ? "mapbox://styles/mapbox/dark-v11"
    : "mapbox://styles/mapbox/streets-v12";
export default function VehicleMap() {
  const fleet = useFleet();
  const preferences = useVehiclePreferences();
  const editing = useContext(LayoutEditingContext);
  const container = useRef<HTMLDivElement>(null);
  const instance = useRef<mapboxgl.Map | null>(null);
  const markers = useRef<VehicleMarkers | null>(null);
  const latest = useRef(fleet);
  latest.current = fleet;
  const editRef = useRef(editing);
  editRef.current = editing;
  const [failure, setFailure] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [overlap, setOverlap] = useState<string[]>([]);
  const fitted = useRef(false);
  const features = validFeatures(fleet.map);
  useEffect(() => {
    fitted.current = false;
  }, [fleet.q, fleet.status]);
  useEffect(() => {
    if (!token?.startsWith("pk.") || !container.current) return;
    setReady(false);
    setFailure(null);
    if (!mapboxgl.supported()) {
      setFailure(
        "Ta przeglądarka nie obsługuje mapy. Lista pojazdów nadal działa.",
      );
      return;
    }
    let map: mapboxgl.Map;
    try {
      map = new mapboxgl.Map({
        container: container.current,
        accessToken: token,
        style: style(),
        center: [19, 52],
        zoom: 5,
        attributionControl: true,
      });
    } catch {
      setFailure("Nie można uruchomić mapy w tej przeglądarce.");
      return;
    }
    instance.current = map;
    markers.current = new VehicleMarkers(map, (ids) => {
      if (ids.length === 1) {
        latest.current.select(ids[0]);
        setOverlap([]);
      } else setOverlap(ids);
    });
    fitted.current = false;
    let frame = 0;
    map.addControl(
      new mapboxgl.NavigationControl({ showCompass: false }),
      "top-right",
    );
    const install = () => {
      const bounds = boundsForFeatures(validFeatures(latest.current.map));
      if (bounds && !fitted.current) {
        map.fitBounds(bounds, { padding: 50, maxZoom: 12, duration: 0 });
        fitted.current = true;
      }
      setReady(true);
    };
    map.on("style.load", install);
    map.on("error", () =>
      setFailure(
        "Nie udało się załadować mapy. Lista pojazdów pozostaje dostępna.",
      ),
    );
    map.on("click", () => {
      if (!editRef.current) setOverlap([]);
    });
    const observer = new ResizeObserver(() => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => map.resize());
    });
    observer.observe(container.current);
    const themes = new MutationObserver(() => {
      setReady(false);
      map.setStyle(style());
    });
    themes.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => {
      observer.disconnect();
      themes.disconnect();
      cancelAnimationFrame(frame);
      markers.current?.remove();
      markers.current = null;
      map.remove();
      instance.current = null;
    };
  }, []);
  useEffect(() => {
    const map = instance.current;
    if (!map || !ready) return;
    markers.current?.update(
      features,
      preferences.photos,
      fleet.selectedId,
      editing,
    );
    const bounds = boundsForFeatures(features);
    if (bounds && !fitted.current) {
      map.fitBounds(bounds, { padding: 50, maxZoom: 12, duration: 0 });
      fitted.current = true;
    }
  }, [fleet.map, fleet.selectedId, ready, preferences.photos, editing]);
  useEffect(() => {
    setOverlap([]);
  }, [fleet.q, fleet.status, editing]);
  useEffect(() => {
    const v = fleet.selected;
    const map = instance.current;
    if (!v || !map || !ready || v.latitude === null || v.longitude === null)
      return;
    map.easeTo({
      center: [v.longitude, v.latitude],
      zoom: Math.max(map.getZoom(), 12),
      duration: matchMedia("(prefers-reduced-motion: reduce)").matches
        ? 0
        : 450,
    });
  }, [
    fleet.selected?.id,
    fleet.selected?.latitude,
    fleet.selected?.longitude,
    ready,
  ]);
  useEffect(() => {
    const map = instance.current;
    if (!map) return;
    for (const handler of [
      map.dragPan,
      map.scrollZoom,
      map.boxZoom,
      map.dragRotate,
      map.keyboard,
      map.doubleClickZoom,
      map.touchZoomRotate,
    ]) {
      if (editing) handler.disable();
      else handler.enable();
    }
  }, [editing, ready]);
  if (!token?.startsWith("pk."))
    return (
      <div className="map-canvas">
        <EmptyState
          icon={MapPin}
          title="Mapa czeka na konfigurację"
          description="Administrator musi skonfigurować dostęp do mapy. Lista pojazdów jest dostępna."
        />
      </div>
    );
  return (
    <div className="map-canvas live-map" aria-label="Mapa pozycji floty">
      <div className="mapbox-container" ref={container} />
      {failure && (
        <div className="map-fallback" role="alert">
          <EmptyState
            icon={MapPin}
            title="Mapa chwilowo niedostępna"
            description={failure}
          />
        </div>
      )}
      {!failure && !features.length && ready && (
        <div className="map-zero" role="status">
          Brak pozycji GPS dla wybranych filtrów.
        </div>
      )}
      <span className="map-note">
        {editing
          ? "Chwyć mapę, aby przesunąć kafelek"
          : `${features.length} pozycji · ${fleet.map?.total ?? 0} pojazdów`}
      </span>
      <button
        className="map-fit button button-secondary"
        aria-label="Pokaż całą flotę na mapie"
        disabled={editing || !ready || !features.length}
        onClick={() => {
          const bounds = boundsForFeatures(features);
          if (bounds)
            instance.current?.fitBounds(bounds, {
              padding: 50,
              maxZoom: 12,
              duration: matchMedia("(prefers-reduced-motion: reduce)").matches
                ? 0
                : 400,
            });
        }}
      >
        <Scan size={15} />
        <span>Cała flota</span>
      </button>
      {fleet.selected && (
        <aside className="map-selection">
          <strong>{fleet.selected.name}</strong>
          <span>
            {statusLabels[fleet.selected.status]} ·{" "}
            {positionTime(fleet.selected.position_at)}
          </span>
          {fleet.selected.latitude === null && (
            <small>Ten pojazd nie ma poprawnej pozycji GPS.</small>
          )}
        </aside>
      )}
      {!!overlap.length && !editing && (
        <aside className="map-overlap" aria-label="Pojazdy w tym miejscu">
          <header>
            <strong>Wybierz pojazd</strong>
            <button
              className="icon-button"
              aria-label="Zamknij wybór pojazdu"
              onClick={() => setOverlap([])}
            >
              <X size={16} />
            </button>
          </header>
          <small>Znaczniki są blisko siebie.</small>
          <div>
            {features
              .filter((f) => overlap.includes(f.properties.id))
              .map((f) => (
                <button
                  key={f.properties.id}
                  onClick={() => {
                    fleet.select(f.properties.id);
                    setOverlap([]);
                  }}
                >
                  <strong>{f.properties.name}</strong>
                  <span>{statusLabels[f.properties.status]}</span>
                </button>
              ))}
          </div>
        </aside>
      )}
    </div>
  );
}
