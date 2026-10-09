import type { ComponentType } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  ChartNoAxesCombined,
  CircleGauge,
  Map,
  Route,
  Truck,
} from "lucide-react";
import { FleetMapWidget } from "../../fleet/components/FleetMapWidget";
import { VehicleListWidget, VehicleSidebarWidget } from "../../fleet/components/VehicleListWidget";
import { MetricsWidget } from "../../analytics/components/MetricsWidget";
import { ActivityWidget } from "../../analytics/components/ActivityWidget";
import { UtilizationWidget } from "../../analytics/components/UtilizationWidget";
import { TripsWidget } from "../../trips/components/TripsWidget";
import type { SectionId, WidgetId } from "./widget-types";

import { SECTION_IDS, SECTION_WIDGETS } from "./widget-layout";

const sectionsFor = (id: WidgetId) =>
  SECTION_IDS.filter((section) => SECTION_WIDGETS[section].includes(id));

type WidgetDefinition = {
  title: string;
  description: string;
  icon: LucideIcon;
  sections: SectionId[];
  component: ComponentType;
  presentations?: Partial<Record<SectionId, ComponentType>>;
};
export const widgetRegistry: Record<WidgetId, WidgetDefinition> = {
  metrics: {
    title: "Przegląd floty",
    description: "Cztery najważniejsze wskaźniki",
    icon: ChartNoAxesCombined,
    sections: sectionsFor("metrics"),
    component: MetricsWidget,
  },
  map: {
    title: "Mapa floty",
    description: "Pozycje pojazdów",
    icon: Map,
    sections: sectionsFor("map"),
    component: FleetMapWidget,
  },
  activity: {
    title: "Alerty i aktywność",
    description: "Zdarzenia i wybrane parametry",
    icon: Activity,
    sections: sectionsFor("activity"),
    component: ActivityWidget,
  },
  vehicles: {
    title: "Pojazdy",
    description: "Lista i statusy floty",
    icon: Truck,
    sections: sectionsFor("vehicles"),
    component: VehicleListWidget,
    presentations: { map: VehicleSidebarWidget },
  },
  utilization: {
    title: "Wykorzystanie floty",
    description: "Podsumowanie aktywności pojazdów",
    icon: CircleGauge,
    sections: sectionsFor("utilization"),
    component: UtilizationWidget,
  },
  trips: {
    title: "Ostatnie przejazdy",
    description: "Historia i ewidencja przebiegu",
    icon: Route,
    sections: sectionsFor("trips"),
    component: TripsWidget,
  },
};
