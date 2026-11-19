import {
  createContext,
  useContext,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  defaultPreferences,
  parsePreferences,
  STORAGE_KEY,
  LEGACY_STORAGE_KEY,
} from "./preference-model";
import type { WidgetId } from "../features/dashboard/model/widget-types";
import { useAuth } from "../features/auth/AuthProvider";
import {
  readAccountPreference,
  writeAccountPreference,
  type AccountPreference,
} from "../shared/api/account-preferences";
import { ApiError } from "../shared/api/client";
import { normalizeLayouts } from "../features/dashboard/model/widget-layout";

export { ACCENT_PRESETS, defaultPreferences } from "./preference-model";
export type {
  DashboardPreferences,
  ThemeMode,
  Arrangement,
} from "./preference-model";

type DashboardPreferences = ReturnType<typeof defaultPreferences>;
const MIGRATION_STORAGE_KEY = "fleet-flow.dashboard.account-migration.v1";
export type DashboardArrangement = {
  visibleWidgets: WidgetId[];
  layouts: { dashboard: DashboardPreferences["layouts"]["dashboard"] };
};
type MigrationState = {
  ownerId: string;
  completed: boolean;
  candidate?: DashboardArrangement;
};
type DashboardCloudState = {
  loading: boolean;
  saving: boolean;
  version: number;
  error: string | null;
  migrationAvailable: boolean;
  conflict: AccountPreference<DashboardArrangement> | null;
};
type DashboardPreferencesState = ReturnType<typeof useDashboardPreferencesState>;
const Context = createContext<DashboardPreferencesState | null>(null);

function readPreferences() {
  try {
    return parsePreferences(
      localStorage.getItem(STORAGE_KEY) ??
        localStorage.getItem(LEGACY_STORAGE_KEY),
    );
  } catch {
    return defaultPreferences();
  }
}

function hasLocalPreferences() {
  try {
    return Boolean(
      localStorage.getItem(STORAGE_KEY) ?? localStorage.getItem(LEGACY_STORAGE_KEY),
    );
  } catch {
    return false;
  }
}

function readMigrationState(): MigrationState | null {
  try {
    const value: unknown = JSON.parse(
      localStorage.getItem(MIGRATION_STORAGE_KEY) ?? "null",
    );
    if (
      !value ||
      typeof value !== "object" ||
      !("ownerId" in value) ||
      typeof value.ownerId !== "string" ||
      !("completed" in value) ||
      typeof value.completed !== "boolean"
    ) return null;
    const candidate =
      "candidate" in value && value.candidate && typeof value.candidate === "object"
        ? arrangementOf(parsePreferences(JSON.stringify(value.candidate)))
        : undefined;
    return { ownerId: value.ownerId, completed: value.completed, candidate };
  } catch {
    return null;
  }
}

function writeMigrationState(value: MigrationState) {
  try {
    localStorage.setItem(MIGRATION_STORAGE_KEY, JSON.stringify(value));
  } catch {
    // Migration ownership is also tracked in memory for the active page.
  }
}

function arrangementOf(value: DashboardPreferences): DashboardArrangement {
  return {
    visibleWidgets: value.visibleWidgets,
    layouts: { dashboard: value.layouts.dashboard },
  };
}

function resetAccountArrangement(current: DashboardPreferences) {
  const defaults = defaultPreferences();
  return {
    ...current,
    visibleWidgets: defaults.visibleWidgets,
    layouts: {
      ...current.layouts,
      dashboard: defaults.layouts.dashboard,
    },
  };
}

function applyArrangement(
  current: DashboardPreferences,
  value: DashboardArrangement,
): DashboardPreferences {
  return {
    ...current,
    visibleWidgets: parsePreferences(JSON.stringify(value)).visibleWidgets,
    layouts: {
      ...current.layouts,
      dashboard: normalizeLayouts(value.layouts).dashboard,
    },
  };
}

