import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { useFleet } from "../model/FleetProvider";
import { refreshSeconds } from "../model/source-refresh";

export function FleetRefreshButton({ compact = false }: { compact?: boolean }) {
  const { sourceRefresh: refresh } = useFleet();
  const [now, setNow] = useState(() => performance.now());
  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | undefined;
    const tick = () => {
      const time = performance.now();
      setNow(time);
      if (time >= refresh.deadline) clearInterval(timer);
    };
    const resume = () => {
      clearInterval(timer);
      tick();
      if (document.visibilityState !== "hidden" && performance.now() < refresh.deadline)
        timer = setInterval(tick, 1000);
    };
    resume();
    document.addEventListener("visibilitychange", resume);
    return () => { clearInterval(timer); document.removeEventListener("visibilitychange", resume); };
  }, [refresh.deadline]);
  const remaining = refreshSeconds(refresh.deadline, now);
  const running = refresh.pending || refresh.state?.running;
  const disabled = !refresh.online || !refresh.state?.enabled || refresh.unavailable
    || running || remaining > 0;
  const reason = !refresh.online ? "Brak połączenia z siecią"
    : !refresh.state || refresh.unavailable ? "Sprawdź dostępność odświeżania"
    : !refresh.state.enabled ? "Synchronizacja jest wyłączona"
    : running ? "Odświeżanie danych trwa"
    : remaining ? `Kolejne odświeżenie za ${remaining} sekund`
    : "Sprawdź najnowsze pozycje i prędkości floty";
  const badge = remaining < 100 ? remaining : remaining < 3600
    ? `${Math.ceil(remaining / 60)}m` : `${Math.ceil(remaining / 3600)}h`;
  return (
    <button type="button"
      className={`button button-secondary fleet-refresh-button ${compact ? "fleet-refresh-compact" : ""}`}
      aria-label={`${compact ? "Odśwież dane pojazdu" : "Odśwież dane floty"}. ${reason}`}
      aria-disabled={Boolean(disabled)}
      title={reason}
      onClick={() => void refresh.run()}
    >
      <RefreshCw size={15} aria-hidden="true" className={running ? "fleet-refresh-spinning" : undefined} />
      {!compact && <span>{running ? "Odświeżanie…" : refresh.state && !refresh.state.enabled
        ? "Wyłączone" : remaining ? `Za ${remaining} s` : "Odśwież"}</span>}
      {compact && !running && remaining > 0 && <span className="fleet-refresh-count" aria-hidden="true">{badge}</span>}
    </button>
  );
}
