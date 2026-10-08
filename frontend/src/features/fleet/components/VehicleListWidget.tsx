import { Truck } from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { EmptyState } from "../../../shared/components/EmptyState";

export function VehicleListWidget({
  variant = "table",
}: {
  variant?: "table" | "sidebar";
}) {
  return (
    <WidgetFrame
      title="Pojazdy"
      icon={Truck}
      badge="Lista floty"
      className="vehicles-widget"
    >
      {variant === "sidebar" ? (
        <EmptyState
          icon={Truck}
          title="Twoje pojazdy pojawią się tutaj"
          description="Lista będzie dostępna obok mapy. Wybór pojazdu pozwoli odnaleźć jego pozycję."
        />
      ) : (
        <div className="table-scroll">
          <table className="vehicle-table">
            <thead>
              <tr>
                <th>Pojazd</th>
                <th>Status</th>
                <th>Kierowca</th>
                <th>Przebieg</th>
                <th>Aktualizacja</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={5}>
                  <EmptyState
                    icon={Truck}
                    title="Twoje pojazdy pojawią się tutaj"
                    description="Lista, statusy i najważniejsze informacje o flocie w jednym miejscu."
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </WidgetFrame>
  );
}

export function VehicleSidebarWidget() {
  return <VehicleListWidget variant="sidebar" />;
}
