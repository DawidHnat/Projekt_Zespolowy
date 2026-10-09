import { useContext, useEffect, useRef, useState } from "react";
import mapboxgl, { type GeoJSONSource } from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { MapPin, Scan } from "lucide-react";
import { useFleet } from "../model/FleetProvider";
import { boundsForFeatures, validFeatures } from "../model/map-model";
import { positionTime, statusLabels } from "../model/types";
import { LayoutEditingContext } from "../../../shared/components/LayoutEditingContext";
import { EmptyState } from "../../../shared/components/EmptyState";

const sourceId = "fleet-vehicles";
const token = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;
const style = () =>
  document.documentElement.dataset.theme === "dark"
    ? "mapbox://styles/mapbox/dark-v11"
    : "mapbox://styles/mapbox/streets-v12";
export default function VehicleMap() {
  const fleet = useFleet();
  const editing = useContext(LayoutEditingContext);
  const container = useRef<HTMLDivElement>(null);
  const instance = useRef<mapboxgl.Map | null>(null);
  const latest = useRef(fleet);
  latest.current = fleet;
  const editRef = useRef(editing);
  editRef.current = editing;
  const [failure, setFailure] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const fitted = useRef(false);
  const features = validFeatures(fleet.map);
  useEffect(() => {
    fitted.current = false;
  }, [fleet.q, fleet.status]);
  useEffect(() => {
    if (!token?.startsWith("pk.") || !container.current) return;
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
    fitted.current = false;
    let frame = 0;
    map.addControl(
      new mapboxgl.NavigationControl({ showCompass: false }),
      "top-right",
    );
    const install = () => {
      const data = {
        type: "FeatureCollection" as const,
        features: validFeatures(latest.current.map),
      };
      if (!map.getSource(sourceId)) {
        map.addSource(sourceId, {
          type: "geojson",
          data,
          cluster: true,
          clusterMaxZoom: 14,
          clusterRadius: 42,
          promoteId: "id",
        });
        map.addLayer({
          id: "fleet-clusters",
          type: "circle",
          source: sourceId,
          filter: ["has", "point_count"],
          paint: {
            "circle-color": "#1479e8",
            "circle-radius": [
              "step",
              ["get", "point_count"],
              19,
              20,
              24,
              50,
              28,
            ],
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
          },
        });
        map.addLayer({
          id: "fleet-counts",
          type: "symbol",
          source: sourceId,
          filter: ["has", "point_count"],
          layout: {
            "text-field": ["get", "point_count_abbreviated"],
            "text-size": 12,
          },
          paint: { "text-color": "#ffffff" },
        });
        map.addLayer({
          id: "fleet-points",
          type: "circle",
          source: sourceId,
          filter: ["!", ["has", "point_count"]],
          paint: {
            "circle-color": [
              "match",
              ["get", "status"],
              "moving",
              "#17a68b",
              "stopped",
              "#df982b",
              "#8291a6",
            ],
            "circle-radius": 8,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
          },
        });
        map.addLayer({
          id: "fleet-names",
          type: "symbol",
          source: sourceId,
          minzoom: 9,
          filter: ["!", ["has", "point_count"]],
          layout: {
            "text-field": ["get", "name"],
            "text-size": 11,
            "text-offset": [0, 1.5],
            "text-anchor": "top",
          },
          paint: {
            "text-color": "#192a42",
            "text-halo-color": "#ffffff",
            "text-halo-width": 1.5,
          },
        });
      }
      const bounds = boundsForFeatures(data.features);
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
    map.on("click", "fleet-points", (e) => {
      if (!editRef.current) {
        const id = e.features?.[0]?.properties?.id;
        if (typeof id === "string") latest.current.select(id);
      }
    });
    map.on("click", "fleet-clusters", (e) => {
      if (editRef.current) return;
      const feature = e.features?.[0];
      if (!feature || feature.geometry.type !== "Point") return;
      const center = feature.geometry.coordinates as [number, number];
      const source = map.getSource(sourceId) as GeoJSONSource;
      source.getClusterExpansionZoom(
        Number(feature.properties?.cluster_id),
        (error, zoom) => {
          if (!error && zoom != null) map.easeTo({ center, zoom });
        },
      );
    });
    map.on("mouseenter", "fleet-points", () => {
      if (!editRef.current) map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", "fleet-points", () => {
      map.getCanvas().style.cursor = "";
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
      map.remove();
      instance.current = null;
    };
  }, []);
  useEffect(() => {
    const map = instance.current;
    if (!map || !ready) return;
    const source = map.getSource(sourceId) as GeoJSONSource | undefined;
    source?.setData({ type: "FeatureCollection", features });
    const bounds = boundsForFeatures(features);
    if (bounds && !fitted.current) {
      map.fitBounds(bounds, { padding: 50, maxZoom: 12, duration: 0 });
      fitted.current = true;
    }
    if (map.getLayer("fleet-points")) {
      map.setPaintProperty("fleet-points", "circle-stroke-color", [
        "case",
        ["==", ["get", "id"], fleet.selectedId || ""],
        "#003dac",
        "#ffffff",
      ]);
      map.setPaintProperty("fleet-points", "circle-stroke-width", [
        "case",
        ["==", ["get", "id"], fleet.selectedId || ""],
        5,
        2,
      ]);
    }
  }, [fleet.map, fleet.selectedId, ready]);
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
    </div>
  );
}
