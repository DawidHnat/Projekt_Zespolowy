import {
  DashboardGrid,
  type DashboardGridProps,
} from "../../dashboard/components/DashboardGrid";
import { SECTION_WIDGETS } from "../../dashboard/model/widget-layout";

const mapWidgets = [...SECTION_WIDGETS.map];
type FleetMapPageProps = Pick<DashboardGridProps, "layouts" | "editing" | "onLayout">;

export function FleetMapPage(props: FleetMapPageProps) {
  return (
    <div className="fleet-map-page" aria-label="Mapa i lista pojazdów">
      <DashboardGrid {...props} section="map" ids={mapWidgets} />
    </div>
  );
}
