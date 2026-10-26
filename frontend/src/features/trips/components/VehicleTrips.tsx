import { useEffect, useState } from "react";
import { Route } from "lucide-react";
import { api } from "../../../shared/api/client";
import { EmptyState } from "../../../shared/components/EmptyState";
import { ListPagination } from "../../../shared/components/ListPagination";
import { useAuth } from "../../auth/AuthProvider";
import { TripDayPicker } from "./TripDayPicker";
import { TripAnnotationEditor } from "./TripAnnotationEditor";
import { tripListPath, type TripList } from "../model/annotations";

const tripTime = (value: string) => new Intl.DateTimeFormat("pl-PL", {
  timeZone: "Europe/Warsaw", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
}).format(new Date(value));

export function VehicleTrips({ vehicleId, day, today, onDay, onUnsaved }: {
  vehicleId: string; day: string; today: string; onDay: (day: string) => void;
  onUnsaved: (value: boolean) => void;
}) {
  const { user } = useAuth();
  const [data, setData] = useState<TripList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [selected, setSelected] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => { onUnsaved(dirty); return () => onUnsaved(false); }, [dirty, onUnsaved]);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setData(null); setSelected(null); setError(null);
    api<TripList>(tripListPath(vehicleId, day, page, pageSize), { signal: controller.signal })
      .then(result => { if (!controller.signal.aborted) setData(result); })
      .catch(err => { if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "Nie można pobrać przejazdów."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [vehicleId, day, page, pageSize, revision]);
  const trip = data?.items.find(item => item.id === selected);
  return (
    <div className="vehicle-trips">
      <TripDayPicker value={day} today={today} label="Dzień podróży pojazdu" disabled={dirty}
        onChange={value => { setPage(1); onDay(value); }} />
      <p className="trip-time-hint">Czas polski · przejazdy obejmujące wybrany dzień</p>
      {loading && <p role="status">Pobieranie przejazdów…</p>}
      {error && <div role="alert"><p>{error}</p><button className="button button-secondary" onClick={() => setRevision(v => v + 1)}>Spróbuj ponownie</button></div>}
      {data && <>
        {data.items.length === 0 ? <EmptyState icon={Route} title="Brak zapisanych przejazdów" description="Wybierz inny dzień, aby sprawdzić przejazdy pojazdu." /> :
          <ul className="trip-annotation-list" aria-label="Przejazdy pojazdu">{data.items.map(item => (
            <li key={item.id}><button type="button" aria-pressed={item.id === selected} disabled={dirty && item.id !== selected}
              onClick={() => setSelected(item.id)}>
              <strong>{tripTime(item.start_at)} → {item.end_at ? tripTime(item.end_at) : "Brak czasu końca"}</strong>
              <span>{item.distance_km === null ? "Brak dystansu" : `${item.distance_km.toLocaleString("pl-PL", { maximumFractionDigits: 3 })} km`} · {item.annotation.purpose || "Brak celu"}</span>
            </button></li>
          ))}</ul>}
        <ListPagination page={page} pageSize={pageSize} total={data.total} loading={loading || dirty} label="Przejazdy pojazdu"
          onPage={setPage} onPageSize={size => { setPageSize(size); setPage(1); }} />
        {trip && <TripAnnotationEditor key={trip.id} trip={trip} canEdit={user?.role === "admin" || user?.role === "editor"}
          onDirty={setDirty} onSaved={value => setData(current => current ? { ...current, items: current.items.map(item => item.id === trip.id ? { ...item, annotation: value } : item) } : current)} />}
        {dirty && <small>Przed zmianą dnia lub przejazdu zapisz albo anuluj edycję.</small>}
      </>}
    </div>
  );
}
