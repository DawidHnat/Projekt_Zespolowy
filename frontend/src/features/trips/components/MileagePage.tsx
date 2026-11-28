import { useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import type { MileagePeriod } from "../../../shared/api/generated/contracts";
import { DatePicker } from "../../../shared/components/DatePicker";
import { ListPagination } from "../../../shared/components/ListPagination";
import { useAuth } from "../../auth/AuthProvider";
import { VehiclePicker } from "../../fleet/components/VehiclePicker";
import { tripTime } from "../model/annotations";
import { previousDay, warsawDay } from "../model/trip-day";
import { TripAnnotationEditor } from "./TripAnnotationEditor";
import { TripCoverageNote } from "./TripCoverageNote";

const kmFormat = new Intl.NumberFormat("pl-PL", { maximumFractionDigits: 3 });
const kilometres = (value: number | null) => value === null ? "Brak danych" : `${kmFormat.format(value)} km`;

export function MileagePage() {
  const today = warsawDay();
  const { user } = useAuth();
  const [from, setFrom] = useState(`${today.slice(0, 7)}-01`);
  const [through, setThrough] = useState(today);
  const [vehicle, setVehicle] = useState<{ id: string; name: string } | null>(null);
  const vehicleId = vehicle?.id;
  const [data, setData] = useState<MileagePeriod | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selected, setSelected] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [recheck, setRecheck] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!vehicleId) return;
    const request = new AbortController();
    const query = new URLSearchParams({
      vehicle_id: vehicleId, from_day: from, through, page: String(page), page_size: String(pageSize),
    });
    setLoading(true);
    setError("");
    api<MileagePeriod>(`/trips/mileage?${query}`, { signal: request.signal })
      .then(value => { if (!request.signal.aborted) setData(value); })
      .catch(() => {
        if (!request.signal.aborted) setError("Nie można pobrać ewidencji. Sprawdź zakres do 93 dni.");
      })
      .finally(() => { if (!request.signal.aborted) setLoading(false); });
    return () => request.abort();
  }, [vehicleId, from, through, page, pageSize, recheck]);

  const resetView = () => {
    setData(null);
    setError("");
    setSelected(null);
    setPage(1);
  };
  const edited = data?.items.find(trip => trip.id === selected);

  return <div className="mileage-page">
    <div className="mileage-filters">
      <div className="mileage-dates">
        <DatePicker label="Od dnia" value={from} required maxDate={through} disabled={dirty}
          onChange={day => { if (day && day !== from) { resetView(); setFrom(day); } }} />
        <DatePicker label="Do dnia" value={through} required minDate={from} maxDate={today}
          disabled={dirty}
          onChange={day => { if (day && day !== through) { resetView(); setThrough(day); } }} />
        <button className="button button-secondary" type="button" disabled={dirty} onClick={() => {
          const yesterday = previousDay(today);
          if (from === yesterday && through === yesterday) return;
          resetView(); setFrom(yesterday); setThrough(yesterday);
        }}>Wczoraj</button>
      </div>
      <VehiclePicker selected={vehicle} disabled={dirty}
        onSelect={next => { resetView(); setVehicle(next); }} />
    </div>

    {!vehicle && <p>Wybierz pojazd, aby obliczyć kilometry i sprawdzić wpisy.</p>}
    {loading && <p role="status">Pobieranie ewidencji…</p>}
    {error && <div role="alert"><p>{error}</p>
      <button className="button button-secondary" type="button" onClick={() => setRecheck(value => value + 1)}>
        Ponów odczyt
      </button>
    </div>}
    {data && <section aria-label="Podsumowanie ewidencji" className="mileage-results">
      <h2>{vehicle?.name}</h2>
      <dl className="mileage-stats">
        <div><dt>Przejazdy w okresie</dt><dd>{data.total}</dd></div>
        <div><dt>Zapisany dystans</dt><dd>{kilometres(data.summary.distance_km)}</dd></div>
        <div><dt>Rozpisane kilometry</dt><dd>{kilometres(data.summary.documented_km)}</dd></div>
        <div><dt>Brak celu</dt><dd>{data.summary.missing_purpose}</dd></div>
        <div><dt>Brak kierowcy</dt><dd>{data.summary.missing_driver}</dd></div>
        <div><dt>Brak dystansu</dt><dd>{data.summary.missing_distance}</dd></div>
      </dl>
      <p className="trip-time-hint">Przejazd liczy się w okresie, w którym się rozpoczął. Rozpisane kilometry wymagają celu, kierowcy i zapisanego dystansu.</p>
      <TripCoverageNote coverage={data.coverage} />
      {!data.total && <p>Brak zapisanych przejazdów w tym okresie.</p>}
      {data.items.length > 0 && <ul className="trip-annotation-list" aria-label="Przejazdy w ewidencji">
        {data.items.map(trip => <li key={trip.id}>
          <button type="button" aria-pressed={selected === trip.id} disabled={dirty && selected !== trip.id}
            onClick={() => setSelected(trip.id)}>
            <strong>{tripTime(trip.start_at)} · {kilometres(trip.distance_km)}</strong>
            <span>{trip.annotation.purpose || "Brak celu"}{!trip.driver_id && " · Brak kierowcy"}</span>
          </button>
        </li>)}
      </ul>}
      <ListPagination page={page} pageSize={pageSize} total={data.total}
        loading={loading || dirty} label="Przejazdy w ewidencji"
        onPage={next => { setData(null); setSelected(null); setPage(next); }}
        onPageSize={size => { resetView(); setPageSize(size); }} />
      {edited && <TripAnnotationEditor key={edited.id} trip={edited}
        canEdit={user?.role === "editor" || user?.role === "admin"}
        onDirty={setDirty} onSaved={() => setRecheck(value => value + 1)} />}
    </section>}
  </div>;
}
