const CORRELATION_ID = /^[A-Za-z0-9._-]{8,64}$/;

export function validCorrelationId(value: unknown): string | null {
  return typeof value === "string" && CORRELATION_ID.test(value) ? value : null;
}

export class ApiError extends Error {
  status: number;
  code: string;
  correlationId: string | null;
  fields: Record<string, string>;
  constructor(
    status: number,
    code: string,
    message: string,
    correlationId: string | null = null,
    fields: Record<string, string> = {},
  ) {
    super(message);
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
    this.fields = fields;
  }
}
const expiredListeners = new Set<() => void>();
// A response from the previous account must not expire its replacement session.
let sessionVersion = 0;

export function advanceSessionVersion() {
  sessionVersion += 1;
}

export function onSessionExpired(listener: () => void) {
  expiredListeners.add(listener);
  return () => {
    expiredListeners.delete(listener);
  };
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
  notifyExpiry = true,
): Promise<T> {
  if (!path.startsWith("/") || path.startsWith("//"))
    throw new Error("Invalid API path");
  const requestedSession = sessionVersion;
  const response = await fetch(`/api/v1${path}`, {
    ...options,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    if (
      response.status === 401 && notifyExpiry &&
      requestedSession === sessionVersion && !options.signal?.aborted
    )
      expiredListeners.forEach((listener) => listener());
    let code = "UNAVAILABLE";
    let fields: Record<string, string> = {};
    let bodyCorrelationId: string | null = null;
    try {
      const payload = await response.json();
      code = payload.error?.code || code;
      if (payload.error?.fields && typeof payload.error.fields === "object")
        fields = payload.error.fields as Record<string, string>;
      bodyCorrelationId = validCorrelationId(payload.error?.correlation_id);
    } catch {
      /* Non-JSON proxy failure. */
    }
    const correlationId =
      validCorrelationId(response.headers.get("X-Correlation-ID")) ?? bodyCorrelationId;
    const messages: Record<string, string> = {
      SOURCE_UNAVAILABLE: "Oczekiwanie na pierwszy odczyt WEBFLEET.",
      INVALID_CREDENTIALS: "Niepoprawny login lub hasło.",
      RATE_LIMITED: "Zbyt wiele prób. Spróbuj ponownie za minutę.",
      UNAUTHENTICATED: "Sesja wygasła. Zaloguj się ponownie.",
      INVALID_RESET: "Link jest niepoprawny lub wygasł. Poproś o nowy link.",
      DATABASE_UNAVAILABLE: "Baza danych jest chwilowo niedostępna.",
      VEHICLE_ARCHIVED: "Pojazd jest zarchiwizowany. Przywróć go przed wykonaniem tej operacji.",
      ALREADY_ARCHIVED: "Pojazd znajduje się już w archiwum.",
      NOT_ARCHIVED: "Pojazd nie znajduje się w archiwum.",
      DUPLICATE_VEHICLE_IDENTITY: "Numer rejestracyjny lub VIN jest już przypisany do innego pojazdu w kartotece.",
      SOURCE_VEHICLE_EXISTS: "Wykryto istniejący pojazd WEBFLEET o tej samej rejestracji lub VIN.",
      ALREADY_LINKED: "Pojazd jest już powiązany ze źródłem WEBFLEET.",
      NOT_SOURCE_VEHICLE: "Wskazany rekord nie jest pojazdem WEBFLEET.",
      IDENTITY_MISMATCH: "Wskazany pojazd WEBFLEET ma niezgodną rejestrację lub sprzeczny numer VIN.",
      LINK_CONFLICT: "Nie udało się bezpiecznie połączyć historii wybranego pojazdu.",
    };
    const baseMessage = messages[code] || "Nie udało się pobrać danych. Spróbuj ponownie.";
    const displayMessage =
      response.status >= 500 && code !== "SOURCE_UNAVAILABLE" && correlationId
        ? `${baseMessage} (ID zgłoszenia: ${correlationId})`
        : baseMessage;
    throw new ApiError(response.status, code, displayMessage, correlationId, fields);
  }
  return response.json() as Promise<T>;
}
