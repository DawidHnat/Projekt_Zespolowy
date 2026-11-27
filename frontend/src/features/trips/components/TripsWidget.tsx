import { useEffect, useState } from "react";
import { Route } from "lucide-react";
import { api } from "../../../shared/api/client";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { EmptyState } from "../../../shared/components/EmptyState";
import { TripDayPicker } from "./TripDayPicker";
import { useTripDay } from "../model/useTripDay";
import { tripDayLabel } from "../model/trip-day";
import { tripListPath, tripTime, type TripList } from "../model/annotations";

export function TripsWidget() {
  const day = useTripDay();
  const [data, setData] = useState<TripList | null>(null);
  const [failed, setFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  const selectedDay = day.value;

  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setFailed(false);
    api<TripList>(tripListPath(null, selectedDay, 1, 5), { signal: controller.signal })
      .then(result => { if (!controller.signal.aborted) setData(result); })
      .catch(() => { if (!controller.signal.aborted) setFailed(true); });
    return () => controller.abort();
  }, [selectedDay, retry]);

  return (
    <WidgetFrame title="Ostatnie przejazdy" icon={Route} className="trips-widget"
      badge={tripDayLabel(day.value, day.today)}>
      <div className="trips-day-view">
        <TripDayPicker value={day.value} today={day.today} onChange={day.select} label="Dzień ostatnich przejazdów" />
        {failed ? (
          <div role="alert">
            <p>Nie można pobrać przejazdów.</p>
            <button className="button button-secondary" onClick={() => setRetry(value => value + 1)}>Spróbuj ponownie</button>
          </div>
        ) : !data ? <p role="status">Pobieranie przejazdów…</p> : data.items.length ? (
          <ul className="trip-stop-list" aria-label="Ostatnie zapisane przejazdy">
            {data.items.map(trip => <li key={trip.id}>
              <strong>{trip.vehicle_name ?? "Pojazd"} · {tripTime(trip.start_at)}</strong>
              <span>{trip.start_address || "Brak adresu"} → {trip.end_address || "Brak adresu"}</span>
              {trip.withdrawn_at && <small>Wycofany z raportu źródła</small>}
            </li>)}
          </ul>
        ) : <EmptyState icon={Route} title="Brak zapisanych przejazdów" description="Wybierz inny dzień." />}
      </div>
    </WidgetFrame>
  );
}
