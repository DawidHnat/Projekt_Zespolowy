import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useAuth } from "../../auth/AuthProvider";
import {
  readAccountPreference,
  writeAccountPreference,
  type AccountPreference,
} from "../../../shared/api/account-preferences";
import { ApiError } from "../../../shared/api/client";
import { prepareLocalImage } from "../../../shared/media/local-image";
import { readVehiclePhotos, saveVehiclePhoto, deleteVehiclePhoto } from "./vehicle-photo-store";
import {
  normalizeLayoutConfig,
  cardSize,
  resizeCards,
  targetSizes,
  validVehicleId,
  type CardSize,
  type VehicleLayoutConfig,
} from "./vehicle-layout";

type VehicleSort = "name-asc" | "name-desc" | "status" | "odometer-asc" | "odometer-desc";
type VehicleModulePreferences = {
  layout: VehicleLayoutConfig;
  sort: VehicleSort;
  filters: { q: string; status: string };
  pageSize: number;
};
type VehicleCloudState = {
  loading: boolean;
  error: string | null;
  migrationAvailable: boolean;
  conflict: AccountPreference<VehicleModulePreferences> | null;
};
const pageSizes = [10, 25, 50, 100];
const sorts: VehicleSort[] = ["name-asc", "name-desc", "status", "odometer-asc", "odometer-desc"];
const statuses = ["moving", "stopped", "offline", "unknown"];

function defaults(): VehicleModulePreferences {
  return {
    layout: normalizeLayoutConfig(null),
    sort: "name-asc",
    filters: { q: "", status: "" },
    pageSize: 25,
  };
}

function normalizeModulePreferences(value: unknown): VehicleModulePreferences {
  const item = value && typeof value === "object" && !Array.isArray(value)
    ? value as Partial<VehicleModulePreferences>
    : {};
  const filters: Partial<VehicleModulePreferences["filters"]> =
    item.filters && typeof item.filters === "object"
    ? item.filters
    : {};
  return {
    layout: normalizeLayoutConfig(item.layout),
    sort: sorts.includes(item.sort as VehicleSort)
      ? item.sort as VehicleSort
      : "name-asc",
    filters: {
      q: typeof filters.q === "string" ? filters.q.slice(0, 100) : "",
      status: statuses.includes(filters.status ?? "") ? filters.status! : "",
    },
    pageSize: pageSizes.includes(item.pageSize ?? 0) ? item.pageSize! : 25,
  };
}

function readLocalPreferences(scope: string) {
  try {
    const layout = localStorage.getItem(`fleet-flow.vehicles.v2.${scope}`) ??
      localStorage.getItem(`fleet-flow.vehicles.v1.${scope}`);
    const pageSize = localStorage.getItem(`fleet-flow.list-page-size.v1.${scope}`);
    return {
      value: {
        ...defaults(),
        layout: normalizeLayoutConfig(JSON.parse(layout ?? "{}")),
        pageSize: pageSizes.includes(Number(pageSize)) ? Number(pageSize) : 25,
      },
      exists: Boolean(layout || pageSize),
    };
  } catch {
    return { value: defaults(), exists: false };
  }
}

function migrationKey(scope: string) {
  return `fleet-flow.vehicles.account-migration.v1.${scope}`;
}

function migrationCompleted(scope: string) {
  try {
    return localStorage.getItem(migrationKey(scope)) === "completed";
  } catch {
    return false;
  }
}

function markMigrationCompleted(scope: string) {
  try {
    localStorage.setItem(migrationKey(scope), "completed");
  } catch {
    // The account-scoped server preference remains authoritative.
  }
}

