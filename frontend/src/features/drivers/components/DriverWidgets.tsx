import {
  CircleHelp,
  ContactRound,
  UserRoundCheck,
  UserRoundX,
} from "lucide-react";
import { useContext } from "react";
import { LayoutEditingContext } from "../../../shared/components/LayoutEditingContext";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { useDrivers } from "../model/DriverContext";

function DriverMetric({
  kind,
}: {
  kind: "active" | "unassigned" | "missing" | "checks";
}) {
  const drivers = useDrivers();
  const editing = useContext(LayoutEditingContext);
  const summary = drivers.data?.summary;
  const config = {
    active: {
      title: "Aktywni kierowcy",
      icon: UserRoundCheck,
      value: summary?.active,
      filter: { active: "active", assigned: "all" },
    },
    unassigned: {
      title: "Bez pojazdu",
      icon: UserRoundX,
      value: summary?.active_unassigned,
      filter: { active: "active", assigned: "without" },
    },
    missing: {
      title: "Brak wpisanych kategorii",
      icon: ContactRound,
      value: summary?.active_missing_categories,
      filter: { active: "active", category: "missing" },
    },
    checks: {
      title: "Przypisania do sprawdzenia",
      icon: CircleHelp,
      value: undefined,
      filter: {},
    },
  } as const;
  const item = config[kind];
  return (
    <WidgetFrame title={item.title} icon={item.icon} className="driver-metric">
      {kind === "checks" ? (
        <>
          <p className="driver-metric-value">—</p>
          <p>
            Ocena kategorii nie jest jeszcze dostępna. Brak oceny nie potwierdza
            uprawnień.
          </p>
        </>
      ) : (
        <>
          <p className="driver-metric-value">{item.value ?? "—"}</p>
          <p>Aktywne osoby · cały wynik wspólnych filtrów</p>
          <button
            className="button button-secondary"
            disabled={!summary || editing}
            onClick={() => drivers.change(item.filter)}
          >
            Pokaż osoby
          </button>
        </>
      )}
    </WidgetFrame>
  );
}
export const DriverActiveWidget = () => <DriverMetric kind="active" />;
export const DriverUnassignedWidget = () => <DriverMetric kind="unassigned" />;
export const DriverMissingWidget = () => <DriverMetric kind="missing" />;
export const DriverChecksWidget = () => <DriverMetric kind="checks" />;
