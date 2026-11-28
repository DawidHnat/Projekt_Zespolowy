export interface OilChangeIntervalInput {
  // Odometer readings and the interval use kilometres with one decimal place.
  lastChangeOdometerKm?: number | null;
  currentOdometerKm?: number | null;
  lastChangeDay?: string | null;
  currentDay?: string | null;
  intervalKm?: number;
  intervalDays?: number;
}

type Warning =
  | "invalid_interval_km"
  | "invalid_interval_days"
  | "invalid_odometer"
  | "odometer_before_last_change"
  | "invalid_calendar_day"
  | "day_before_last_change";

export interface OilChangeIntervalResult {
  remainingKm: number | null;
  remainingDays: number | null;
  status: "in_time" | "due" | "overdue" | "insufficient_data";
  warnings: Warning[];
}

const MILLISECONDS_PER_DAY = 86_400_000;
// Fleet odometer values use Numeric(14, 1). Compare whole tenths of a kilometre.
const ODOMETER_UNITS_PER_KM = 10;

function odometerUnits(km: number): number {
  const units = Math.round(km * ODOMETER_UNITS_PER_KM);
  return Number.isSafeInteger(units) && units >= 0 && units / ODOMETER_UNITS_PER_KM === km
    ? units
    : NaN;
}

// Input is already a Warsaw calendar day. UTC midnight is used only to assign
// each civil date an ordinal, so 23- and 25-hour days count as one day.
function calendarDayNumber(value: string): number {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith("0000")) return NaN;
  const date = new Date(`${value}T00:00:00Z`);
  if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0, 10) !== value) return NaN;
  return date.getTime() / MILLISECONDS_PER_DAY;
}

export function calculateOilChangeInterval({
  lastChangeOdometerKm,
  currentOdometerKm,
  lastChangeDay,
  currentDay,
  intervalKm = 10_000,
  intervalDays = 365,
}: OilChangeIntervalInput): OilChangeIntervalResult {
  const warnings: Warning[] = [];
  const kmInterval = odometerUnits(intervalKm);
  const validKmInterval = kmInterval > 0;
  const validDayInterval = Number.isSafeInteger(intervalDays) && intervalDays > 0;
  if (!validKmInterval) warnings.push("invalid_interval_km");
  if (!validDayInterval) warnings.push("invalid_interval_days");

  const lastOdometer = lastChangeOdometerKm == null ? null : odometerUnits(lastChangeOdometerKm);
  const currentOdometer = currentOdometerKm == null ? null : odometerUnits(currentOdometerKm);
  let remainingKm: number | null = null;
  if (Number.isNaN(lastOdometer) || Number.isNaN(currentOdometer)) {
    warnings.push("invalid_odometer");
  } else if (lastOdometer !== null && currentOdometer !== null) {
    if (currentOdometer < lastOdometer) {
      warnings.push("odometer_before_last_change");
    } else if (validKmInterval) {
      remainingKm = (kmInterval - (currentOdometer - lastOdometer)) / ODOMETER_UNITS_PER_KM;
    }
  }

  const lastDay = lastChangeDay == null ? null : calendarDayNumber(lastChangeDay);
  const today = currentDay == null ? null : calendarDayNumber(currentDay);
  let remainingDays: number | null = null;
  if (Number.isNaN(lastDay) || Number.isNaN(today)) {
    warnings.push("invalid_calendar_day");
  } else if (lastDay !== null && today !== null) {
    if (today < lastDay) {
      warnings.push("day_before_last_change");
    } else if (validDayInterval) {
      remainingDays = intervalDays - (today - lastDay);
    }
  }

  let status: OilChangeIntervalResult["status"] = "insufficient_data";
  if ([remainingKm, remainingDays].some(value => value !== null && value < 0)) {
    status = "overdue";
  } else if (remainingKm === 0 || remainingDays === 0) {
    status = "due";
  } else if (remainingKm !== null && remainingDays !== null) {
    status = "in_time";
  }
  return { remainingKm, remainingDays, status, warnings };
}
