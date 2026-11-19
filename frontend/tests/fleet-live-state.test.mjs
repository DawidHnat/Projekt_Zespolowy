import test from "node:test";
import assert from "node:assert/strict";
import { fleetUtilization } from "../src/features/analytics/model/utilization.ts";
import { refreshDeadline, refreshSeconds } from "../src/features/fleet/model/source-refresh.ts";

const summary = { total: 5, moving: 2, stopped: 1, offline: 1, unknown: 1,
  source: { status: "ok", last_success_at: null, error_code: null } };

test("utilization uses the whole summary and groups uncertain vehicles separately from stopped", () => {
  const values = fleetUtilization(summary);
  assert.equal(values.moving, 2);
  assert.equal(values.stopped, 1);
  assert.equal(values.others, 2);
  assert.equal(values.percentage, "40%");
  assert.equal(values.movingShare, 40);
  assert.equal(values.stoppedEnd, 60);
});

test("missing, empty and wholly unconfirmed fleets have distinct states", () => {
  assert.equal(fleetUtilization(null), null);
  assert.equal(fleetUtilization({ ...summary, moving: 9 }), null);
  const empty = fleetUtilization({ ...summary, total: 0, moving: 0, stopped: 0, offline: 0, unknown: 0 });
  assert.equal(empty.percentage, "0");
  assert.equal(empty.total, 0);
  const unknown = fleetUtilization({ ...summary, moving: 0, stopped: 0, offline: 3, unknown: 2 });
  assert.equal(unknown.percentage, "—");
  assert.equal(unknown.others, 5);
  const degraded = fleetUtilization({ ...summary, source: { ...summary.source, status: "degraded" } });
  assert.equal(degraded.current, false);
  assert.equal(degraded.percentage, "—");
  assert.equal(fleetUtilization({ ...summary, total: 1000, moving: 1, stopped: 999, offline: 0, unknown: 0 }).percentage, "<1%");
});

test("cooldown follows the server duration and a monotonic clock, including expiry and provider backoff", () => {
  const state = { enabled: true, running: false, server_time: "2030-05-01T10:00:00Z",
    next_allowed_at: "2030-05-01T10:01:00Z", retry_after_seconds: 60 };
  const deadline = refreshDeadline(state, 500);
  assert.equal(deadline, 60_500);
  assert.equal(refreshSeconds(deadline, 500), 60);
  assert.equal(refreshSeconds(deadline, 30_500), 30);
  assert.equal(refreshSeconds(deadline, 60_499), 1);
  assert.equal(refreshSeconds(deadline, 60_500), 0);
  assert.equal(refreshSeconds(deadline, 100_000), 0);
  assert.equal(refreshDeadline({ ...state, next_allowed_at: null, retry_after_seconds: 1200 }, 500), 1_200_500);
});
