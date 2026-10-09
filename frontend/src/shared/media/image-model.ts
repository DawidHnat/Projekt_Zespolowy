export const MAX_IMAGE_BYTES = 10 * 1024 * 1024;
export const MAX_IMAGE_PIXELS = 40_000_000;
export const MAX_IMAGE_EDGE = 2560;

export function validateImageFile(file: Pick<File, "size" | "type">) {
  if (!["image/jpeg", "image/png", "image/webp"].includes(file.type))
    throw new Error("Wybierz zdjęcie JPG, PNG lub WebP.");
  if (!file.size || file.size > MAX_IMAGE_BYTES)
    throw new Error("Wybierz obraz o rozmiarze do 10 MB.");
}
export function fitImage(
  width: number,
  height: number,
  maxEdge = MAX_IMAGE_EDGE,
) {
  if (
    !Number.isFinite(width) ||
    !Number.isFinite(height) ||
    width <= 0 ||
    height <= 0 ||
    width * height > MAX_IMAGE_PIXELS
  )
    throw new Error("Obraz jest zbyt duży. Wybierz zdjęcie do 40 megapikseli.");
  const scale = Math.min(1, maxEdge / Math.max(width, height));
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale)),
  };
}
