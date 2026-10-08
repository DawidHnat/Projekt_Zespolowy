import { Activity, BellRing, Gauge, ShieldCheck } from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import type { WidgetProps } from "../../dashboard/model/widget-types";

export function ActivityWidget({ onHide }: WidgetProps) {
  return (
    <WidgetFrame
      title="Alerty i aktywność"
      icon={Activity}
      onHide={onHide}
      className="activity-widget"
    >
      <div className="activity-intro">
        <span className="activity-orbit">
          <BellRing size={28} />
        </span>
        <h3>Bądź na bieżąco</h3>
        <p>Zdarzenia i alerty z floty pojawią się w tym miejscu.</p>
      </div>
      <div className="activity-categories">
        <span>
          <ShieldCheck size={16} />
          Statusy pojazdów
        </span>
        <span>
          <Gauge size={16} />
          Wybrane parametry
        </span>
      </div>
    </WidgetFrame>
  );
}
