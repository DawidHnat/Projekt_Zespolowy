import { useEffect, useRef, useState } from "react";
import {
  prepareBackgroundImage,
  readBackgroundImage,
  type BackgroundImage,
} from "./background-image";
import {
  deleteAccountBackgroundImage,
  readAccountBackgroundImage,
  writeAccountBackgroundImage,
} from "../../../shared/api/account-preferences";

export function useBackgroundImage(
  accountId: string | undefined,
  selectedImageId: string | null,
) {
  const [image, setImage] = useState<BackgroundImage | null>(null);
  const [preview, setPreview] = useState<{ id: string; url: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const operation = useRef(0);

  useEffect(() => {
    const token = ++operation.current;
    setBusy(false);
    setError("");
    if (!accountId || !selectedImageId) {
      setImage(null);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError("");
    readAccountBackgroundImage(selectedImageId, controller.signal)
      .then((blob) => {
        if (controller.signal.aborted || operation.current !== token) return;
        setImage({
          id: selectedImageId,
          blob,
          name: "Własne tło",
          width: 0,
          height: 0,
        });
      })
      .catch((reason: unknown) => {
        if (controller.signal.aborted || operation.current !== token) return;
        setImage(null);
        setError(
          reason instanceof Error
            ? reason.message
            : "Nie udało się pobrać własnego tła z konta.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted && operation.current === token)
          setLoading(false);
      });
    return () => controller.abort();
  }, [accountId, selectedImageId]);

  useEffect(() => {
    if (!image) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(image.blob);
    setPreview({ id: image.id, url });
    return () => URL.revokeObjectURL(url);
  }, [image]);

  const upload = async (file: File): Promise<string | null> => {
    if (!accountId) return null;
    const token = ++operation.current;
    setBusy(true);
    setError("");
    try {
      const next = await prepareBackgroundImage(file);
      await writeAccountBackgroundImage(next.id, next.blob);
      if (operation.current !== token) return null;
      setImage(next);
      return next.id;
    } catch (reason) {
      if (operation.current === token)
        setError(
          reason instanceof Error
            ? reason.message
            : "Nie udało się zapisać obrazu na koncie.",
        );
      return null;
    } finally {
      if (operation.current === token) setBusy(false);
    }
  };

  const importLegacy = async (id: string): Promise<boolean> => {
    if (!accountId) return false;
    const token = ++operation.current;
    setBusy(true);
    setError("");
    try {
      const legacy = await readBackgroundImage();
      if (!legacy || legacy.id !== id) {
        throw new Error(
          "Stare zdjęcie nie jest dostępne w tej przeglądarce. Wybierz nowe tło w Ustawieniach.",
        );
      }
      await writeAccountBackgroundImage(legacy.id, legacy.blob);
      if (operation.current !== token) return false;
      setImage(legacy);
      return true;
    } catch (reason) {
      if (operation.current === token)
        setError(
          reason instanceof Error
            ? reason.message
            : "Nie udało się przenieść starego tła na konto.",
        );
      return false;
    } finally {
      if (operation.current === token) setBusy(false);
    }
  };

  const remove = async () => {
    if (!accountId || !selectedImageId) return false;
    const token = ++operation.current;
    setBusy(true);
    setError("");
    try {
      await deleteAccountBackgroundImage(selectedImageId);
      if (operation.current !== token) return false;
      setImage(null);
      return true;
    } catch (reason) {
      if (operation.current === token)
        setError(
          reason instanceof Error
            ? reason.message
            : "Nie udało się usunąć zapisanego zdjęcia. Spróbuj ponownie.",
        );
      return false;
    } finally {
      if (operation.current === token) setBusy(false);
    }
  };

  return {
    image,
    url: preview?.id === image?.id ? preview?.url ?? "" : "",
    loading,
    busy,
    error,
    upload,
    importLegacy,
    remove,
  };
}
export type BackgroundImageController = ReturnType<typeof useBackgroundImage>;
