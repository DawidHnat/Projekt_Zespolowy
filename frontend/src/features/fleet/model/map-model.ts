import type { FleetFeature, FleetMap } from "./types.ts";

export function mapEmptyState(
  data: FleetMap | null,
  loading: boolean,
  error: string | null,
  filtered: boolean,
) {
  if (validFeatures(data).length) return null;
  if (error)
    return {
      title: "Dane floty niedostępne",
      description: error,
      action: "retry" as const,
    };
  if (loading)
    return {
      title: "Pobieranie pojazdów…",
      description: "Pozycje pojawią się po pobraniu danych floty.",
      action: null,
    };
  if (!data)
    return {
      title: "Oczekiwanie na dane floty",
      description: "Mapa pokaże pozycje po pierwszej udanej synchronizacji.",
      action: "retry" as const,
    };
  if (!data.total)
    return filtered
      ? {
          title: "Brak wyników",
          description: "Żaden pojazd nie pasuje do wybranych filtrów.",
          action: "clear" as const,
        }
      : {
          title: "Flota jest pusta",
          description: "Nie ma jeszcze pojazdów do wyświetlenia.",
          action: null,
        };
  return {
    title: "Brak pozycji GPS",
    description: "Pojazdy są dostępne na liście, ale nie mają poprawnej pozycji GPS.",
    action: null,
  };
}

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
