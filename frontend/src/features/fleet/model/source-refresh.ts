export type SourceRefreshState = {
  enabled: boolean;
  running: boolean;
  server_time: string;
  next_allowed_at: string | null;
  retry_after_seconds: number;
};

export type SourceRefreshResult = SourceRefreshState & {
  result: "updated" | "cooldown" | "busy" | "failed" | "disabled";
};

// Use a monotonic browser deadline; the user's wall clock need not match the server.
export function refreshDeadline(state: SourceRefreshState, now: number) {
  const difference = Date.parse(state.next_allowed_at ?? "") - Date.parse(state.server_time);
  const delay = Number.isFinite(difference)
    ? Math.max(0, difference)
    : Math.max(0, state.retry_after_seconds * 1000);
  return now + (Number.isFinite(delay) ? delay : 0);
}

export function refreshSeconds(deadline: number, now: number) {
  return Math.max(0, Math.ceil((deadline - now) / 1000));
}
