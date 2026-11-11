import { Map, MapPin } from "lucide-react";
import { lazy, Suspense } from "react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { EmptyState } from "../../../shared/components/EmptyState";
import { useFleet } from "../model/FleetProvider";
import { updateTime } from "../model/types";
const VehicleMap = lazy(() => import("./VehicleMap"));
export function FleetMapWidget() {
  const fleet = useFleet();
  return (
    <WidgetFrame
      title="Mapa floty"
      icon={Map}
      badge="Pozycje pojazdów"
      className="map-widget"
    >
      <p className="fleet-update map-update-time" role="status">
        Ostatnia udana synchronizacja:{" "}
        {updateTime(fleet.list?.source.last_success_at ?? null)}.
      </p>
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
