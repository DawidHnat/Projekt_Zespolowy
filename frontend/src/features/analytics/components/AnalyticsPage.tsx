import { useEffect, useState } from "react";
import { api } from "../../../shared/api/client";
import type { UsagePeriod, VehicleUsage } from "../../../shared/api/generated/contracts";
import { DatePicker } from "../../../shared/components/DatePicker";
import { VehiclePicker } from "../../fleet/components/VehiclePicker";
import { previousDay, warsawDay } from "../../trips/model/trip-day";

type Selection = { id: string; name: string };
type Sort = "name" | "distance_km" | "trip_count" | "active_days";
const limit = 10;
const format = new Intl.NumberFormat("pl-PL", { maximumFractionDigits: 3 });
const display = (value: number | null, unit = "") =>
  value === null ? "Brak danych" : `${format.format(value)}${unit}`;

function sortedUsage(items: VehicleUsage[], sort: Sort) {
  return [...items].sort((left, right) => {
    if (sort !== "name") {
      const a = left[sort] ?? -1;
      const b = right[sort] ?? -1;
      if (a !== b) return b - a;
    }
    return left.name.localeCompare(right.name, "pl");
  });
}

export function AnalyticsPage() {
  const today = warsawDay();
  const [from, setFrom] = useState(`${today.slice(0, 7)}-01`);
  const [through, setThrough] = useState(today);
  const [choice, setChoice] = useState<Selection | null>(null);
  const [vehicles, setVehicles] = useState<Selection[]>([]);
  const [data, setData] = useState<UsagePeriod | null>(null);
  const [sort, setSort] = useState<Sort>("distance_km");
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    if (!vehicles.length) return;
    const controller = new AbortController();
    const query = new URLSearchParams({ from_day: from, through });
    for (const vehicle of vehicles) query.append("vehicle_ids", vehicle.id);
    setData(null);
    setError(false);
    api<UsagePeriod>(`/analytics/usage?${query}`, { signal: controller.signal })
      .then(result => { if (!controller.signal.aborted) setData(result); })
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, [from, through, vehicles, retry]);

  const canAdd = choice && vehicles.length < limit && !vehicles.some(vehicle => vehicle.id === choice.id);

  return <div className="usage-page">
    <div className="usage-controls">
      <div className="usage-dates">
        <DatePicker label="Od dnia" value={from} maxDate={through} required
          onChange={day => { if (day && day !== from) { setData(null); setFrom(day); } }} />
        <DatePicker label="Do dnia" value={through} minDate={from} maxDate={today} required
          onChange={day => { if (day && day !== through) { setData(null); setThrough(day); } }} />
        <button type="button" className="button button-secondary" onClick={() => {
          const day = previousDay(today);
          if (from === day && through === day) return;
          setData(null); setFrom(day); setThrough(day);
        }}>Wczoraj</button>
      </div>
      <VehiclePicker selected={choice} onSelect={setChoice} disabled={vehicles.length >= limit}
        legend="Pojazdy do porównania" />
      <button type="button" className="button button-secondary" disabled={!canAdd}
        onClick={() => {
          if (choice && canAdd) { setData(null); setVehicles(existing => [...existing, choice]); }
        }}>Dodaj do porównania</button>
      {vehicles.length > 0 && <ul aria-label="Wybrane pojazdy" className="usage-selection">
        {vehicles.map(vehicle => <li key={vehicle.id}>
          <button type="button" className="button button-secondary"
            aria-label={`Usuń z porównania: ${vehicle.name}`}
            onClick={() => { setData(null); setVehicles(items => items.filter(item => item.id !== vehicle.id)); }}>
            {vehicle.name} ×
          </button>
        </li>)}
      </ul>}
    </div>

    {!vehicles.length ? <p>Dodaj pojazd, aby zobaczyć wykorzystanie w okresie.</p> : error ? (
      <div role="alert">
        <p>Nie można pobrać porównania. Sprawdź zakres do 93 dni.</p>
        <button type="button" className="button button-secondary" onClick={() => setRetry(value => value + 1)}>
          Ponów odczyt
        </button>
      </div>
    ) : !data ? <p role="status">Pobieranie porównania…</p> : (
      <section aria-label="Wykorzystanie pojazdów" className="usage-results">
        <dl className="usage-metrics">
          <div><dt>Zapisany dystans</dt><dd>{display(data.summary.distance_km, " km")}</dd></div>
          <div><dt>Zapisane przejazdy</dt><dd>{display(data.summary.trip_count)}</dd></div>
          <div><dt>Dni z przejazdem</dt><dd>{display(data.summary.active_days)}</dd></div>
        </dl>
        <p>Dane z historii WEBFLEET. Przejazd liczy się według dnia rozpoczęcia w Europe/Warsaw.</p>
        {!data.summary.coverage_complete && <p>Pokrycie lub dystans części przejazdów są niepełne.</p>}
        <label>Sortowanie <select aria-label="Sortuj porównanie" value={sort}
          onChange={event => setSort(event.target.value as Sort)}>
          <option value="distance_km">Dystans</option>
          <option value="trip_count">Przejazdy</option>
          <option value="active_days">Dni z przejazdem</option>
          <option value="name">Nazwa</option>
        </select></label>
        <div className="usage-table-wrap" role="region" tabIndex={0} aria-label="Tabela wykorzystania">
          <table>
            <thead><tr><th scope="col">Pojazd</th><th scope="col">Dystans</th><th scope="col">Przejazdy</th>
              <th scope="col">Dni z przejazdem</th><th scope="col">Raporty według dnia zakończenia</th></tr></thead>
            <tbody>{sortedUsage(data.items, sort).map(item => <tr key={item.vehicle_id}>
              <th scope="row">{item.name}</th>
              <td>{display(item.distance_km, " km")}</td>
              <td>{display(item.trip_count)}</td>
              <td>{display(item.active_days)}</td>
              <td>{item.coverage.state === "unavailable" ? "Brak raportów"
                : `${item.coverage.covered_days.length} z ${item.coverage.requested_days} dni`}
                {item.coverage.failed_days.length > 0 && ` · błędy: ${item.coverage.failed_days.length}`}
                {item.missing_distance > 0 && ` · bez dystansu: ${item.missing_distance}`}
              </td>
            </tr>)}</tbody>
          </table>
        </div>
      </section>
    )}
  </div>;
}
