import { api } from "./client";

export type PreferenceModule = "dashboard" | "vehicles";
export type AccountPreference<T> = {
  module: PreferenceModule;
  version: number;
  value: T | null;
  updated_at: string | null;
};

export function readAccountPreference<T>(
  module: PreferenceModule,
  signal?: AbortSignal,
) {
  return api<AccountPreference<T>>(`/preferences/${module}`, { signal });
}

export function writeAccountPreference<T>(
  module: PreferenceModule,
  version: number,
  value: T,
) {
  return api<AccountPreference<T>>(`/preferences/${module}`, {
    method: "PUT",
    body: JSON.stringify({ version, value }),
  });
}