function usePreferences(scope: string) {
  const [initial] = useState(() => readLocalPreferences(scope));
  const [saved, setSaved] = useState<VehicleModulePreferences>(defaults);
  const [draft, setDraft] = useState<VehicleLayoutConfig | null>(null);
  const [editScope, setEditScope] = useState<"all" | "selected">("selected");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [cloud, setCloud] = useState<VehicleCloudState>({
    loading: true,
    error: null,
    migrationAvailable: false,
    conflict: null,
  });
  const [saving, setSaving] = useState(false);
  const [photos, setPhotos] = useState<Record<string, string>>({});
  const [photosLoading, setPhotosLoading] = useState(true);
  const [photoError, setPhotoError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const urls = useRef(new Map<string, string>());
  const mounted = useRef(false);
  const operation = useRef(0);
  const revision = useRef(0);
  const conflictRef = useRef<AccountPreference<VehicleModulePreferences> | null>(null);
  const savedRef = useRef(saved);
  savedRef.current = saved;
  const saveQueue = useRef<Promise<boolean>>(Promise.resolve(true));
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setCloud({ loading: true, error: null, migrationAvailable: false, conflict: null });
    void readAccountPreference<VehicleModulePreferences>("vehicles", controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        revision.current = result.version;
        if (result.value) {
          const next = normalizeModulePreferences(result.value);
          savedRef.current = next;
          setSaved(next);
          markMigrationCompleted(scope);
        } else {
          savedRef.current = defaults();
          setSaved(defaults());
        }
        setCloud({
          loading: false,
          error: null,
          migrationAvailable:
            result.version === 0 &&
            result.value === null &&
            initial.exists &&
            !migrationCompleted(scope),
          conflict: null,
        });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setCloud({
          loading: false,
          error: error instanceof Error ? error.message : "Nie można pobrać ustawień konta.",
          migrationAvailable: false,
          conflict: null,
        });
      });
    return () => controller.abort();
  }, [scope, initial.exists]);

  const writeValue = (
    getValue: () => VehicleModulePreferences,
    expectedVersion?: number,
  ): Promise<boolean> => {
    const task = saveQueue.current.then(async () => {
      if (
        cloud.loading ||
        (conflictRef.current && expectedVersion === undefined)
      )
        return false;
      setSaving(true);
      setCloud((current) => ({ ...current, error: null }));
      try {
        const result = await writeAccountPreference(
          "vehicles",
          expectedVersion ?? revision.current,
          getValue(),
        );
        revision.current = result.version;
        conflictRef.current = null;
        markMigrationCompleted(scope);
        setCloud({ loading: false, error: null, migrationAvailable: false, conflict: null });
        return true;
      } catch (error) {
        if (error instanceof ApiError && error.status === 409) {
          try {
            const latest = await readAccountPreference<VehicleModulePreferences>("vehicles");
            revision.current = latest.version;
            conflictRef.current = latest;
            setCloud({ loading: false, error: null, migrationAvailable: false, conflict: latest });
          } catch (readError) {
            setCloud((current) => ({
              ...current,
              error: readError instanceof Error
                ? readError.message
                : "Nie można odczytać bieżących ustawień konta.",
            }));
          }
        } else {
          setCloud((current) => ({
            ...current,
            error: error instanceof Error ? error.message : "Nie udało się zapisać ustawień konta.",
          }));
        }
        return false;
      } finally {
        setSaving(false);
      }
    });
    saveQueue.current = task;
    return task;
  };

  const scheduleWrite = () => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      saveTimer.current = null;
      // A layout save already in the queue can update preferences before this write runs.
      void writeValue(() => savedRef.current);
    }, 500);
  };

  const updateSettings = (patch: Partial<VehicleModulePreferences>) => {
    if (cloud.loading) return;
    const next = { ...savedRef.current, ...patch };
    savedRef.current = next;
    setSaved(next);
    scheduleWrite();
  };

  const chooseMigration = async () => {
    if (!cloud.migrationAvailable) return;
    const next = initial.value;
    if (await writeValue(() => next, 0)) {
      savedRef.current = next;
      setSaved(next);
      markMigrationCompleted(scope);
    }
  };

  const resolveConflict = async (action: "reload" | "overwrite") => {
    const conflict = conflictRef.current;
    if (!conflict) return;
    if (action === "reload") {
      if (!conflict.value) return;
      const latest = normalizeModulePreferences(conflict.value);
      savedRef.current = latest;
      setSaved(latest);
      setDraft(null);
      conflictRef.current = null;
      setCloud({ loading: false, error: null, migrationAvailable: false, conflict: null });
      return;
    }
    const layoutDraft = draft;
    const layout = layoutDraft ? normalizeLayoutConfig(layoutDraft) : savedRef.current.layout;
    if (await writeValue(() => ({ ...savedRef.current, layout }), conflict.version)) {
      const next = { ...savedRef.current, layout };
      savedRef.current = next;
      setSaved(next);
      setDraft((current) => current === layoutDraft ? null : current);
    }
  };

  useEffect(() => {
    mounted.current = true;
    let active = true;
    readVehiclePhotos(scope)
      .then((rows) => {
        if (!active) return;
        const next: Record<string, string> = {};
        for (const { vehicleId, image } of rows) {
          const url = URL.createObjectURL(image.blob);
          urls.current.set(vehicleId, url);
          next[vehicleId] = url;
        }
        setPhotos(next);
      })
      .catch(() => {
        if (active)
          setPhotoError(
            "Zapisane zdjęcia są chwilowo niedostępne. Możesz dodać zdjęcie na tę sesję.",
          );
      })
      .finally(() => {
        if (active) setPhotosLoading(false);
      });
    return () => {
      active = false;
      mounted.current = false;
      if (saveTimer.current) clearTimeout(saveTimer.current);
      for (const url of urls.current.values()) URL.revokeObjectURL(url);
      urls.current.clear();
    };
  }, [scope]);

  const upload = async (id: string, file: File) => {
    if (busy || photosLoading) return;
    const revisionId = ++operation.current;
    setBusy(id);
    setPhotoError("");
    try {
      const image = await prepareLocalImage(file, 1024);
      if (!mounted.current || operation.current !== revisionId) return;
      try {
        await saveVehiclePhoto(scope, id, image);
      } catch {
        if (mounted.current)
          setPhotoError(
            "Zdjęcie działa w tej sesji, ale przeglądarka nie zapisała go na później.",
          );
      }
      if (!mounted.current || operation.current !== revisionId) return;
      const url = URL.createObjectURL(image.blob);
      const previous = urls.current.get(id);
      urls.current.set(id, url);
      setPhotos((values) => ({ ...values, [id]: url }));
      if (previous) URL.revokeObjectURL(previous);
    } catch (error) {
      if (mounted.current)
        setPhotoError(error instanceof Error ? error.message : "Nie udało się dodać zdjęcia.");
    } finally {
      if (mounted.current && operation.current === revisionId) setBusy(null);
    }
  };

  const remove = async (id: string) => {
    if (busy || photosLoading) return;
    setBusy(id);
    setPhotoError("");
    try {
      await deleteVehiclePhoto(scope, id);
      if (!mounted.current) return;
      const url = urls.current.get(id);
      if (url) URL.revokeObjectURL(url);
      urls.current.delete(id);
      setPhotos((values) => {
        const next = { ...values };
        delete next[id];
        return next;
      });
    } catch {
      if (mounted.current)
        setPhotoError("Nie udało się usunąć zapisanego zdjęcia. Spróbuj ponownie.");
    } finally {
      if (mounted.current) setBusy(null);
    }
  };

  return {
    photos,
    photosLoading,
    photoError,
    busy,
    upload,
    remove,
    cloud,
    saving,
    retrySave: () => writeValue(() => savedRef.current),
    sort: saved.sort,
    filters: saved.filters,
    pageSize: saved.pageSize,
    updateFilters: (filters: VehicleModulePreferences["filters"]) => updateSettings({ filters }),
    updateSort: (sort: VehicleSort) => updateSettings({ sort }),
    updatePageSize: (pageSize: number) => updateSettings({ pageSize }),
    chooseMigration,
    resolveConflict,
    editing: draft !== null,
    editScope,
    selectedIds,
    setEditScope,
    isSelected: (id: string) =>
      draft !== null && (editScope === "all" || selectedIds.includes(id)),
    groupSize: targetSizes(
      draft ?? saved.layout,
      editScope === "all" ? "all" : selectedIds,
    ),
    toggle: (id: string) => {
      if (!draft || !validVehicleId(id)) return;
      if (editScope === "all") {
        setEditScope("selected");
        setSelectedIds([id]);
      } else
        setSelectedIds((ids) =>
          ids.includes(id) ? ids.filter((value) => value !== id) : [...ids, id],
        );
    },
    selectVisible: (ids: string[]) => {
      setEditScope("selected");
      setSelectedIds((previous) => [
        ...new Set([...previous, ...ids.filter(validVehicleId)]),
      ]);
    },
    clearSelection: () => {
      setEditScope("selected");
      setSelectedIds([]);
    },
    focus: (id: string) => {
      if (editScope === "selected" && !selectedIds.includes(id))
        setSelectedIds([id]);
    },
    size: (id: string) => cardSize(draft ?? saved.layout, id),
    start: () => {
      if (draft || cloud.loading || saving) return;
      setEditScope("selected");
      setSelectedIds([]);
      setDraft(saved.layout);
    },
    change: (id: string, patch: Partial<CardSize>) =>
      setDraft((previous) =>
        previous
          ? resizeCards(
              previous,
              editScope === "all"
                ? "all"
                : selectedIds.includes(id)
                  ? selectedIds
                  : [id],
              patch,
            )
          : previous,
      ),
    changeGroup: (patch: Partial<CardSize>) =>
      setDraft((previous) =>
        previous
          ? resizeCards(previous, editScope === "all" ? "all" : selectedIds, patch)
          : previous,
      ),
    reset: () => setDraft((previous) => previous ? normalizeLayoutConfig(null) : previous),
    cancel: () => setDraft(null),
    save: async (overwrite = false) => {
      if (!draft) return false;
      const layoutDraft = draft;
      const layout = normalizeLayoutConfig(layoutDraft);
      if (!await writeValue(
        () => ({ ...savedRef.current, layout }),
        overwrite ? conflictRef.current?.version : undefined,
      )) return false;
      const next = { ...savedRef.current, layout };
      savedRef.current = next;
      setSaved(next);
      setDraft((current) => current === layoutDraft ? null : current);
      return true;
    },
  };
}

const Context = createContext<ReturnType<typeof usePreferences> | null>(null);

function ScopedPreferences({ scope, children }: { scope: string; children: ReactNode }) {
  return <Context value={usePreferences(scope)}>{children}</Context>;
}

export function VehiclePreferencesProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  return user ? (
    <ScopedPreferences key={user.id} scope={user.id}>
      {children}
    </ScopedPreferences>
  ) : null;
}

export function useVehiclePreferences() {
  const value = useContext(Context);
  if (!value) throw new Error("VehiclePreferencesProvider required");
  return value;
}
