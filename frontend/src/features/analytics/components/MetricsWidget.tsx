import {
  ChartNoAxesCombined,
  Truck,
  Navigation,
  CircleParking,
  BellRing,
} from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";

import { useFleet } from "../../fleet/model/FleetProvider";

const metrics = [
  { label: "Pojazdy we flocie", icon: Truck, tone: "accent", field: "total" },
  {
    label: "Pojazdy w ruchu",
    icon: Navigation,
    tone: "success",
    field: "moving",
  },
  {
    label: "Na postoju",
    icon: CircleParking,
    tone: "warning",
    field: "stopped",
  },
  {
    label: "Dane nieaktualne",
    icon: BellRing,
    tone: "danger",
    field: "offline",
  },
] as const;

export function MetricsWidget() {
  const fleet = useFleet();
  return (
    <WidgetFrame
      title="Przegląd floty"
      icon={ChartNoAxesCombined}
      className="metrics-widget"
      badge="Najważniejsze wskaźniki"
    >
      <div className="metrics-grid">
        {metrics.map(({ label, icon: Icon, tone, field }) => (
          <div className={`metric metric-${tone}`} key={label}>
            <span className="metric-icon">
              <Icon size={22} aria-hidden="true" />
            </span>
            <div>
              <h3>{label}</h3>
              <p className="metric-value">{fleet.summary?.[field] ?? "—"}</p>
              <p className="metric-hint">
                {fleet.summary
                  ? "Ostatnie pomiary floty"
                  : "Oczekiwanie na dane"}
              </p>
            </div>
            <span className="metric-line" aria-hidden="true" />
          </div>
        ))}
      </div>
    </WidgetFrame>
  );
}
