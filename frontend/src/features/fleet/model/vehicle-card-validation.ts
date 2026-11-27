import { calendarDate } from "../../../shared/components/calendar-date.ts";

// Bounds and units mirror VehicleCardUpdate (SCRUM-68).
export const vehicleCardNumberBounds = {
  year: [1900, 2100],
  engine_capacity_cc: [1, 100_000],
  power_kw: [0, 10_000],
  dmc_kg: [1, 1_000_000],
  curb_weight_kg: [0, 1_000_000],
  payload_kg: [0, 1_000_000],
  seats: [1, 100],
  axles: [1, 20],
} as const;
export type VehicleCardNumberField = keyof typeof vehicleCardNumberBounds;

const dateFields = ["purchase_date", "first_registration", "first_registration_poland"] as const;
type Field = VehicleCardNumberField | typeof dateFields[number];
type FieldError = "integer" | "range" | "calendar_date" | "registration_order";

export function isVehicleCardNumberField(field: string): field is VehicleCardNumberField {
  return Object.hasOwn(vehicleCardNumberBounds, field);
}

/** Validate effective form values (saved values overlaid with edits).
 * Blank and null mean missing. Errors are keyed by the affected API field.
 */
export function validateVehicleCardFields(values: Partial<Record<Field, string | number | null>>) {
  const errors: Partial<Record<Field, FieldError>> = {};
  for (const field of Object.keys(vehicleCardNumberBounds).filter(isVehicleCardNumberField)) {
    const value = values[field];
    if (value == null || (typeof value === "string" && !value.trim())) continue;
    const number = typeof value === "number" ? value : Number(value);
    const [min, max] = vehicleCardNumberBounds[field];
    if ((typeof value === "string" && !/^-?\d+$/.test(value.trim())) || !Number.isInteger(number)) {
      errors[field] = "integer";
    } else if (number < min || number > max) {
      errors[field] = "range";
    }
  }
  const dates: Partial<Record<typeof dateFields[number], string>> = {};
  for (const field of dateFields) {
    const value = values[field];
    if (value == null || (typeof value === "string" && !value.trim())) continue;
    if (typeof value !== "string" || !calendarDate(value)) errors[field] = "calendar_date";
    else dates[field] = value;
  }
  const { first_registration, first_registration_poland } = dates;
  if (first_registration && first_registration_poland && first_registration_poland < first_registration) {
    errors.first_registration_poland = "registration_order";
  }
  return errors;
}
