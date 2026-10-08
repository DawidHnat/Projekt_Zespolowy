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
import { VehicleListWidget } from "../../fleet/components/VehicleListWidget";
import { MetricsWidget } from "../../analytics/components/MetricsWidget";
import { ActivityWidget } from "../../analytics/components/ActivityWidget";
import { UtilizationWidget } from "../../analytics/components/UtilizationWidget";
import { TripsWidget } from "../../trips/components/TripsWidget";
import type { SectionId, WidgetId, WidgetProps } from "./widget-types";

type WidgetDefinition = {
  title: string;
  description: string;
  icon: LucideIcon;
  sections: SectionId[];
  component: ComponentType<WidgetProps>;
};
export const widgetRegistry: Record<WidgetId, WidgetDefinition> = {
  metrics: {
    title: "Przegląd floty",
    description: "Cztery najważniejsze wskaźniki",
    icon: ChartNoAxesCombined,
    sections: ["dashboard", "fleet", "analytics"],
    component: MetricsWidget,
  },
  map: {
    title: "Mapa floty",
    description: "Pozycje pojazdów",
    icon: Map,
    sections: ["dashboard", "fleet"],
    component: FleetMapWidget,
  },
  activity: {
    title: "Alerty i aktywność",
    description: "Zdarzenia i wybrane parametry",
    icon: Activity,
    sections: ["dashboard", "analytics"],
    component: ActivityWidget,
  },
  vehicles: {
    title: "Pojazdy",
    description: "Lista i statusy floty",
    icon: Truck,
    sections: ["dashboard", "fleet"],
    component: VehicleListWidget,
  },
  utilization: {
    title: "Wykorzystanie floty",
    description: "Podsumowanie aktywności pojazdów",
    icon: CircleGauge,
    sections: ["dashboard", "analytics"],
    component: UtilizationWidget,
  },
  trips: {
    title: "Ostatnie przejazdy",
    description: "Historia i ewidencja przebiegu",
    icon: Route,
    sections: ["dashboard", "trips"],
    component: TripsWidget,
  },
};
