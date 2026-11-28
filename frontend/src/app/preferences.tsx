import {
  createContext,
  useContext,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
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
import { normalizeLayouts, type SavedLayouts } from "../features/dashboard/model/widget-layout";

export { ACCENT_PRESETS, defaultPreferences } from "./preference-model";
export type {
  DashboardPreferences,
  ThemeMode,
  Arrangement,
} from "./preference-model";

type DashboardPreferences = ReturnType<typeof defaultPreferences>;
const MIGRATION_STORAGE_KEY = "fleet-flow.dashboard.account-migration.v1";
type SyncedLayouts = Pick<SavedLayouts, "dashboard" | "map">;
export type DashboardArrangement = {
  visibleWidgets: WidgetId[];
  layouts: Partial<SyncedLayouts>;
};
export type DashboardAccountPreferences = Pick<
  DashboardPreferences,
  "theme" | "accent" | "material" | "background" | "visibleWidgets"
> & { layouts: SyncedLayouts };
type MigrationState = {
  ownerId: string;
  completed: boolean;
  candidate?: DashboardAccountPreferences;
};
type DashboardCloudState = {
  loading: boolean;
  saving: boolean;
  version: number;
  error: string | null;
  migrationAvailable: boolean;
  conflict: AccountPreference<DashboardAccountPreferences> | null;
};
type DashboardPreferencesState = ReturnType<typeof useDashboardPreferencesState>;
const Context = createContext<DashboardPreferencesState | null>(null);

function readLegacyPreferences() {
  try {
    return parsePreferences(
      localStorage.getItem(STORAGE_KEY) ??
        localStorage.getItem(LEGACY_STORAGE_KEY),
    );
  } catch {
    return defaultPreferences();
  }
}

function hasLegacyPreferences() {
  try {
    return Boolean(
      localStorage.getItem(STORAGE_KEY) ?? localStorage.getItem(LEGACY_STORAGE_KEY),
    );
  } catch {
    return false;
  }
}

function syncedPreferences(value: DashboardPreferences): DashboardAccountPreferences {
  return {
    theme: value.theme,
    accent: value.accent,
    material: value.material,
    background: value.background,
    visibleWidgets: value.visibleWidgets,
    layouts: {
      dashboard: value.layouts.dashboard,
      map: value.layouts.map,
    },
  };
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
    let candidate: DashboardAccountPreferences | undefined;
    if ("candidate" in value && value.candidate && typeof value.candidate === "object") {
      const source = value.candidate as Record<string, unknown>;
      const parsed = parsePreferences(JSON.stringify(source));
      const legacy = readLegacyPreferences();
      const sourceLayouts =
        source.layouts && typeof source.layouts === "object"
          ? source.layouts as Record<string, unknown>
          : {};
      const merged: DashboardPreferences = {
        ...parsed,
        theme: "theme" in source ? parsed.theme : legacy.theme,
        accent: "accent" in source ? parsed.accent : legacy.accent,
        material: "material" in source ? parsed.material : legacy.material,
        background: "background" in source ? parsed.background : legacy.background,
        layouts: {
          ...legacy.layouts,
          ...(sourceLayouts.dashboard ? { dashboard: parsed.layouts.dashboard } : {}),
          ...(sourceLayouts.map ? { map: parsed.layouts.map } : {}),
        },
      };
      candidate = syncedPreferences(merged);
    }
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

function applyAccountPreferences(
  current: DashboardPreferences,
  value: Partial<DashboardAccountPreferences>,
): DashboardPreferences {
  const parsed = parsePreferences(JSON.stringify(value));
  const hasAppearance =
    "theme" in value || "accent" in value || "material" in value || "background" in value;
  const normalizedLayouts = normalizeLayouts(value.layouts);
  return {
    ...current,
    ...(hasAppearance
      ? {
          theme: parsed.theme,
          accent: parsed.accent,
          material: parsed.material,
          background: parsed.background,
        }
      : {}),
    visibleWidgets: parsed.visibleWidgets,
    layouts: {
      ...current.layouts,
      ...(value.layouts?.dashboard
        ? { dashboard: normalizedLayouts.dashboard }
        : {}),
      ...(value.layouts?.map ? { map: normalizedLayouts.map } : {}),
    },
  };
}

function mergeArrangement(
  current: DashboardPreferences,
  value: DashboardArrangement,
): DashboardPreferences {
  return {
    ...current,
    visibleWidgets: value.visibleWidgets,
    layouts: {
      ...current.layouts,
      ...value.layouts,
    },
  };
}

function useDashboardPreferencesState() {
  const { user } = useAuth();
  const [preferences, setPreferencesState] = useState(defaultPreferences);
  const preferencesRef = useRef(preferences);
  const [systemDark, setSystemDark] = useState(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches,
  );
  const migrationState = useRef(readMigrationState());
  const [localWasPresent] = useState(
    () => hasLegacyPreferences() || Boolean(migrationState.current?.candidate),
  );
  const migrationCandidate = useRef(
    migrationState.current?.candidate ?? syncedPreferences(readLegacyPreferences()),
  );
  const [cloud, setCloud] = useState<DashboardCloudState>({
    loading: Boolean(user),
    saving: false,
    version: 0,
    error: null,
    migrationAvailable: false,
    conflict: null,
  });
  const cloudRef = useRef(cloud);
  const version = useRef(0);
  const accountId = useRef(user?.id ?? null);
  const activeAccountId = useRef(user?.id ?? null);
  accountId.current = user?.id ?? null;
  const saveQueue = useRef<Promise<boolean>>(Promise.resolve(true));
  const resolvedTheme =
    preferences.theme === "system"
      ? systemDark
        ? "dark"
        : "light"
      : preferences.theme;

  const updateCloud = (next: DashboardCloudState) => {
    cloudRef.current = next;
    setCloud(next);
  };
  const updateLocalPreferences = (next: DashboardPreferences) => {
    preferencesRef.current = next;
    setPreferencesState(next);
  };

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

  useLayoutEffect(() => {
    const nextId = user?.id ?? null;
    if (activeAccountId.current !== nextId) {
      activeAccountId.current = nextId;
      version.current = 0;
      updateLocalPreferences(defaultPreferences());
      updateCloud({
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
      updateCloud({
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
    if (localWasPresent && !migrationState.current) {
      migrationState.current = {
        ownerId: id,
        completed: false,
        candidate: migrationCandidate.current,
      };
      writeMigrationState(migrationState.current);
    }
    if (
      migrationState.current?.ownerId === id &&
      !migrationState.current.completed &&
      migrationState.current.candidate
    ) {
      migrationCandidate.current = migrationState.current.candidate;
    }

    const controller = new AbortController();
    version.current = 0;
    updateCloud({
      loading: true,
      saving: false,
      version: 0,
      error: null,
      migrationAvailable: false,
      conflict: null,
    });
    readAccountPreference<Partial<DashboardAccountPreferences>>(
      "dashboard",
      controller.signal,
    )
      .then((result) => {
        if (controller.signal.aborted || accountId.current !== id) return;
        version.current = result.version;
        if (result.value) {
          updateLocalPreferences(
            applyAccountPreferences(defaultPreferences(), result.value),
          );
          if (!migrationState.current || migrationState.current.ownerId === id) {
            migrationState.current = { ownerId: id, completed: true };
            writeMigrationState(migrationState.current);
          }
        } else {
          updateLocalPreferences(defaultPreferences());
        }
        const migrationAvailable =
          result.version === 0 &&
          result.value === null &&
          localWasPresent &&
          migrationState.current?.ownerId === id &&
          !migrationState.current.completed;
        updateCloud({
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
        updateCloud({
          ...cloudRef.current,
          loading: false,
          saving: false,
          error: error instanceof Error
            ? error.message
            : "Nie można pobrać ustawień konta.",
        });
      });
    return () => controller.abort();
  }, [user?.id, localWasPresent]);

  const writePreferences = (
    value: DashboardAccountPreferences,
    overwrite = false,
    onlyIfMissing = false,
  ): Promise<boolean> => {
    const task = saveQueue.current.then(async () => {
      const currentCloud = cloudRef.current;
      const id = accountId.current;
      if (
        !id ||
        currentCloud.loading ||
        (!overwrite && currentCloud.conflict) ||
        (onlyIfMissing && currentCloud.version !== 0)
      ) return false;
      const expectedVersion = onlyIfMissing
        ? 0
        : overwrite
          ? currentCloud.conflict?.version
          : version.current;
      if (expectedVersion === undefined) return false;
      updateCloud({ ...currentCloud, saving: true, error: null });
      try {
        const result = await writeAccountPreference(
          "dashboard",
          expectedVersion,
          value,
        );
        if (accountId.current !== id) return false;
        version.current = result.version;
        if (migrationState.current?.ownerId === id) {
          migrationState.current = {
            ownerId: id,
            completed: true,
          };
          writeMigrationState(migrationState.current);
        }
        updateCloud({
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
            const latest =
              await readAccountPreference<DashboardAccountPreferences>("dashboard");
            if (accountId.current !== id) return false;
            version.current = latest.version;
            updateCloud({
              loading: false,
              saving: false,
              version: latest.version,
              error: null,
              migrationAvailable: false,
              conflict: latest,
            });
          } catch (readError) {
            updateCloud({
              ...cloudRef.current,
              saving: false,
              error: readError instanceof Error
                ? readError.message
                : "Nie można odczytać bieżących ustawień konta.",
            });
          }
        } else {
          updateCloud({
            ...cloudRef.current,
            saving: false,
            error: error instanceof Error
              ? error.message
              : "Nie udało się zapisać ustawień konta.",
          });
        }
        return false;
      }
    });
    saveQueue.current = task;
    return task;
  };

  const setPreferences: Dispatch<SetStateAction<DashboardPreferences>> = (next) => {
    if (cloudRef.current.loading) return;
    const value =
      typeof next === "function" ? next(preferencesRef.current) : next;
    updateLocalPreferences(value);
    if (accountId.current) void writePreferences(syncedPreferences(value));
  };

  const saveArrangement = async (
    value: DashboardArrangement,
    overwrite = false,
  ) => {
    const next = mergeArrangement(preferencesRef.current, value);
    if (!await writePreferences(syncedPreferences(next), overwrite)) return false;
    updateLocalPreferences(next);
    return true;
  };

  const chooseMigration = async () => {
    if (!cloudRef.current.migrationAvailable) return false;
    const value = migrationCandidate.current;
    if (!await writePreferences(value, false, true)) return false;
    updateLocalPreferences(
      applyAccountPreferences(defaultPreferences(), value),
    );
    return true;
  };

  const reloadRemoteArrangement = () => {
    const latest = cloudRef.current.conflict;
    if (!latest) return;
    const next = latest.value
      ? applyAccountPreferences(defaultPreferences(), latest.value)
      : defaultPreferences();
    version.current = latest.version;
    updateLocalPreferences(next);
    updateCloud({
      ...cloudRef.current,
      version: latest.version,
      error: null,
      conflict: null,
      migrationAvailable: false,
    });
  };

  return {
    preferences,
    setPreferences,
    resolvedTheme,
    cloud,
    saveArrangement,
    chooseMigration,
    migrationBackgroundId:
      migrationCandidate.current.background.kind === "custom"
        ? migrationCandidate.current.background.customId
        : null,
    retrySave: () => writePreferences(syncedPreferences(preferencesRef.current)),
    overwriteCurrent: () =>
      writePreferences(
        syncedPreferences(preferencesRef.current),
        true,
      ),
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
