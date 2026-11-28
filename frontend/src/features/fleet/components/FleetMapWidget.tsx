import { Map, MapPin } from "lucide-react";
import { lazy, Suspense } from "react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { EmptyState } from "../../../shared/components/EmptyState";
import { ErrorBoundary } from "../../../shared/components/ErrorBoundary";
import { useFleet } from "../model/FleetProvider";
import { updateTime } from "../model/types";
import { FleetRefreshButton } from "./FleetRefreshButton";

const hasMapToken = import.meta.env.VITE_MAPBOX_TOKEN?.startsWith("pk.");
const VehicleMap = lazy(() => hasMapToken
  ? import("./VehicleMap")
  : import("./MapConfigurationNotice"));

export function FleetMapWidget() {
  const fleet = useFleet();
  return (
    <WidgetFrame
      title="Mapa floty"
      icon={Map}
      badge="Pozycje pojazdów"
      className="map-widget"
    >
      <div className="fleet-map-toolbar">
        <div>
          <p className="fleet-update map-update-time">
            Ostatnia udana synchronizacja:{" "}
            {updateTime(fleet.list?.source.last_success_at ?? null)}.
          </p>
          <p className="fleet-refresh-feedback" role="status">{fleet.sourceRefresh.message}</p>
        </div>
        <FleetRefreshButton />
      </div>
      <ErrorBoundary
        fallback={
          <div className="map-canvas map-load-fallback" role="alert">
            <EmptyState
              icon={MapPin}
              title="Nie udało się załadować mapy"
              description="Lista pojazdów i pozostałe formularze nadal działają. Odśwież stronę, aby ponowić pobieranie mapy. Niezapisane zmiany wymagają potwierdzenia w przeglądarce."
            />
            <button
              className="button button-primary"
              type="button"
              onClick={() => window.location.reload()}
            >
              Odśwież stronę
            </button>
          </div>
        }
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
      </ErrorBoundary>
    </WidgetFrame>
  );
}
