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
  CARD_DEFAULT,
  normalizeVehicleLayout,
  resizeCard,
  type CardSize,
  type VehicleLayout,
} from "./vehicle-layout";

function usePreferences(scope: string) {
  const storageKey = `fleet-flow.vehicles.v1.${scope}`;
  const [initial] = useState(() => {
    try {
      return {
        layout: normalizeVehicleLayout(
          JSON.parse(localStorage.getItem(storageKey) || "{}"),
        ),
        persistent: true,
      };
    } catch {
      return { layout: {}, persistent: false };
    }
  });
  const [saved, setSaved] = useState<VehicleLayout>(initial.layout);
  const [draft, setDraft] = useState<VehicleLayout | null>(null);
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
    size: (id: string) => (draft ?? saved)[id] ?? CARD_DEFAULT,
    start: () => setDraft((previous) => previous ?? { ...saved }),
    change: (id: string, size: CardSize) =>
      setDraft((previous) =>
        previous ? resizeCard(previous, id, size) : previous,
      ),
    reset: () => setDraft((previous) => (previous ? {} : previous)),
    cancel: () => setDraft(null),
    save: () => {
      if (!draft) return;
      const next = normalizeVehicleLayout(draft);
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
