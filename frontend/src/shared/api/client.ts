const CORRELATION_ID = /^[A-Za-z0-9._-]{8,64}$/;

export function validCorrelationId(value: unknown): string | null {
  return typeof value === "string" && CORRELATION_ID.test(value) ? value : null;
}

export class ApiError extends Error {
  status: number;
  code: string;
  correlationId: string | null;
  constructor(
    status: number,
    code: string,
    message: string,
    correlationId: string | null = null,
  ) {
    super(message);
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
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

export async function apiResponse(
  path: string,
  options: RequestInit = {},
  notifyExpiry = true,
): Promise<Response> {
  if (!path.startsWith("/") || path.startsWith("//"))
    throw new Error("Invalid API path");
  const requestedSession = sessionVersion;
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body !== undefined)
    headers.set("Content-Type", "application/json");
  const response = await fetch(`/api/v1${path}`, {
    ...options,
    credentials: "same-origin",
    headers,
  });
  if (!response.ok) {
    if (
      response.status === 401 && notifyExpiry &&
      requestedSession === sessionVersion && !options.signal?.aborted
    )
      expiredListeners.forEach((listener) => listener());
    let code = "UNAVAILABLE";
    let bodyCorrelationId: string | null = null;
    try {
      const payload = await response.json();
      code = payload.error?.code || code;
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
      INVALID_CURRENT_PASSWORD: "Aktualne hasło jest niepoprawne.",
      EMAIL_UNCHANGED: "Wpisz adres inny niż aktualny.",
      EMAIL_CONFIRMATION_UNAVAILABLE: "Wysyłka linku jest chwilowo niedostępna. Spróbuj ponownie później.",
      EMAIL_CONFIRMATION_FAILED: "Nie udało się wysłać linku. Spróbuj ponownie.",
      INVALID_EMAIL_CONFIRMATION: "Link jest niepoprawny lub wygasł. Poproś o nowy link w Profilu.",
      INVALID_ACTIVATION: "Link jest niepoprawny lub wygasł. Poproś administratora o nowe zaproszenie.",
      ACCOUNT_IDENTIFIER_TAKEN: "Login lub adres e-mail jest już używany.",
      ACCOUNT_VERSION_CONFLICT: "Konto zmieniono. Wczytaj jego aktualne dane i spróbuj ponownie.",
      ACCOUNT_ACTIVATION_REQUIRED: "Użytkownik musi ustawić pierwsze hasło z linku aktywacyjnego.",
      ACCOUNT_ALREADY_ACTIVATED: "To konto zostało już aktywowane.",
      ACCOUNT_INVITE_UNAVAILABLE: "Zaproszenie wymaga oczekującego konta z adresem e-mail.",
      ACTIVATION_MAIL_UNAVAILABLE: "Poczta SMTP wymaga konfiguracji. Konto jest gotowe do ponowienia zaproszenia.",
      ACTIVATION_MAIL_FAILED: "Nie udało się wysłać zaproszenia. Spróbuj ponownie.",
      LAST_ADMIN: "Zachowaj co najmniej jednego aktywnego administratora.",
      DATABASE_UNAVAILABLE: "Baza danych jest chwilowo niedostępna.",
      VERSION_CONFLICT:
        "Ustawienia zmieniły się na innym urządzeniu. Wybierz, którą wersję zachować.",
      PAYLOAD_TOO_LARGE: "Wybrane tło przekracza dozwolony limit 8 MB.",
      IMAGE_NOT_FOUND: "Zapisane tło nie jest już dostępne na koncie.",
      UNSUPPORTED_MEDIA_TYPE: "Nie udało się przygotować obrazu WebP. Wybierz inne zdjęcie.",
      INVALID_CONTENT_LENGTH: "Nie udało się odczytać rozmiaru wybranego pliku.",
      IMAGE_ID_CONFLICT: "Nie udało się powiązać obrazu z tym kontem. Spróbuj ponownie.",
    };
    const baseMessage = messages[code] || "Nie udało się pobrać danych. Spróbuj ponownie.";
    const displayMessage =
      response.status >= 500 && code !== "SOURCE_UNAVAILABLE" && correlationId
        ? `${baseMessage} (ID zgłoszenia: ${correlationId})`
        : baseMessage;
    throw new ApiError(response.status, code, displayMessage, correlationId);
  }
  return response;
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
  notifyExpiry = true,
): Promise<T> {
  return apiResponse(path, options, notifyExpiry).then(
    (response) => response.json() as Promise<T>,
  );
}
