export type Profile = {
  display_name: string;
  username: string;
  email: string | null;
  role: string;
};

export function passwordChangeValidation(current: string, next: string, confirmation: string): string | null {
  if (!current) return "Wpisz aktualne hasło.";
  if (Array.from(next).length < 12) return "Nowe hasło musi mieć co najmniej 12 znaków.";
  if (Array.from(current).length > 1024 || Array.from(next).length > 1024)
    return "Hasło może mieć najwyżej 1024 znaki.";
  if (next !== confirmation) return "Nowe hasła muszą być zgodne.";
  if (next === current) return "Wybierz inne nowe hasło.";
  return null;
}

export function profileError(error: unknown): string {
  const code = error && typeof error === "object" && "code" in error ? error.code : null;
  if (code === "INVALID_CURRENT_PASSWORD") return "Aktualne hasło jest niepoprawne. Wpisz hasła ponownie.";
  if (code === "PASSWORD_UNCHANGED") return "Wybierz inne nowe hasło.";
  if (code === "RATE_LIMITED") return "Zbyt wiele prób. Spróbuj ponownie za 15 minut.";
  if (code === "VALIDATION_ERROR") return "Sprawdź pola formularza i wpisz hasła ponownie.";
  return "Nie udało się potwierdzić operacji. Sprawdź połączenie i spróbuj ponownie.";
}

export function profileRole(role: string): string {
  switch (role) {
    case "admin": return "Administrator";
    case "editor": return "Edytor";
    case "viewer": return "Tylko odczyt";
    default: return "Nieznana rola";
  }
}
