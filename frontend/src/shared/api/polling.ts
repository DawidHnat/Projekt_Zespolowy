type PollingEnvironment = {
  available: () => boolean;
  subscribe: (listener: () => void) => () => void;
  schedule: (callback: () => void, delay: number) => ReturnType<typeof setTimeout>;
  cancel: (timer: ReturnType<typeof setTimeout>) => void;
};

export function browserPollingEnvironment(): PollingEnvironment {
  return {
    available: () => document.visibilityState !== "hidden" && navigator.onLine,
    subscribe(listener) {
      document.addEventListener("visibilitychange", listener);
      window.addEventListener("online", listener);
      window.addEventListener("offline", listener);
      return () => {
        document.removeEventListener("visibilitychange", listener);
        window.removeEventListener("online", listener);
        window.removeEventListener("offline", listener);
      };
    },
    schedule: (callback, delay) => setTimeout(callback, delay),
    cancel: (timer) => clearTimeout(timer),
  };
}

/** One request group at a time. Delay starts after settlement, never during a request. */
export function startPolling(
  load: (signal: AbortSignal) => Promise<void>,
  environment: PollingEnvironment,
  onPause: () => void = () => {},
  interval = 60_000,
  maximumDelay = 300_000,
) {
  let disposed = false;
  let running = false;
  let requested = false;
  let failures = 0;
  let controller: AbortController | null = null;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const cancelTimer = () => {
    if (timer !== undefined) environment.cancel(timer);
    timer = undefined;
  };
  const run = async () => {
    if (disposed || running || !environment.available()) return;
    requested = false;
    running = true;
    const attempt = new AbortController();
    controller = attempt;
    try {
      await load(attempt.signal);
      if (!attempt.signal.aborted) failures = 0;
    } catch {
      if (!attempt.signal.aborted) {
        failures += 1;
        // Promise.all may reject before its other requests settle.
        attempt.abort();
      }
    } finally {
      running = false;
      controller = null;
      if (!disposed && environment.available()) {
        if (requested) void run();
        else timer = environment.schedule(refresh, Math.min(maximumDelay, interval * 2 ** failures));
      }
    }
  };
  const refresh = () => {
    cancelTimer();
    requested = true;
    void run();
  };
  const unsubscribe = environment.subscribe(() => {
    if (environment.available()) refresh();
    else {
      cancelTimer();
      requested = true;
      controller?.abort();
      onPause();
    }
  });
  refresh();
  return {
    refresh,
    dispose() {
      disposed = true;
      cancelTimer();
      controller?.abort();
      unsubscribe();
    },
  };
}
