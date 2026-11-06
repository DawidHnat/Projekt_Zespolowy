import test from "node:test";
import assert from "node:assert/strict";
import { calendarDate, calendarValue, displayCalendarDate } from "../src/shared/components/calendar-date.ts";

test("calendar days round trip in local time, including DST boundaries and leap days", () => {
  for (const day of ["2026-03-29", "2026-10-25", "2024-02-29", "2026-12-31", "0099-01-01"]) {
    assert.equal(calendarValue(calendarDate(day)), day);
  }
  for (const day of ["2026-02-29", "2026-02-31", "2026-13-01", "2026-00-10", "0000-01-01", "2026-1-1", "invalid", ""]) {
    assert.equal(calendarDate(day), undefined);
  }
});

test("displayed dates use Polish formatting without inventing missing or invalid days", () => {
  assert.equal(displayCalendarDate("2026-10-27"), "27.10.2026");
  assert.equal(displayCalendarDate("2024-02-29"), "29.02.2024");
  assert.equal(displayCalendarDate("0099-01-01"), "01.01.0099");
  assert.equal(displayCalendarDate("2026-02-29"), "");
  assert.equal(displayCalendarDate(""), "");
});
