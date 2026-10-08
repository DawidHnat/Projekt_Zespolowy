import { CircleGauge } from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import type { WidgetProps } from "../../dashboard/model/widget-types";

export function UtilizationWidget({ onHide }: WidgetProps) {
  return (
    <WidgetFrame
      title="Wykorzystanie floty"
      icon={CircleGauge}
      onHide={onHide}
      className="utilization-widget"
    >
      <div className="utilization-body">
        <div className="empty-gauge">
          <span>
            —<small>Brak danych</small>
          </span>
        </div>
        <ul className="gauge-legend">
          <li>
            <i className="legend-dot success-dot" />W ruchu <span>—</span>
          </li>
          <li>
            <i className="legend-dot warning-dot" />
            Na postoju <span>—</span>
          </li>
          <li>
            <i className="legend-dot muted-dot" />
            Pozostałe <span>—</span>
          </li>
        </ul>
      </div>
      <p className="widget-footnote">
        Przejrzysty obraz wykorzystania pojazdów.
      </p>
    </WidgetFrame>
  );
}