function useDashboardPreferencesState() {
  const { user } = useAuth();
  const [initialPreferences] = useState(readPreferences);
  const [preferences, setPreferences] = useState(initialPreferences);
  const [systemDark, setSystemDark] = useState(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches,
  );
  const [persistent, setPersistent] = useState(true);
  const migrationState = useRef(readMigrationState());
  const [localWasPresent] = useState(
    () => hasLocalPreferences() || Boolean(migrationState.current?.candidate),
  );
  const migrationCandidate = useRef(
    migrationState.current?.candidate ?? arrangementOf(initialPreferences),
  );
  const [cloud, setCloud] = useState<DashboardCloudState>({
    loading: Boolean(user),
    saving: false,
    version: 0,
    error: null,
    migrationAvailable: false,
    conflict: null,
  });
  const version = useRef(0);
  const accountId = useRef(user?.id);
  const activeAccountId = useRef(user?.id ?? null);
  accountId.current = user?.id;
  const resolvedTheme =
    preferences.theme === "system"
      ? systemDark
        ? "dark"
        : "light"
      : preferences.theme;
  useEffect(() => {
    const query = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => setSystemDark(query.matches);
    query.addEventListener("change", handleChange);
    return () => query.removeEventListener("change", handleChange);
  }, []);
  useLayoutEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = resolvedTheme;
    root.dataset.material = preferences.material;
    root.style.colorScheme = resolvedTheme;
    root.style.setProperty("--accent", preferences.accent);
    root.style.setProperty("--accent-on", accentForeground(preferences.accent));
  }, [resolvedTheme, preferences.accent, preferences.material]);
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
      setPersistent(true);
    } catch {
      setPersistent(false);
    }
  }, [preferences]);
  useLayoutEffect(() => {
    const nextId = user?.id ?? null;
    if (activeAccountId.current !== nextId) {
      activeAccountId.current = nextId;
      version.current = 0;
      setPreferences(resetAccountArrangement);
      setCloud({
        loading: Boolean(nextId),
        saving: false,
        version: 0,
        error: null,
        migrationAvailable: false,
        conflict: null,
      });
    }
    if (!user) {
      version.current = 0;
      setCloud({
        loading: false,
        saving: false,
        version: 0,
        error: null,
        migrationAvailable: false,
        conflict: null,
      });
      return;
    }
    const id = user.id;
    // A failed or cancelled GET must not hand local settings to the next account.
    if (localWasPresent && !migrationState.current) {
      migrationState.current = {
        ownerId: id,
        completed: false,
        candidate: migrationCandidate.current,
      };
      writeMigrationState(migrationState.current);
    } else if (
      migrationState.current?.ownerId === id &&
      !migrationState.current.completed &&
      migrationState.current.candidate
    ) {
      migrationCandidate.current = migrationState.current.candidate;
    }
    const controller = new AbortController();
    version.current = 0;
    setCloud({
      loading: true,
      saving: false,
      version: 0,
      error: null,
      migrationAvailable: false,
      conflict: null,
    });
    readAccountPreference<DashboardArrangement>("dashboard", controller.signal)
      .then((result) => {
        if (controller.signal.aborted || accountId.current !== id) return;
        version.current = result.version;
        if (result.value) {
          setPreferences((current) => applyArrangement(current, result.value!));
          if (
            !migrationState.current ||
            migrationState.current.ownerId === id
          ) {
            migrationState.current = { ownerId: id, completed: true };
            writeMigrationState(migrationState.current);
          }
        }
        let migrationAvailable = false;
        if (result.version === 0 && result.value === null && localWasPresent) {
          const migration = migrationState.current;
          migrationAvailable =
            migration?.ownerId === id && !migration.completed;
        }
        setCloud({
          loading: false,
          saving: false,
          version: result.version,
          error: null,
          migrationAvailable,
          conflict: null,
        });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || accountId.current !== id) return;
        setCloud((current) => ({
          ...current,
          loading: false,
          saving: false,
          error: error instanceof Error ? error.message : "Nie można pobrać ustawień konta.",
        }));
      });
    return () => controller.abort();
  }, [user?.id, localWasPresent]);

  const writeArrangement = async (
    value: DashboardArrangement,
    overwrite = false,
    onlyIfMissing = false,
  ): Promise<boolean> => {
    if (
      cloud.loading ||
      cloud.saving ||
      (cloud.migrationAvailable && !onlyIfMissing) ||
      !user
    ) return false;
    const expectedVersion = onlyIfMissing
      ? 0
      : overwrite
        ? cloud.conflict?.version
        : version.current;
    if (expectedVersion === undefined) return false;
    setCloud((current) => ({ ...current, saving: true, error: null }));
    try {
      const result = await writeAccountPreference(
        "dashboard",
        expectedVersion,
        value,
      );
      if (accountId.current !== user.id) return false;
      if (onlyIfMissing) {
        migrationState.current = { ownerId: user.id, completed: true };
        writeMigrationState(migrationState.current);
      }
      version.current = result.version;
      setPreferences((current) => applyArrangement(current, value));
      setCloud({
        loading: false,
        saving: false,
        version: result.version,
        error: null,
        migrationAvailable: false,
        conflict: null,
      });
      return true;
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        try {
          const latest = await readAccountPreference<DashboardArrangement>("dashboard");
          if (accountId.current !== user.id) return false;
          version.current = latest.version;
          setCloud({
            loading: false,
            saving: false,
            version: latest.version,
            error: null,
            migrationAvailable: false,
            conflict: latest,
          });
        } catch (readError) {
          setCloud((current) => ({
            ...current,
            saving: false,
            error: readError instanceof Error
              ? readError.message
              : "Nie można odczytać bieżących ustawień konta.",
          }));
        }
      } else {
        setCloud((current) => ({
          ...current,
          saving: false,
          error: error instanceof Error ? error.message : "Nie udało się zapisać ustawień konta.",
        }));
      }
      return false;
    }
  };

  const chooseMigration = async (importLocal: boolean) => {
    const candidate = importLocal
      ? migrationCandidate.current
      : arrangementOf(defaultPreferences());
    const saved = await writeArrangement(candidate, false, true);
    if (saved && !importLocal)
      setPreferences((current) => applyArrangement(current, candidate));
  };

  const reloadRemoteArrangement = () => {
    const latest = cloud.conflict;
    if (!latest?.value) return;
    version.current = latest.version;
    setPreferences((current) => applyArrangement(current, latest.value!));
    setCloud((current) => ({
      ...current,
      version: latest.version,
      error: null,
      conflict: null,
      migrationAvailable: false,
    }));
  };

  return {
    preferences,
    setPreferences,
    resolvedTheme,
    persistent,
    cloud,
    saveArrangement: writeArrangement,
    chooseMigration,
    reloadRemoteArrangement,
    toggleWidget: (id: WidgetId) =>
      setPreferences((previous) => ({
        ...previous,
        visibleWidgets: previous.visibleWidgets.includes(id)
          ? previous.visibleWidgets.filter((value) => value !== id)
          : [...previous.visibleWidgets, id],
      })),
    reset: () => setPreferences(defaultPreferences()),
  };
}

export function DashboardPreferencesProvider({
  children,
}: {
  children: ReactNode;
}) {
  return <Context value={useDashboardPreferencesState()}>{children}</Context>;
}

export function useDashboardPreferences() {
  const value = useContext(Context);
  if (!value) throw new Error("DashboardPreferencesProvider required");
  return value;
}

// Choose legible text for any user-selected accent, including pale colors.
function accentForeground(hex: string) {
  const rgb = [1, 3, 5]
    .map((index) => parseInt(hex.slice(index, index + 2), 16) / 255)
    .map((value) =>
      value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4,
    );
  const luminance = rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722;
  return (luminance + 0.05) / 0.05 >= 1.05 / (luminance + 0.05)
    ? "#000000"
    : "#ffffff";
}
