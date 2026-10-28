import test from "node:test";
import assert from "node:assert/strict";
import { startPolling } from "../src/shared/api/polling.ts";

const settled = () => new Promise(resolve => setImmediate(resolve));
function environment() {
  let available = true;
  let listener;
  let sequence = 0;
  const timers = new Map();
  return {
    timers,
    available: () => available,
    subscribe(callback) { listener = callback; return () => { listener = undefined; }; },
    schedule(callback, delay) { const id = ++sequence; timers.set(id, { callback, delay }); return id; },
    cancel: id => timers.delete(id),
    change(value) { available = value; listener?.(); },
    tick() {
      assert.equal(timers.size, 1);
      const [id, timer] = [...timers][0];
      timers.delete(id); timer.callback();
      return timer.delay;
    },
  };
}

test("hidden/offline polling pauses, aborts and resumes once without overlap", async () => {
  const env = environment();
  let finish;
  const signals = [];
  const poll = startPolling(signal => {
    signals.push(signal);
    return new Promise(resolve => { finish = resolve; });
  }, env);
  poll.refresh(); poll.refresh();
  assert.equal(signals.length, 1);
  env.change(false);
  assert.equal(signals[0].aborted, true);
  assert.equal(env.timers.size, 0);
  env.change(true); env.change(true);
  assert.equal(signals.length, 1); // The aborted operation must settle first.
  finish(); await settled();
  assert.equal(signals.length, 2);
  finish(); await settled();
  assert.equal(env.timers.size, 1);
  env.change(false);
  assert.equal(env.timers.size, 0);
  poll.refresh();
  assert.equal(signals.length, 2);
  env.change(true);
  assert.equal(signals.length, 3);
  poll.dispose();
  assert.equal(signals[2].aborted, true);
  finish(); await settled();
  assert.equal(env.timers.size, 0);
  env.change(true);
  assert.equal(signals.length, 3);
});

test("errors back off to a cap, manual retry is immediate and success resets the delay", async () => {
  const env = environment();
  let fails = true;
  let calls = 0;
  const poll = startPolling(async () => {
    calls++;
    if (fails) throw new Error("synthetic failure");
  }, env);
  await settled();
  assert.equal(env.tick(), 120_000); await settled();
  assert.equal(env.tick(), 240_000); await settled();
  assert.equal(env.tick(), 300_000); await settled();
  assert.equal(env.tick(), 300_000); await settled();
  fails = false;
  poll.refresh(); await settled();
  assert.equal(calls, 6);
  assert.equal(env.tick(), 60_000); await settled();
  poll.dispose();
});

test("filter/account cleanup cannot reschedule or complete an old polling generation", async () => {
  const env = environment();
  let finish;
  let oldSignal;
  const old = startPolling(signal => {
    oldSignal = signal;
    return new Promise(resolve => { finish = resolve; });
  }, env);
  old.dispose();
  let newCalls = 0;
  const current = startPolling(async () => { newCalls++; }, env);
  finish(); await settled();
  assert.equal(oldSignal.aborted, true);
  assert.equal(newCalls, 1);
  assert.equal(env.timers.size, 1);
  current.dispose();
});
