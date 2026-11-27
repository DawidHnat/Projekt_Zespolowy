import { calendarDate } from "../../../shared/components/calendar-date.ts";

// Bounds and units mirror VehicleCardFieldsMixin (SCRUM-68).
export const vehicleCardNumberBounds = {
  year: [1900, 2100],
  engine_capacity_cc: [1, 100_000],
  power_kw: [1, 10_000],
  gross_weight_kg: [1, 120_000],
  curb_weight_kg: [1, 120_000],
  payload_kg: [1, 120_000],
  passenger_seats: [0, 120],
  axles: [1, 20],
} as const;
export type VehicleCardNumberField = keyof typeof vehicleCardNumberBounds;

export const dateFields = ["leasing_buyout_on", "first_registration_on", "first_registration_pl_on", "leasing_end_on", "inspection_due_on", "insurance_due_on", "manual_odometer_date"] as const;
type Field = VehicleCardNumberField | typeof dateFields[number];
type FieldError = "integer" | "range" | "calendar_date" | "registration_order" | "exceeds_gross_weight";

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
  const { first_registration_on, first_registration_pl_on } = dates;
  if (first_registration_on && first_registration_pl_on && first_registration_pl_on < first_registration_on) {
    errors.first_registration_pl_on = "registration_order";
  }
  const gross = Number(values.gross_weight_kg);
  if (!errors.gross_weight_kg && gross > 0) {
    for (const field of ["curb_weight_kg", "payload_kg"] as const) {
      if (!errors[field] && Number(values[field]) > gross) errors[field] = "exceeds_gross_weight";
    }
  }
  return errors;
}

const fieldMessages: Record<FieldError, string> = {
  integer: "Podaj liczbę całkowitą.",
  range: "Wartość jest poza dopuszczalnym zakresem.",
  calendar_date: "Podaj poprawną datę.",
  exceeds_gross_weight: "Wartość nie może przekraczać DMC.",
  registration_order: "Pierwsza rejestracja w Polsce nie może być wcześniejsza niż pierwsza rejestracja.",
};

export function vehicleCardFieldMessages(values: Parameters<typeof validateVehicleCardFields>[0]) {
  const messages: Record<string, string> = {};
  for (const [field, error] of Object.entries(validateVehicleCardFields(values))) {
    if (error === "range" && isVehicleCardNumberField(field)) {
      const [min, max] = vehicleCardNumberBounds[field];
      messages[field] = `Podaj wartość z zakresu ${min}–${max}.`;
    } else {
      messages[field] = fieldMessages[error];
    }
  }
  return messages;
}
