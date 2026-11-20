import { Activity } from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { useAlerts } from "../model/useAlerts";

export function ActivityWidget() {
  const alerts = useAlerts("unread", 1, 10);
  return <WidgetFrame title="Alerty i aktywność" icon={Activity} className="activity-widget">
    <div className="activity-alerts">
      {alerts.loading && !alerts.data && <p role="status">Pobieranie alertów…</p>}
      {alerts.error && <div role="alert"><p>{alerts.error}</p><button className="button button-secondary" onClick={alerts.refresh}>Ponów alerty</button></div>}
      {alerts.data && <>
        <p><strong>{alerts.data.total}</strong> nieprzeczytanych alertów dziennego dystansu</p>
        {!alerts.data.total && <p>Brak nieprzeczytanych przekroczeń. Dystans obejmuje odebrane pomiary.</p>}
        <ul>{alerts.data.items.slice(0, 3).map(item => <li key={item.id}>
          <strong>{item.vehicle_name || item.vehicle_id}</strong>
          <span>{item.distance_km.toLocaleString("pl-PL")} km · próg {item.threshold_km.toLocaleString("pl-PL")} km</span>
        </li>)}</ul>
        {alerts.data.total > 0 && <p>Niepełne pokrycie dnia. Widoczne maksymalnie trzy najnowsze zdarzenia.</p>}
      </>}
      <a className="button button-secondary" href="#alerts">Wszystkie alerty</a>
    </div>
  </WidgetFrame>;
}
