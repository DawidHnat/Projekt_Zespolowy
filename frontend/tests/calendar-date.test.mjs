import test from "node:test";
import assert from "node:assert/strict";
import { calendarDate, calendarValue, displayCalendarDate, calendarInputError, calendarInputValue } from "../src/shared/components/calendar-date.ts";

test("calendar days round trip in local time, including DST boundaries and leap days", () => {
  for (const day of ["2026-03-29", "2026-10-25", "2024-02-29", "2026-12-31", "0099-01-01"]) {
    assert.equal(calendarValue(calendarDate(day)), day);
  }
  for (const day of ["2026-02-29", "2026-02-31", "2026-13-01", "2026-00-10", "0000-01-01", "2026-1-1", "invalid", ""]) {
    assert.equal(calendarDate(day), undefined);
  }
});

test("typed dates cannot roll into another month, escape limits or erase a required day", () => {
  assert.equal(displayCalendarDate("2026-10-27"), "27.10.2026");
  assert.equal(calendarInputValue("25.10.2026"), "2026-10-25");
  assert.equal(calendarInputValue("31.02.2026"), undefined);
  assert.equal(calendarInputValue(" "), "");
  assert.equal(calendarInputError("27.10.2026", { minDate: "2026-10-27", maxDate: "2026-10-27" }), "");
  assert.match(calendarInputError("31.02.2026", {}), /poprawną datę/);
  assert.match(calendarInputError("2026-10-27", {}), /DD.MM.RRRR/);
  assert.match(calendarInputError("26.10.2026", { minDate: "2026-10-27" }), /Najwcześniejsza/);
  assert.match(calendarInputError("28.10.2026", { maxDate: "2026-10-27" }), /Najpóźniejsza/);
  assert.match(calendarInputError("", { required: true }), /Wybierz datę/);
  assert.equal(calendarInputError("", {}), "");
});
