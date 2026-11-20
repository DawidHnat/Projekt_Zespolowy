import { CheckCheck, Circle, ExternalLink } from "lucide-react";
import type { Alert } from "../../../shared/api/generated/contracts";
import { useFleet } from "../../fleet/model/FleetProvider";

const distance = (value: number) => value.toLocaleString("pl-PL", { maximumFractionDigits: 3 });
const eventDay = (value: string) => new Intl.DateTimeFormat("pl-PL", { timeZone: "UTC", dateStyle: "long" }).format(new Date(`${value}T12:00:00Z`));

export function AlertRows({ items, saving, onReceipt }: {
  items: Alert[]; saving: string | null; onReceipt: (item: Alert) => void;
}) {
  const fleet = useFleet();
  return <ul className="alert-list" aria-label="Alerty dziennego dystansu">
    {items.map(item => <li key={item.id} className={item.read_at ? "alert-read" : "alert-unread"}>
      <div className="alert-row-heading">
        <strong>Przekroczenie dziennego dystansu</strong>
        <span>{item.read_at ? "Przeczytany" : "Nieprzeczytany"}</span>
      </div>
      <button className="alert-vehicle" onClick={() => fleet.inspect(item.vehicle_id)}>
        {item.vehicle_name || item.vehicle_id}{item.license_plate ? ` · ${item.license_plate}` : ""}
        <ExternalLink size={14} aria-hidden="true" />
      </button>
      <p><time dateTime={item.event_day}>{eventDay(item.event_day)}</time> · czas polski</p>
      <p><strong>{distance(item.distance_km)} km</strong> · próg {distance(item.threshold_km)} km</p>
      <p>Niepełne dane: dystans obejmuje odebrane pomiary, a nie cały dzień.</p>
      <button className="button button-secondary" disabled={saving !== null}
        onClick={() => onReceipt(item)}>
        {item.read_at ? <Circle size={16} aria-hidden="true" /> : <CheckCheck size={16} aria-hidden="true" />}
        {saving === item.id ? "Zapisywanie…" : item.read_at ? "Oznacz jako nieprzeczytany" : "Oznacz jako przeczytany"}
      </button>
    </li>)}
  </ul>;
}
