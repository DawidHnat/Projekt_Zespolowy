import { DatePicker } from "../../../shared/components/DatePicker";
import { previousDay } from "../model/trip-day";

export function TripDayPicker({
  value,
  today,
  onChange,
  label,
  disabled = false,
}: {
  value: string;
  today: string;
  onChange: (day: string) => void;
  label: string;
  disabled?: boolean;
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
            disabled={disabled}
            onClick={() => onChange(day)}
          >
            {name}
          </button>
        ))}
      </div>
      <DatePicker
        value={value}
        maxDate={today}
        required
        label={label}
        disabled={disabled}
        onChange={onChange}
      />
    </div>
  );
}
