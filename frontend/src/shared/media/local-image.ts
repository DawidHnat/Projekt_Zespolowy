import { fitImage, validateImageFile, MAX_IMAGE_EDGE } from "./image-model.ts";

export type LocalImage = {
  id: string;
  blob: Blob;
  name: string;
  width: number;
  height: number;
};

// Re-encode locally: neither EXIF nor original file bytes enter storage or requests.
export async function prepareLocalImage(
  file: File,
  maxEdge = MAX_IMAGE_EDGE,
): Promise<LocalImage> {
  validateImageFile(file);
  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    throw new Error("Nie udało się odczytać obrazu. Wybierz inny plik.");
  }
  try {
    const { width, height } = fitImage(bitmap.width, bitmap.height, maxEdge);
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    if (!context)
      throw new Error("Ta przeglądarka nie obsługuje przygotowania zdjęcia.");
    context.fillStyle = "#e5ecf4";
    context.fillRect(0, 0, width, height);
    context.drawImage(bitmap, 0, 0, width, height);
    const blob = await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob(
        (value) => {
          if (value) resolve(value);
          else reject(new Error("Nie udało się przygotować obrazu."));
        },
        "image/webp",
        0.85,
      ),
    );
    return {
      id: crypto.randomUUID(),
      blob,
      name: file.name.slice(0, 120),
      width,
      height,
    };
  } finally {
    bitmap.close();
  }
}
