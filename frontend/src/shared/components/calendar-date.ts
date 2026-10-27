/** Calendar dates are local civil days, never instants converted through UTC. */
export function calendarDate(value: string): Date | undefined {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return undefined;
  const [year, month, day] = value.split("-").map(Number);
  if (year < 1) return undefined;
  const date = new Date(0);
  date.setFullYear(year, month - 1, day);
  date.setHours(12, 0, 0, 0);
  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day
    ? date
    : undefined;
}

export function calendarValue(date: Date): string {
  return [date.getFullYear().toString().padStart(4, "0"),
    (date.getMonth() + 1).toString().padStart(2, "0"),
    date.getDate().toString().padStart(2, "0")].join("-");
}

export function displayCalendarDate(value: string): string {
  return calendarDate(value) ? value.split("-").reverse().join(".") : "";
}

export function calendarInputValue(text: string): string | undefined {
  if (!text.trim()) return "";
  const parts = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(text.trim());
  const value = parts ? `${parts[3]}-${parts[2]}-${parts[1]}` : "";
  return calendarDate(value) ? value : undefined;
}

export function calendarInputError(
  text: string,
  { required = false, minDate, maxDate }: { required?: boolean; minDate?: string; maxDate?: string },
): string {
  if (!text.trim()) return required ? "Wybierz datę." : "";
  const value = calendarInputValue(text);
  if (!value) return "Wpisz poprawną datę w formacie DD.MM.RRRR.";
  if (minDate && value < minDate) return `Najwcześniejsza data: ${displayCalendarDate(minDate)}.`;
  if (maxDate && value > maxDate) return `Najpóźniejsza data: ${displayCalendarDate(maxDate)}.`;
  return "";
}
