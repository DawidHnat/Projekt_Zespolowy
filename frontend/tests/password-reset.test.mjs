import { test } from "node:test";
import assert from "node:assert/strict";
import {
  activationTokenFromHash,
  resetTokenFromHash,
  validResetToken,
} from "../src/features/auth/reset-model.ts";
test("reset link uses a fragment and accepts only bounded opaque tokens", () => {
  const token = "synthetic_token_1234567890";
  assert.equal(resetTokenFromHash("#reset-password?token=" + token), token);
  assert.equal(resetTokenFromHash("#dashboard"), null);
  assert.equal(resetTokenFromHash("#reset-password?token="), "");
  assert.equal(validResetToken(token), true);
  assert.equal(validResetToken("<script>"), false);
  assert.equal(validResetToken("a".repeat(101)), false);
});

test("activation links use a separate fragment from password reset links", () => {
  const token = "synthetic_token_1234567890";
  assert.equal(activationTokenFromHash("#activate-account?token=" + token), token);
  assert.equal(resetTokenFromHash("#activate-account?token=" + token), null);
  assert.equal(activationTokenFromHash("#reset-password?token=" + token), null);
  assert.equal(activationTokenFromHash("#activate-account?token="), "");
});
