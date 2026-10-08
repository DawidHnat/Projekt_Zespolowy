import type { FleetFeature, FleetMap } from "./types.ts";
export function validFeatures(data: FleetMap | null): FleetFeature[] {
  return (data?.features || []).filter(({ geometry, properties }) => {
    const [lng, lat] = geometry.coordinates;
    return (
      Number.isFinite(lng) &&
      Number.isFinite(lat) &&
      Math.abs(lng) <= 180 &&
      Math.abs(lat) <= 90 &&
      typeof properties.id === "string"
    );
  });
}
export function boundsForFeatures(
  features: FleetFeature[],
): [[number, number], [number, number]] | null {
  if (!features.length) return null;
  const lng = features.map((f) => f.geometry.coordinates[0]);
  const lat = features.map((f) => f.geometry.coordinates[1]);
  return [
    [Math.min(...lng), Math.min(...lat)],
    [Math.max(...lng), Math.max(...lat)],
  ];
}
