import { CalendarDays } from "lucide-react";
import { previousDay } from "../model/trip-day";

export function TripDayPicker({
  value,
  today,
  onChange,
  label,
}: {
  value: string;
  today: string;
  onChange: (day: string) => void;
  label: string;
}) {
  return (
    <div className="trip-day-picker" role="group" aria-label={label}>
      <div className="trip-day-shortcuts">
        {[
          { name: "Dzisiaj", day: today },
          { name: "Wczoraj", day: previousDay(today) },
        ].map(({ name, day }) => (
          <button
            key={name}
            className="button button-secondary"
            aria-pressed={value === day}
            onClick={() => onChange(day)}
          >
            {name}
          </button>
        ))}
      </div>
      <label className="trip-day-calendar">
        <CalendarDays size={15} aria-hidden="true" />
        <input
          type="date"
          aria-label={label}
          value={value}
          max={today}
          required
          onChange={(event) => onChange(event.target.value)}
        />
      </label>
    </div>
  );
}
