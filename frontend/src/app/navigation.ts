import {
  Bell,
  CarFront,
  BookOpen,
  CreditCard,
  LayoutDashboard,
  MapPinned,
  Users,
  Wrench,
  Settings,
} from "lucide-react";

// Page IDs are independent of the persisted dashboard layout groups.
export const sections = [
  {
    id: "dashboard",
    title: "Pulpit",
    icon: LayoutDashboard,
    description: "Najważniejsze informacje o flocie, ułożone po Twojemu.",
  },
  {
    id: "map",
    title: "Mapa",
    icon: MapPinned,
    description: "Pozycje i lista pojazdów w jednym widoku.",
  },
  {
    id: "vehicles",
    title: "Pojazdy",
    icon: CarFront,
    description: "Twoje pojazdy, zdjęcia i kafelki o wybranym rozmiarze.",
  },
  {
    id: "service",
    title: "Serwis",
    icon: Wrench,
    description: "Wymiany oleju, filtrów i nadchodzące przeglądy.",
    placeholder: {
      title: "Przeglądy pod kontrolą",
      description:
        "Tu pojawią się nadchodzące serwisy, interwały ustalane dla każdego pojazdu i lista wykonanych wymian oleju oraz filtrów.",
    },
  },
  {
    id: "mileage",
    title: "Ewidencja przebiegu",
    icon: BookOpen,
    description: "Kilometrówka i dokumentowanie przebiegu pojazdów.",
    placeholder: {
      title: "Każdy kilometr na swoim miejscu",
      description:
        "Tu przygotujesz ewidencję przebiegu: daty, trasy, cele przejazdów i kilometry przypisane do pojazdu.",
    },
  },
  {
    id: "drivers",
    title: "Kierowcy",
    icon: Users,
    description: "Ręczna kartoteka kierowców, kontakt i historia przypisań.",
  },
  {
    id: "fuel-cards",
    title: "Karty paliwowe",
    icon: CreditCard,
    description: "Karty i informacje potrzebne do ich obsługi.",
    placeholder: {
      title: "Karty uporządkowane w jednym miejscu",
      description:
        "Tu znajdą się informacje o kartach paliwowych, ich operatorach, ważności i przypisaniach do pojazdów lub kierowców.",
    },
  },
  {
    id: "alerts",
    title: "Alerty",
    icon: Bell,
    description: "Przekroczenia dziennego dystansu, reguły i Twój stan odczytu.",
  },
  {
    id: "settings",
    title: "Ustawienia",
    icon: Settings,
    description: "Wygląd, tło i konfiguracja Twojej przestrzeni pracy.",
  },
] as const;

export type AppSection = (typeof sections)[number];
export type AppSectionId = AppSection["id"];

const legacySections: Record<string, AppSectionId> = {
  fleet: "map",
  trips: "mileage",
  analytics: "dashboard",
};

export function sectionFromHash(hash: string): AppSectionId {
  const id = hash.replace(/^#/, "");
  return (
    sections.find((section) => section.id === id)?.id ??
    (Object.hasOwn(legacySections, id) ? legacySections[id] : "dashboard")
  );
}
