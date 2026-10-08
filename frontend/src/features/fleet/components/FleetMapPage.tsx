import { FleetMapWidget } from "./FleetMapWidget";
import { VehicleListWidget } from "./VehicleListWidget";

export function FleetMapPage() {
  return (
    <div className="fleet-map-page" aria-label="Mapa i lista pojazdów">
      <FleetMapWidget />
      <VehicleListWidget variant="sidebar" />
    </div>
  );
}
