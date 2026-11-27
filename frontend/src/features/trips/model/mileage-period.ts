import { validTripDay, warsawDay } from "./trip-day.ts";

// Must match the backend limit of GET /trips/mileage (inclusive day count).
export const MAX_PERIOD_DAYS = 93;

/** Current month up to today, as Warsaw calendar days (YYYY-MM-DD). */
export function initialPeriod(now = new Date()) {
  const today = warsawDay(now);
  return { from: `${today.slice(0, 7)}-01`, through: today };
}

/** Inclusive number of calendar days, or null for an invalid day. */
export function periodDays(from: string, through: string): number | null {
  if (!validTripDay(from) || !validTripDay(through)) return null;
  const start = Date.parse(`${from}T12:00:00Z`);
  const end = Date.parse(`${through}T12:00:00Z`);
  return Math.round((end - start) / 86_400_000) + 1;
}

/** Message for the user, or an empty string when the period can be read. */
export function periodError(from: string, through: string): string {
  const days = periodDays(from, through);
  if (days === null) return "Wybierz prawidłowe daty okresu.";
  if (days < 1) return "Data początkowa nie może być późniejsza niż końcowa.";
  if (days > MAX_PERIOD_DAYS)
    return `Okres może obejmować najwyżej ${MAX_PERIOD_DAYS} dni (wybrano ${days}). Skróć zakres dat.`;
  return "";
}
