import { CircleGauge } from "lucide-react";
import type { CSSProperties } from "react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { useFleet } from "../../fleet/model/FleetProvider";
import { updateTime } from "../../fleet/model/types";
import { fleetUtilization } from "../model/utilization";

export function UtilizationWidget() {
  const fleet = useFleet();
  const values = fleetUtilization(fleet.summary);
  const caption = !values
    ? fleet.loading ? "Pobieranie stanu floty…" : "Nie można pobrać stanu floty."
    : fleet.error ? "Pokazujemy ostatni poprawny odczyt."
    : fleet.summary?.source.status === "degraded" ? "Źródło jest niedostępne. Statusy niepotwierdzone."
    : values.total === 0 ? "We flocie nie ma jeszcze pojazdów."
    : "Bieżący stan całej floty. Pozostałe: starsze lub brakujące pomiary.";
  return (
    <WidgetFrame
      title="Wykorzystanie floty"
      icon={CircleGauge}
      className="utilization-widget"
      badge={fleet.error || fleet.summary?.source.status === "degraded"
        ? "Ostatni odczyt" : "Bieżący stan"}
    >
      <div className="utilization-body">
        <div className={`empty-gauge fleet-gauge ${values?.current ? "has-values" : ""}`}
          style={values ? { "--moving-share": `${values.movingShare}%`,
            "--stopped-end": `${values.stoppedEnd}%` } as CSSProperties : undefined}
          role="img"
          aria-label={values ? `Stan floty: ${values.moving} w ruchu, ${values.stopped} na postoju, ${values.others} pozostałe`
            : "Brak danych o stanie floty"}
        >
          <span>
            {values?.percentage ?? "—"}<small>{values?.label ?? "Brak danych"}</small>
          </span>
        </div>
        <ul className="gauge-legend">
          <li>
            <i className="legend-dot success-dot" />W ruchu <span>{values?.moving ?? "—"}</span>
          </li>
          <li>
            <i className="legend-dot warning-dot" />
            Na postoju <span>{values?.stopped ?? "—"}</span>
          </li>
          <li>
            <i className="legend-dot muted-dot" />
            Pozostałe <span>{values?.others ?? "—"}</span>
          </li>
        </ul>
      </div>
      <p className="widget-footnote">
        {caption}
        {values && fleet.summary?.source.last_success_at && <><br />Odczyt: {updateTime(fleet.summary.source.last_success_at)}.</>}
      </p>
    </WidgetFrame>
  );
}
