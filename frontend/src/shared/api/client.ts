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
    try {
      code = (await response.json()).error?.code || code;
    } catch {
      /* Non-JSON proxy failure. */
    }
    const messages: Record<string, string> = {
      SOURCE_UNAVAILABLE: "Oczekiwanie na pierwszy odczyt WEBFLEET.",
      INVALID_CREDENTIALS: "Niepoprawny login lub hasło.",
      RATE_LIMITED: "Zbyt wiele prób. Spróbuj ponownie za minutę.",
      UNAUTHENTICATED: "Sesja wygasła. Zaloguj się ponownie.",
      INVALID_RESET: "Link jest niepoprawny lub wygasł. Poproś o nowy link.",
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
    };
    throw new ApiError(
      response.status,
      code,
      messages[code] || "Nie udało się pobrać danych. Spróbuj ponownie.",
    );
  }
  return response.json() as Promise<T>;
}
