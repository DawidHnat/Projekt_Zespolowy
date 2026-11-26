export const ENTITY_LABELS: Record<string, string> = {
  vehicle: "Kartoteka pojazdu",
  vehicle_odometer: "Przebieg ręczny",
  vehicle_document: "Dokument / zdjęcie pojazdu",
  driver: "Kartoteka kierowcy",
  driver_assignment: "Przypisanie kierowcy",
  trip_annotation: "Adnotacja podróży",
  user_account: "Konto użytkownika",
  user_session: "Sesja i uwierzytelnianie",
};

export const OPERATION_LABELS: Record<string, string> = {
  "vehicle.created": "Dodano pojazd ręczny",
  "vehicle.updated": "Zaktualizowano kartotekę pojazdu",
  "vehicle.archived": "Zarchiwizowano pojazd",
  "vehicle.restored": "Przywrócono pojazd z archiwum",
  "vehicle.source_linked": "Połączono pojazd ręczny z WEBFLEET",
  "vehicle.imported": "Zaimportowano dane z WEBFLEET",
  "vehicle.odometer_updated": "Zapisano ręczny odczyt przebiegu",
  "vehicle.document_dates_updated": "Zmieniono terminy badań / OC",
  "vehicle.document_uploaded": "Dodano skan dokumentu pojazdu",
  "vehicle.document_replaced": "Podmieniono skan dokumentu pojazdu",
  "vehicle.document_deleted": "Usunięto skan dokumentu pojazdu",
  "vehicle.photo_updated": "Zaktualizowano zdjęcie pojazdu",
  "vehicle.photo_deleted": "Usunięto zdjęcie pojazdu",
  "driver.created": "Dodano kierowcę",
  "driver.updated": "Zaktualizowano dane kierowcy",
  "driver_assignment.created": "Przypisano kierowcę do pojazdu",
  "driver_assignment.closed": "Zakończono przypisanie kierowcy",
  "trip_annotation.updated": "Zaktualizowano ewidencję przejazdu",
  "auth.login_succeeded": "Zalogowano do aplikacji",
  "auth.login_failed": "Odrzucono próbę logowania",
  "auth.logout": "Wylogowano sesję",
  "auth.sessions_revoked": "Unieważniono wszystkie aktywne sesje",
  "auth.password_changed": "Zmieniono hasło konta",
  "auth.password_reset_confirmed": "Potwierdzono reset hasła",
};

export const FIELD_LABELS: Record<string, string> = {
  origin: "Pochodzenie",
  name: "Nazwa",
  number: "Numer obiektu",
  license_plate: "Rejestracja",
  vehicle_type: "Typ pojazdu",
  make: "Marka",
  model: "Model",
  year: "Rok produkcji",
  vin: "VIN",
  fuel_type: "Paliwo",
  leasing_company: "Leasingodawca",
  leasing_contract_no: "Nr umowy leasingu",
  leasing_end_on: "Koniec leasingu",
  inspection_due_on: "Badanie techniczne",
  insurance_due_on: "Ważność OC",
  manual_odometer_km: "Przebieg ręczny (km)",
  manual_odometer_date: "Data odczytu przebiegu",
  gross_weight_kg: "DMC (kg)",
  passenger_seats: "Miejsca pasażerskie",
  tows_heavy_trailer: "Przyczepa ciężka (+E)",
  required_category_override: "Wymagana kat. (wyjątek)",
  archived: "W archiwum",
  archived_reason: "Powód archiwizacji",
  driver_id: "Kierowca (ID)",
  vehicle_id: "Pojazd (ID)",
  kind: "Rodzaj załącznika",
  mime_type: "Typ pliku",
  size_bytes: "Rozmiar (B)",
  scan_status: "Status skanera",
  version: "Wersja",
  deleted: "Usunięto",
  display_name: "Nazwa wyświetlana",
  first_name: "Imię",
  last_name: "Nazwisko",
  identifier: "Identyfikator",
  active: "Aktywny",
  categories: "Kategorie prawa jazdy",
  phone_configured: "Telefon skonfigurowany",
  email_configured: "E-mail skonfigurowany",
  started_at: "Początek przypisania",
  ended_at: "Koniec przypisania",
  purpose: "Cel przejazdu",
  description: "Opis przejazdu",
  role: "Rola",
  password_changed: "Zmiana hasła",
  password_reset: "Reset hasła",
  action: "Zdarzenie sesji",
  revoked_all: "Wylogowano wszystkie sesje",
};

export function formatAuditTimestamp(value: string): string {
  return new Intl.DateTimeFormat("pl-PL", {
    timeZone: "Europe/Warsaw",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

export function formatAuditValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "brak";
  if (typeof value === "boolean") return value ? "tak" : "nie";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "brak";
  return String(value);
}

export function formatActorLabel(
  actorType: string,
  actor: { id: string; display_name: string } | null | undefined,
): string {
  if (actorType === "import") return "Import WEBFLEET";
  if (actorType === "system") return "System";
  return actor?.display_name || "Użytkownik";
}
