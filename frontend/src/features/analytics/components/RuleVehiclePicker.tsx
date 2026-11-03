import { VehiclePicker } from "../../fleet/components/VehiclePicker";
import type { ComponentProps } from "react";
export function RuleVehiclePicker(props: ComponentProps<typeof VehiclePicker>) {
  return (
    <VehiclePicker
      {...props}
      legend="Pojazd reguły"
      paginationLabel="Wybór pojazdu reguły"
    />
  );
}
