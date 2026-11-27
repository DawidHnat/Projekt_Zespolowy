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
      value: summary?.assignments_to_check?.total ?? undefined,
      filter: { active: "active", compatibility: "attention" },
    },
  } as const;
  const item = config[kind];
  const checks = summary?.assignments_to_check;
  const checksBreakdown = checks?.by_reason
    ? [
        checks.by_reason.category_mismatch
          ? `niezgodna kat.: ${checks.by_reason.category_mismatch}`
          : null,
        checks.by_reason.missing_driver_categories
          ? `brak kat.: ${checks.by_reason.missing_driver_categories}`
          : null,
        checks.by_reason.missing_vehicle_dmc
          ? `brak DMC: ${checks.by_reason.missing_vehicle_dmc}`
          : null,
        checks.by_reason.missing_passenger_seats
          ? `brak miejsc: ${checks.by_reason.missing_passenger_seats}`
          : null,
        checks.by_reason.missing_vehicle_requirements
          ? `brak wymogów: ${checks.by_reason.missing_vehicle_requirements}`
          : null,
      ]
        .filter(Boolean)
        .join(" · ")
    : "";
  return (
    <WidgetFrame title={item.title} icon={item.icon} className="driver-metric">
      {kind === "checks" ? (
        <>
          <p className="driver-metric-value">{checks?.total ?? "—"}</p>
          <p>
            {checks && checks.total > 0
              ? `Niezgodne: ${checks.incompatible} · Niezweryfikowane: ${checks.unverified}${checksBreakdown ? ` (${checksBreakdown})` : ""}. Brak danych nie potwierdza uprawnień.`
              : "Brak aktywnych relacji z niezgodnością lub luką danych. Brak danych nie potwierdza uprawnień."}
          </p>
          <button
            className="button button-secondary"
            disabled={!summary || editing}
            onClick={() => drivers.change(item.filter)}
          >
            Pokaż osoby
          </button>
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
