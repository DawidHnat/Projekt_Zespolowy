import test from "node:test";
import assert from "node:assert/strict";
import { passwordChangeValidation, profileError, profileRole } from "../src/features/auth/profile-model.ts";
import { sectionFromHash } from "../src/app/navigation.ts";

test("password validation preserves whitespace, handles Unicode and enforces bounds and confirmation", () => {
  assert.equal(passwordChangeValidation("old", "  hasło testowe  ", "  hasło testowe  "), null);
  assert.equal(passwordChangeValidation("old", "🚚".repeat(12), "🚚".repeat(12)), null);
  assert.ok(passwordChangeValidation("old", "🚚".repeat(6), "🚚".repeat(6)));
  assert.ok(passwordChangeValidation("", "new-long-password", "new-long-password"));
  assert.ok(passwordChangeValidation("old", "short", "short"));
  assert.ok(passwordChangeValidation("old", "new-long-password", "different-password"));
  assert.ok(passwordChangeValidation("old-long-password", "old-long-password", "old-long-password"));
  assert.ok(passwordChangeValidation("old", "x".repeat(1025), "x".repeat(1025)));
});

test("profile errors do not reflect secrets and profile links work directly", () => {
  for (const code of ["INVALID_CURRENT_PASSWORD", "PASSWORD_UNCHANGED", "RATE_LIMITED", "VALIDATION_ERROR", "UNKNOWN"]) {
    assert.doesNotMatch(profileError({ code, message: "private-password-token-SQL" }), /private|token|SQL/);
  }
  assert.equal(profileRole("viewer"), "Tylko odczyt");
  assert.equal(profileRole("__proto__"), "Nieznana rola");
  assert.equal(profileRole("toString"), "Nieznana rola");
  assert.equal(sectionFromHash("#profile"), "profile");
});
