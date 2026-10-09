import { test } from "node:test";
import assert from "node:assert/strict";
import { api, onSessionExpired } from "../src/shared/api/client.ts";
import { positionTime } from "../src/features/fleet/model/types.ts";

test("API uses same-origin cookies and never reflects provider errors", async () => {
  const saved = globalThis.fetch;
  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(url, "/api/v1/fleet/vehicles");
      assert.equal(options.credentials, "same-origin");
      return new Response(
        JSON.stringify({
          error: {
            code: "DATABASE_UNAVAILABLE",
            message: "secret-connection-details",
          },
        }),
        { status: 503 },
      );
    };
    await assert.rejects(
      api("/fleet/vehicles"),
      (e) => e.status === 503 && !e.message.includes("secret"),
    );
  } finally {
    globalThis.fetch = saved;
  }
});
test("401 clears authenticated state while invalid login does not broadcast expiration", async () => {
  const saved = globalThis.fetch;
  let calls = 0;
  const remove = onSessionExpired(() => calls++);
  try {
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ error: { code: "INVALID_CREDENTIALS" } }), {
        status: 401,
      });
    await assert.rejects(api("/auth/login", {}, false));
    assert.equal(calls, 0);
    await assert.rejects(api("/fleet/map"));
    assert.equal(calls, 1);
    remove();
    await assert.rejects(api("/fleet/map"));
    assert.equal(calls, 1);
  } finally {
    globalThis.fetch = saved;
    remove();
  }
});
test("API rejects external paths and timestamps use Warsaw DST", async () => {
  await assert.rejects(api("//other.example/path"));
  assert.match(positionTime("2026-01-10T12:00:00Z"), /13:00/);
  assert.match(positionTime("2026-07-10T12:00:00Z"), /14:00/);
  assert.equal(positionTime(null), "Brak pomiaru");
});
