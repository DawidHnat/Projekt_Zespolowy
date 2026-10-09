import { useEffect, useRef, useState } from "react";
import {
  deleteBackgroundImage,
  prepareBackgroundImage,
  readBackgroundImage,
  saveBackgroundImage,
  type BackgroundImage,
} from "./background-image";

export function useBackgroundImage() {
  const [image, setImage] = useState<BackgroundImage | null>(null);
  const [preview, setPreview] = useState<{ id: string; url: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [persistent, setPersistent] = useState(true);
  const [error, setError] = useState("");
  const operation = useRef(0);
  useEffect(() => {
    let active = true;
    const initialOperation = operation.current;
    readBackgroundImage()
      .then((value) => {
        if (active && operation.current === initialOperation) setImage(value);
      })
      .catch(() => {
        if (active) setPersistent(false);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);
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
    const token = ++operation.current;
    setBusy(true);
    setError("");
    try {
      const next = await prepareBackgroundImage(file);
      if (operation.current !== token) return null;
      try {
        await saveBackgroundImage(next);
        setPersistent(true);
      } catch {
        setPersistent(false);
      }
      if (operation.current !== token) return null;
      setImage(next);
      return next.id;
    } catch (reason) {
      if (operation.current === token)
        setError(reason instanceof Error ? reason.message : "Nie udało się dodać obrazu.");
      return null;
    } finally {
      if (operation.current === token) setBusy(false);
    }
  };
  const remove = async () => {
    ++operation.current;
    setBusy(true);
    setError("");
    try {
      await deleteBackgroundImage();
      setImage(null);
      return true;
    } catch {
      setError("Nie udało się usunąć zapisanego zdjęcia. Spróbuj ponownie.");
      return false;
    } finally {
      setBusy(false);
    }
  };
  return {
    image,
    url: preview?.id === image?.id ? preview?.url ?? "" : "",
    loading, busy, persistent, error, upload, remove,
  };
}
export type BackgroundImageController = ReturnType<typeof useBackgroundImage>;
