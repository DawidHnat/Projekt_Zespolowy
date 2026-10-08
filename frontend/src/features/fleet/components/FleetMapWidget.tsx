import { Map, MapPin } from "lucide-react";
import { lazy, Suspense } from "react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { EmptyState } from "../../../shared/components/EmptyState";
const VehicleMap = lazy(() => import("./VehicleMap"));
export function FleetMapWidget() {
  return (
    <WidgetFrame
      title="Mapa floty"
      icon={Map}
      badge="Pozycje pojazdów"
      className="map-widget"
    >
      <Suspense
        fallback={
          <div className="map-canvas">
            <EmptyState
              icon={MapPin}
              title="Ładowanie mapy…"
              description="Przygotowujemy widok floty."
            />
          </div>
        }
      >
        <VehicleMap />
      </Suspense>
    </WidgetFrame>
  );
}
