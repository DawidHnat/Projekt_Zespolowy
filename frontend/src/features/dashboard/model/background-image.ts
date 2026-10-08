import { fitImage, validateImageFile } from "./background-model";

export type BackgroundImage = {
  id: string;
  blob: Blob;
  name: string;
  width: number;
  height: number;
};
const DATABASE = "fleet-flow.media.v1";
const STORE = "backgrounds";
const KEY = "custom";

// Store only a re-encoded bitmap: original metadata and filename never leave the browser.
export async function prepareBackgroundImage(file: File): Promise<BackgroundImage> {
  validateImageFile(file);
  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    throw new Error("Nie udało się odczytać obrazu. Wybierz inny plik.");
  }
  try {
    const { width, height } = fitImage(bitmap.width, bitmap.height);
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Ta przeglądarka nie obsługuje przygotowania zdjęcia.");
    context.fillStyle = "#e5ecf4";
    context.fillRect(0, 0, width, height);
    context.drawImage(bitmap, 0, 0, width, height);
    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((value) => {
        if (value) resolve(value);
        else reject(new Error("Nie udało się przygotować obrazu."));
      }, "image/webp", 0.85);
    });
    return { id: crypto.randomUUID(), blob, name: file.name.slice(0, 120), width, height };
  } finally {
    bitmap.close();
  }
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    let blocked = false;
    const request = indexedDB.open(DATABASE, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE);
    request.onsuccess = () => {
      if (blocked) request.result.close();
      else resolve(request.result);
    };
    request.onerror = () => reject(request.error);
    request.onblocked = () => {
      blocked = true;
      reject(new Error("Magazyn obrazów jest niedostępny."));
    };
  });
}
async function withStore<T>(
  mode: "readonly" | "readwrite",
  operation: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const db = await openDatabase();
  try {
    return await new Promise<T>((resolve, reject) => {
      const transaction = db.transaction(STORE, mode);
      const request = operation(transaction.objectStore(STORE));
      transaction.oncomplete = () => resolve(request.result);
      transaction.onabort = () => reject(transaction.error ?? request.error);
      transaction.onerror = () => reject(transaction.error ?? request.error);
    });
  } finally {
    db.close();
  }
}
export async function readBackgroundImage(): Promise<BackgroundImage | null> {
  const value: unknown = await withStore("readonly", store => store.get(KEY));
  if (!value || typeof value !== "object") return null;
  const image = value as Partial<BackgroundImage>;
  return typeof image.id === "string" && image.blob instanceof Blob &&
    typeof image.name === "string" && typeof image.width === "number" && typeof image.height === "number"
    ? image as BackgroundImage : null;
}
export const saveBackgroundImage = (image: BackgroundImage) =>
  withStore("readwrite", store => store.put(image, KEY));
export const deleteBackgroundImage = () =>
  withStore("readwrite", store => store.delete(KEY));
