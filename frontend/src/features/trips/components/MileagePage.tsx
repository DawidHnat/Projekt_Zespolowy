import { useEffect, useState } from "react";
import { api, ApiError } from "../../../shared/api/client";
import { DatePicker } from "../../../shared/components/DatePicker";
import { ListPagination } from "../../../shared/components/ListPagination";
import { VehiclePicker } from "../../fleet/components/VehiclePicker";
import type { TripList } from "../model/annotations";
import { initialPeriod, periodError } from "../model/mileage-period";

type MileagePeriod = TripList & {
  summary: {
    distance_km: number | null;
    documented_km: number | null;
    missing_purpose: number;
    missing_distance: number;
  };
};

const formatKm = (value: number | null) =>
  value === null ? "Brak danych" : `${value.toLocaleString("pl-PL", { maximumFractionDigits: 3 })} km`;

export function MileagePage() {
  const [initial] = useState(() => initialPeriod());
  const todayIso = initial.through;
  const [from, setFrom] = useState(initial.from);
  const [through, setThrough] = useState(initial.through);
  const rangeError = periodError(from, through);
  const [vehicle, setVehicle] = useState<{ id: string; name: string } | null>(null);
  const [data, setData] = useState<MileagePeriod | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    if (!vehicle || rangeError) return;
    const controller = new AbortController();
    const query = new URLSearchParams({
      vehicle_id: vehicle.id, from_day: from, through,
      page: String(page), page_size: String(pageSize),
    });
    setLoading(true);
    setError("");
    api<MileagePeriod>(`/trips/mileage?${query}`, { signal: controller.signal })
      .then((result) => { if (!controller.signal.aborted) setData(result); })
      .catch((failure: unknown) => {
        if (controller.signal.aborted) return;
        setError(failure instanceof ApiError && failure.status === 422
          ? "Wybierz prawidłowy okres do 93 dni."
          : "Nie można pobrać ewidencji.");
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [vehicle, from, through, page, pageSize, revision, rangeError]);

  const reset = () => { setData(null); setError(""); setPage(1); };

  return (
    <div className="mileage-page">
      <div className="mileage-filters">
        <DatePicker label="Od dnia" value={from} required maxDate={through}
          onChange={(value) => { if (value) { reset(); setFrom(value); } }} />
        <DatePicker label="Do dnia" value={through} required minDate={from} maxDate={todayIso}
          onChange={(value) => { if (value) { reset(); setThrough(value); } }} />
        <VehiclePicker selected={vehicle} disabled={false}
          onSelect={(next) => { reset(); setVehicle(next); }} />
      </div>
      {rangeError && <p className="form-error" role="alert">{rangeError}</p>}
      {!vehicle && <p>Wybierz pojazd, aby obliczyć ewidencję.</p>}
      {loading && <p role="status">Pobieranie ewidencji…</p>}
      {error && <div role="alert"><p>{error}</p><button type="button" className="button button-secondary"
        onClick={() => setRevision((value) => value + 1)}>Ponów odczyt</button></div>}
      {data && <section aria-label="Podsumowanie ewidencji" className="mileage-results">
        <h2>{vehicle?.name}</h2>
        <dl className="mileage-stats">
          <div><dt>Przejazdy</dt><dd>{data.total}</dd></div>
          <div><dt>Zapisany dystans</dt><dd>{formatKm(data.summary.distance_km)}</dd></div>
          <div><dt>Rozpisane kilometry</dt><dd>{formatKm(data.summary.documented_km)}</dd></div>
          <div><dt>Brak celu</dt><dd>{data.summary.missing_purpose}</dd></div>
          <div><dt>Brak dystansu</dt><dd>{data.summary.missing_distance}</dd></div>
        </dl>
        <p className="trip-time-hint">Przejazdy liczone według dnia rozpoczęcia; okres do 93 dni.</p>
        {!data.total && <p>Brak zapisanych przejazdów w tym okresie.</p>}
        {data.items.length > 0 && <ul className="trip-annotation-list" aria-label="Przejazdy w ewidencji">
          {data.items.map((trip) => <li key={trip.id}>
            <strong>{new Date(trip.start_at).toLocaleString("pl-PL", { timeZone: "Europe/Warsaw" })}</strong>
            <span>{formatKm(trip.distance_km)} · {trip.annotation.purpose || "Brak celu"}</span>
          </li>)}
        </ul>}
        <ListPagination page={page} pageSize={pageSize} total={data.total}
          loading={loading} label="Przejazdy w ewidencji" onPage={setPage}
          onPageSize={(size) => { reset(); setPageSize(size); }} />
      </section>}
    </div>
  );
}
