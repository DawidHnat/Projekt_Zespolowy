const zone = "Europe/Warsaw";
const calendar = new Intl.DateTimeFormat("en-CA", {
  timeZone: zone,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

export function warsawDay(now = new Date()): string {
  const parts = calendar.formatToParts(now);
  return ["year", "month", "day"]
    .map((type) => parts.find((part) => part.type === type)!.value)
    .join("-");
}

export function validTripDay(day: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) return false;
  const date = new Date(`${day}T12:00:00Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === day;
}

export function previousDay(day: string): string {
  if (!validTripDay(day)) throw new Error("Invalid calendar day");
  const date = new Date(`${day}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() - 1);
  return date.toISOString().slice(0, 10);
}

export function tripDayLabel(day: string, today: string): string {
  if (day === today) return "Dzisiaj";
  if (day === previousDay(today)) return "Wczoraj";
  return new Intl.DateTimeFormat("pl-PL", {
    timeZone: zone,
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(`${day}T12:00:00Z`));
}
