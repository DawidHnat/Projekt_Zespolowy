import type { Summary } from "../../fleet/model/types.ts";

export function fleetUtilization(summary: Summary | null) {
  if (!summary) return null;
  const { total, moving, stopped, offline, unknown } = summary;
  if (![total, moving, stopped, offline, unknown].every(value => Number.isSafeInteger(value) && value >= 0)
    || moving + stopped + offline + unknown !== total) return null;
  const others = offline + unknown;
  const current = summary.source?.status === "ok" && moving + stopped > 0;
  const share = total ? moving / total * 100 : 0;
  return {
    total, moving, stopped, others, current,
    movingShare: current ? share : 0,
    stoppedEnd: current ? (moving + stopped) / total * 100 : 0,
    percentage: total === 0 ? "0" : !current ? "—"
      : share > 0 && share < 1 ? "<1%" : `${Math.round(share)}%`,
    label: total === 0 ? "Pojazdów" : !current ? "Brak statusów" : "w ruchu",
  };
}
