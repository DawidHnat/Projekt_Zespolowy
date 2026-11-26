export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
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
    try {
      const error = (await response.json()).error;
      code = error?.code || code;
    } catch {
      /* Non-JSON proxy failure. */
    }
    const messages: Record<string, string> = {
      SOURCE_UNAVAILABLE: "Oczekiwanie na pierwszy odczyt WEBFLEET.",
      INVALID_CREDENTIALS: "Niepoprawny login lub hasło.",
      RATE_LIMITED: "Zbyt wiele prób. Spróbuj ponownie za minutę.",
      UNAUTHENTICATED: "Sesja wygasła. Zaloguj się ponownie.",
      INVALID_RESET: "Link jest niepoprawny lub wygasł. Poproś o nowy link.",
      DATABASE_UNAVAILABLE: "Baza danych jest chwilowo niedostępna.",
      VERSION_CONFLICT:
        "Ustawienia zmieniły się na innym urządzeniu. Wybierz, którą wersję zachować.",
      PAYLOAD_TOO_LARGE: "Wybrane tło przekracza dozwolony limit 8 MB.",
      IMAGE_NOT_FOUND: "Zapisane tło nie jest już dostępne na koncie.",
      UNSUPPORTED_MEDIA_TYPE: "Nie udało się przygotować obrazu WebP. Wybierz inne zdjęcie.",
      INVALID_CONTENT_LENGTH: "Nie udało się odczytać rozmiaru wybranego pliku.",
      IMAGE_ID_CONFLICT: "Nie udało się powiązać obrazu z tym kontem. Spróbuj ponownie.",
    };
    throw new ApiError(
      response.status,
      code,
      messages[code] || "Nie udało się pobrać danych. Spróbuj ponownie.",
    );
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
