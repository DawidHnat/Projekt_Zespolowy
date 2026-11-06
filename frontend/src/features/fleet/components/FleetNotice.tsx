import { useFleet } from "../model/FleetProvider";
import { updateTime } from "../model/types";
export function FleetNotice() {
  const f = useFleet();
  const lastSuccess = updateTime(f.list?.source.last_success_at ?? null);
  if (f.error)
    return (
      <div className="fleet-notice" role="alert">
        <span>
          {f.error}
          {f.list && ` Wyświetlamy ostatni poprawny odczyt: ${lastSuccess}.`}
        </span>
        <button onClick={f.refresh}>Ponów</button>
      </div>
    );
  if (f.list?.source.status === "degraded")
    return (
      <p className="fleet-notice" role="status">
        WEBFLEET jest chwilowo niedostępny. Ostatni poprawny odczyt: {lastSuccess}.
      </p>
    );
  if (f.loading && f.list)
    return (
      <p className="fleet-update" role="status">
        Aktualizowanie widoku… Ostatnia synchronizacja: {lastSuccess}.
      </p>
    );
  return f.list ? (
    <p className="fleet-update" role="status">
      Ostatnia synchronizacja: {lastSuccess}.
    </p>
  ) : null;
}
