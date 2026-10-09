import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useAuth } from "../../auth/AuthProvider";
import { prepareLocalImage } from "../../../shared/media/local-image";
import {
  readVehiclePhotos,
  saveVehiclePhoto,
  deleteVehiclePhoto,
} from "./vehicle-photo-store";
import {
  normalizeLayoutConfig,
  cardSize,
  resizeCards,
  targetSizes,
  validVehicleId,
  type CardSize,
  type VehicleLayoutConfig,
} from "./vehicle-layout";

function usePreferences(scope: string) {
  const storageKey = `fleet-flow.vehicles.v2.${scope}`;
  const [initial] = useState(() => {
    try {
      return {
        layout: normalizeLayoutConfig(
          JSON.parse(
            localStorage.getItem(storageKey) ??
              localStorage.getItem(`fleet-flow.vehicles.v1.${scope}`) ??
              "{}",
          ),
        ),
        persistent: true,
      };
    } catch {
      return { layout: normalizeLayoutConfig(null), persistent: false };
    }
  });
  const [saved, setSaved] = useState<VehicleLayoutConfig>(initial.layout);
  const [draft, setDraft] = useState<VehicleLayoutConfig | null>(null);
  const [editScope, setEditScope] = useState<"all" | "selected">("selected");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [persistent, setPersistent] = useState(initial.persistent);
  const [photos, setPhotos] = useState<Record<string, string>>({});
  const [photosLoading, setPhotosLoading] = useState(true);
  const [photoError, setPhotoError] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const urls = useRef(new Map<string, string>());
  const mounted = useRef(false);
  const operation = useRef(0);
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
      for (const url of urls.current.values()) URL.revokeObjectURL(url);
      urls.current.clear();
    };
  }, [scope]);
  const upload = async (id: string, file: File) => {
    if (busy || photosLoading) return;
    const revision = ++operation.current;
    setBusy(id);
    setPhotoError("");
    try {
      const image = await prepareLocalImage(file, 1024);
      if (!mounted.current || operation.current !== revision) return;
      try {
        await saveVehiclePhoto(scope, id, image);
      } catch {
        if (mounted.current)
          setPhotoError(
            "Zdjęcie działa w tej sesji, ale przeglądarka nie zapisała go na później.",
          );
      }
      if (!mounted.current || operation.current !== revision) return;
      const url = URL.createObjectURL(image.blob);
      const previous = urls.current.get(id);
      urls.current.set(id, url);
      setPhotos((values) => ({ ...values, [id]: url }));
      if (previous) URL.revokeObjectURL(previous);
    } catch (e) {
      if (mounted.current)
        setPhotoError(
          e instanceof Error ? e.message : "Nie udało się dodać zdjęcia.",
        );
    } finally {
      if (mounted.current && operation.current === revision) setBusy(null);
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
        setPhotoError(
          "Nie udało się usunąć zapisanego zdjęcia. Spróbuj ponownie.",
        );
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
    persistent,
    editing: draft !== null,
    editScope,
    selectedIds,
    setEditScope,
    isSelected: (id: string) =>
      draft !== null && (editScope === "all" || selectedIds.includes(id)),
    groupSize: targetSizes(
      draft ?? saved,
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
    size: (id: string) => cardSize(draft ?? saved, id),
    start: () => {
      if (draft) return;
      setEditScope("selected");
      setSelectedIds([]);
      setDraft(saved);
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
          ? resizeCards(
              previous,
              editScope === "all" ? "all" : selectedIds,
              patch,
            )
          : previous,
      ),
    reset: () =>
      setDraft((previous) =>
        previous ? normalizeLayoutConfig(null) : previous,
      ),
    cancel: () => setDraft(null),
    save: () => {
      if (!draft) return;
      const next = normalizeLayoutConfig(draft);
      try {
        localStorage.setItem(storageKey, JSON.stringify(next));
        setPersistent(true);
      } catch {
        setPersistent(false);
      }
      setSaved(next);
      setDraft(null);
    },
  };
}
const Context = createContext<ReturnType<typeof usePreferences> | null>(null);
function ScopedPreferences({
  scope,
  children,
}: {
  scope: string;
  children: ReactNode;
}) {
  return <Context value={usePreferences(scope)}>{children}</Context>;
}
export function VehiclePreferencesProvider({
  children,
}: {
  children: ReactNode;
}) {
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
