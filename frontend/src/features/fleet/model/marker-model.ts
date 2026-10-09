export type ProjectedVehicle = { id: string; x: number; y: number };
// This is a click hit area, not clustering: every marker stays on the map.
export function vehiclesAtPoint(
  vehicles: ProjectedVehicle[],
  point: { x: number; y: number },
  radius = 18,
) {
  return vehicles
    .filter((v) => Math.hypot(v.x - point.x, v.y - point.y) <= radius)
    .map((v) => v.id);
}
