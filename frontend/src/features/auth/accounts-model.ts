export const accountRoles = {
  admin: "Administrator",
  editor: "Kierownik floty",
  viewer: "Użytkownik",
} as const;

export const accountStatuses = {
  pending: "Oczekujące",
  active: "Aktywne",
  inactive: "Nieaktywne",
  blocked: "Zablokowane",
} as const;

export type AccountRole = keyof typeof accountRoles;
export type AccountStatus = keyof typeof accountStatuses;
export type Account = {
  id: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  display_name: string;
  email: string | null;
  role: AccountRole;
  status: AccountStatus;
  needs_activation: boolean;
  version: number;
};

export type AccountsPage = {
  items: Account[];
  page: number;
  page_size: number;
  total: number;
};
