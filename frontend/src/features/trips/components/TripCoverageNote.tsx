import type { TripCoverage } from "../../../shared/api/generated/contracts";

export function TripCoverageNote({ coverage }: { coverage: TripCoverage | null }) {
  if (!coverage) return null;
  const { state, covered_days, requested_days, failed_days } = coverage;
  if (state === "unavailable") {
    return <p className="trip-time-hint">Raporty źródła za ten okres nie zostały pobrane.</p>;
  }
  return <p className="trip-time-hint">
    Raporty według daty zakończenia przejazdu: {covered_days.length} z {requested_days} dni.
    {failed_days.length > 0 && ` Nieudane próby: ${failed_days.length}.`}
  </p>;
}
