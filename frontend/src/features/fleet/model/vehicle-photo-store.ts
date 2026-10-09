import type { LocalImage } from "../../../shared/media/local-image";
import { validVehicleId } from "./vehicle-layout";
type PhotoRow = { vehicleId: string; image: LocalImage };
const database = "fleet-flow.vehicle-photos.v1";
const storeName = "photos";
const key = (scope: string, vehicleId: string) => `${scope}:${vehicleId}`;

function open(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    let blocked = false;
    const request = indexedDB.open(database, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(storeName);
    request.onsuccess = () => {
      if (blocked) request.result.close();
      else resolve(request.result);
    };
    request.onerror = () => reject(request.error);
    request.onblocked = () => {
      blocked = true;
      reject(new Error("Magazyn zdjęć jest niedostępny."));
    };
  });
}
async function run<T>(
  mode: IDBTransactionMode,
  action: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const db = await open();
  try {
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(storeName, mode);
      const request = action(tx.objectStore(storeName));
      tx.oncomplete = () => resolve(request.result);
      tx.onabort = tx.onerror = () => reject(tx.error ?? request.error);
    });
  } finally {
    db.close();
  }
}
export async function readVehiclePhotos(scope: string): Promise<PhotoRow[]> {
  const rows: unknown[] = await run("readonly", (store) =>
    store.getAll(IDBKeyRange.bound(`${scope}:`, `${scope}:\uffff`)),
  );
  return rows.filter((value): value is PhotoRow => {
    if (!value || typeof value !== "object") return false;
    const row = value as Partial<PhotoRow>;
    return (
      typeof row.vehicleId === "string" &&
      validVehicleId(row.vehicleId) &&
      !!row.image &&
      typeof row.image.id === "string" &&
      row.image.blob instanceof Blob &&
      ["image/webp", "image/jpeg", "image/png"].includes(row.image.blob.type)
    );
  });
}
export const saveVehiclePhoto = (
  scope: string,
  vehicleId: string,
  image: LocalImage,
) =>
  run("readwrite", (store) =>
    store.put({ vehicleId, image }, key(scope, vehicleId)),
  );
export const deleteVehiclePhoto = (scope: string, vehicleId: string) =>
  run("readwrite", (store) => store.delete(key(scope, vehicleId)));
