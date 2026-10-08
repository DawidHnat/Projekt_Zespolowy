import { useFleet } from "../model/FleetProvider";
export function FleetNotice() {
  const f = useFleet();
  if (f.error)
    return (
      <div className="fleet-notice" role="alert">
        <span>
          {f.error}
          {f.list && " Wyświetlamy ostatni pobrany widok."}
        </span>
        <button onClick={f.refresh}>Ponów</button>
      </div>
    );
  if (f.list?.source.status === "degraded")
    return (
      <p className="fleet-notice" role="status">
        WEBFLEET jest chwilowo niedostępny. Wyświetlamy ostatnie pomiary.
      </p>
    );
  if (f.loading && f.list)
    return (
      <p className="fleet-update" role="status">
        Aktualizowanie widoku…
      </p>
    );
  return null;
}
