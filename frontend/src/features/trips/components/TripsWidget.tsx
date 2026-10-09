import { Route, MapPin, Clock3, ParkingCircle } from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { EmptyState } from "../../../shared/components/EmptyState";
import { TripDayPicker } from "./TripDayPicker";
import { useTripDay } from "../model/useTripDay";
import { tripDayLabel } from "../model/trip-day";

export function TripsWidget() {
  const day = useTripDay();
  return (
    <WidgetFrame
      title="Ostatnie przejazdy"
      icon={Route}
      className="trips-widget"
      badge={tripDayLabel(day.value, day.today)}
    >
      <div className="trips-day-view">
        <TripDayPicker
          value={day.value}
          today={day.today}
          onChange={day.select}
          label="Dzień ostatnich przejazdów"
        />
        <div className="trips-day-context">
          <strong>{tripDayLabel(day.value, day.today)}</strong>
          <span>Przejazdy i postoje · czas polski</span>
        </div>
        <EmptyState
          icon={Route}
          title="Historia w przygotowaniu"
          description="Tutaj pojawią się pojazdy i ich trasy z wybranego dnia."
        />
        <div className="trips-view-legend" aria-label="Informacje o przejeździe">
          <span><MapPin size={14} aria-hidden="true" /> Trasa</span>
          <span><ParkingCircle size={14} aria-hidden="true" /> Postoje</span>
          <span><Clock3 size={14} aria-hidden="true" /> Czas i dystans</span>
        </div>
      </div>
    </WidgetFrame>
  );
}
