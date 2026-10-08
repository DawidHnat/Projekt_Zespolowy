import {
  ChartNoAxesCombined,
  Truck,
  Navigation,
  CircleParking,
  BellRing,
} from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";

const metrics = [
  { label: "Pojazdy we flocie", icon: Truck, tone: "accent" },
  { label: "Pojazdy w ruchu", icon: Navigation, tone: "success" },
  { label: "Na postoju", icon: CircleParking, tone: "warning" },
  { label: "Aktywne alerty", icon: BellRing, tone: "danger" },
] as const;

export function MetricsWidget() {
  return (
    <WidgetFrame
      title="Przegląd floty"
      icon={ChartNoAxesCombined}
      className="metrics-widget"
      badge="Najważniejsze wskaźniki"
    >
      <div className="metrics-grid">
        {metrics.map(({ label, icon: Icon, tone }) => (
          <div className={`metric metric-${tone}`} key={label}>
            <span className="metric-icon">
              <Icon size={22} aria-hidden="true" />
            </span>
            <div>
              <h3>{label}</h3>
              <p className="metric-value">—</p>
              <p className="metric-hint">Oczekiwanie na dane</p>
            </div>
            <span className="metric-line" aria-hidden="true" />
          </div>
        ))}
      </div>
    </WidgetFrame>
  );
}
