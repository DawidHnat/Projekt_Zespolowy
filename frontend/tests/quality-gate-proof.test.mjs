import assert from "node:assert/strict";
import test from "node:test";

test("SCRUM-127 intentional failing test: never merge this proof branch", () => {
  assert.equal(1, 2, "Intentional CI gate proof, not a product requirement");
});
