import assert from "node:assert/strict";
import test from "node:test";

test("archive scope query omits default active and preserves explicit archived or all scopes", () => {
  const buildFilter = ({ q = "", status = "", archive = "active" }) =>
    new URLSearchParams({
      q,
      ...(status ? { status } : {}),
      ...(archive !== "active" ? { archive } : {}),
    }).toString();

  assert.equal(buildFilter({ q: "", status: "", archive: "active" }), "q=");
  assert.equal(buildFilter({ q: "GD", status: "", archive: "archived" }), "q=GD&archive=archived");
  assert.equal(buildFilter({ q: "", status: "stopped", archive: "all" }), "q=&status=stopped&archive=all");
});
