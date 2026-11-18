import { positionAge, updateTime } from "../model/types";

export function VehiclePositionTime({ value }: { value: string | null }) {
  if (!value || !Number.isFinite(Date.parse(value)))
    return <span>Brak czasu pozycji</span>;
  return (
    <time dateTime={value} title={`Pomiar GPS: ${updateTime(value)} · czas polski`}>
      {positionAge(value)}
    </time>
  );
}
