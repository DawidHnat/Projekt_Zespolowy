import { useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import type { TripStopList } from "../../../shared/api/generated/contracts";
import { ListPagination } from "../../../shared/components/ListPagination";
import { tripTime, tripWindowQuery } from "../model/annotations";

export function TripStops({ vehicleId, day, through }: { vehicleId: string; day: string; through: string }) {
  const [data, setData] = useState<TripStopList | null>(null);
  const [error, setError] = useState(false);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const query = tripWindowQuery(day, through);
    query.set("vehicle_id", vehicleId);
    query.set("page", String(page));
    query.set("page_size", String(size));
    setData(null);
    setError(false);
    api<TripStopList>(`/trips/stops?${query}`, { signal: controller.signal })
      .then(result => { if (!controller.signal.aborted) setData(result); })
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, [vehicleId, day, through, page, size, retry]);

  return <section>
    <h3>Postoje od 5 minut</h3>
    {error ? <div role="alert">
      <p>Nie można pobrać postojów.</p>
      <button className="button button-secondary" onClick={() => setRetry(value => value + 1)}>Ponów postoje</button>
    </div> : !data ? <p role="status">Pobieranie postojów…</p> : <>
      {data.items.length ? <ul className="trip-stop-list" aria-label="Postoje pojazdu">
        {data.items.map(stop => <li key={stop.start_at}>
          <strong>{tripTime(stop.start_at)} → {tripTime(stop.end_at)}</strong>
          <span>{Math.floor(stop.duration_seconds / 60)} min · {stop.address ?? "Brak adresu"}</span>
        </li>)}
      </ul> : <p>Brak zapisanych postojów w wybranym okresie.</p>}
      <ListPagination page={page} pageSize={size} total={data.total} loading={false} label="Postoje pojazdu"
        onPage={setPage} onPageSize={value => { setSize(value); setPage(1); }} />
    </>}
  </section>;
}
