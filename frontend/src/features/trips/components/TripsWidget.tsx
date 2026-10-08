import { Route, ArrowUpRight } from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { EmptyState } from "../../../shared/components/EmptyState";
import type { WidgetProps } from "../../dashboard/model/widget-types";

export function TripsWidget({ onHide }: WidgetProps) {
  return (
    <WidgetFrame
      title="Ostatnie przejazdy"
      icon={Route}
      onHide={onHide}
      className="trips-widget"
    >
      <EmptyState
        icon={ArrowUpRight}
        title="Każda trasa ma swoją historię"
        description="Tutaj zobaczysz przejazdy, dystans, cel i opis podróży."
      />
    </WidgetFrame>
  );
}
