import test from "node:test";
import assert from "node:assert/strict";
import { annotationDraft, annotationValidation, annotationError, tripDayRange, tripListPath } from "../src/features/trips/model/annotations.ts";

test("trip queries include the whole Polish day, including 23 and 25 hour DST days", () => {
  assert.deepEqual(tripDayRange("2026-03-29"), { from: "2026-03-28T23:00:00.000Z", to: "2026-03-29T22:00:00.000Z" });
  assert.deepEqual(tripDayRange("2026-10-25"), { from: "2026-10-24T22:00:00.000Z", to: "2026-10-25T23:00:00.000Z" });
  assert.deepEqual(tripDayRange("2026-01-01"), { from: "2025-12-31T23:00:00.000Z", to: "2026-01-01T23:00:00.000Z" });
  assert.throws(() => tripDayRange("2026-02-30"));
  const query = new URL(tripListPath("id&other=bad", "2026-10-25", 2, 10), "https://example.test").searchParams;
  assert.equal(query.get("vehicle_id"), "id&other=bad");
  assert.equal(query.get("page"), "2");
  assert.equal(query.get("page_size"), "10");
  assert.equal(query.has("other"), false);
});

test("annotation validation accepts Polish multiline text and emoji but rejects unsafe or excessive input", () => {
  assert.deepEqual(annotationDraft({ purpose: null, description: null }), { purpose: "", description: "" });
  assert.equal(annotationValidation({ purpose: "Odbiór 🚚", description: "Zażółć\nDrugi wiersz" }), null);
  assert.equal(annotationValidation({ purpose: "🚚".repeat(200), description: "x".repeat(2000) }), null);
  for (const purpose of ["x".repeat(201), "a\nb", "a\rb", "a\x00b", "a\ud800b"]) {
    assert.ok(annotationValidation({ purpose, description: "" }));
  }
  assert.ok(annotationValidation({ purpose: "", description: "x".repeat(2001) }));
  assert.equal(annotationValidation({ purpose: "", description: "" }), null);
});

test("save failures explain retained text without reflecting server internals", () => {
  for (const code of ["VERSION_CONFLICT", "FORBIDDEN", "VALIDATION_ERROR", "NOT_FOUND", "UNKNOWN"]) {
    const message = annotationError({ code, message: "private SQL error" });
    assert.match(message, /pozostał w formularzu/);
    assert.doesNotMatch(message, /SQL|private/);
  }
  assert.match(annotationError(new TypeError("fetch failed")), /Spróbuj ponownie/);
});
