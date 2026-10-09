import { Route, ArrowUpRight } from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { EmptyState } from "../../../shared/components/EmptyState";

export function TripsWidget() {
  return (
    <WidgetFrame
      title="Ostatnie przejazdy"
      icon={Route}
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
