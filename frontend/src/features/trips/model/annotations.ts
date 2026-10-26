import { validTripDay } from "./trip-day.ts";

export type Annotation = {
  purpose: string | null;
  description: string | null;
  version: number;
  updated_at: string | null;
  updated_by: { id: string; display_name: string } | null;
};
export type Trip = {
  id: string;
  vehicle_id: string;
  start_at: string;
  end_at: string | null;
  distance_km: number | null;
  duration_seconds: number | null;
  annotation: Annotation;
};
export type TripList = { items: Trip[]; total: number; page: number; page_size: number };
export type AnnotationDraft = { purpose: string; description: string };

export const annotationDraft = (value: Annotation): AnnotationDraft => ({
  purpose: value.purpose ?? "",
  description: value.description ?? "",
});
export function annotationValidation(draft: AnnotationDraft): string | null {
  if (Array.from(draft.purpose).length > 200) return "Cel może mieć najwyżej 200 znaków.";
  if (Array.from(draft.description).length > 2000) return "Opis może mieć najwyżej 2000 znaków.";
  if (/[\r\n]/.test(draft.purpose)) return "Cel wpisz w jednym wierszu.";
  if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f\ud800-\udfff]/u.test(draft.purpose + draft.description))
    return "Usuń niedozwolone znaki z notatki.";
  return null;
}

const offsetFormat = new Intl.DateTimeFormat("en-US", {
  timeZone: "Europe/Warsaw", timeZoneName: "longOffset",
});
function midnightUtc(day: string): string {
  const wall = Date.parse(`${day}T00:00:00Z`);
  let instant = wall;
  for (let i = 0; i < 3; i++) {
    const offset = offsetFormat.formatToParts(new Date(instant)).find(p => p.type === "timeZoneName")!.value;
    const match = /^GMT([+-])(\d\d):(\d\d)(?::(\d\d))?$/.exec(offset);
    if (!match) throw new Error("Nie można ustalić polskiej strefy czasu.");
    const seconds = (Number(match[2]) * 3600 + Number(match[3]) * 60 + Number(match[4] ?? 0)) * (match[1] === "+" ? 1 : -1);
    const next = wall - seconds * 1000;
    if (next === instant) break;
    instant = next;
  }
  return new Date(instant).toISOString();
}
export function tripDayRange(day: string): { from: string; to: string } {
  if (!validTripDay(day)) throw new Error("Niepoprawna data.");
  const following = new Date(`${day}T12:00:00Z`);
  following.setUTCDate(following.getUTCDate() + 1);
  return { from: midnightUtc(day), to: midnightUtc(following.toISOString().slice(0, 10)) };
}
export function tripListPath(vehicleId: string, day: string, page: number, pageSize: number): string {
  return `/trips?${new URLSearchParams({ vehicle_id: vehicleId, ...tripDayRange(day), page: String(page), page_size: String(pageSize) })}`;
}
export function annotationError(error: unknown): string {
  const code = error && typeof error === "object" && "code" in error ? error.code : null;
  if (code === "VERSION_CONFLICT") return "Ktoś zmienił tę notatkę. Twój tekst pozostał w formularzu. Sprawdź bieżącą wersję przed ponownym zapisem.";
  if (code === "FORBIDDEN") return "Nie masz uprawnień do zapisu. Twój tekst pozostał w formularzu.";
  if (code === "VALIDATION_ERROR") return "Sprawdź cel i opis. Twój tekst pozostał w formularzu.";
  if (code === "NOT_FOUND") return "Ten przejazd nie jest już dostępny. Twój tekst pozostał w formularzu.";
  return "Nie udało się potwierdzić zapisu. Twój tekst pozostał w formularzu. Spróbuj ponownie.";
}
