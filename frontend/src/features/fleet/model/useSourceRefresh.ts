import { useEffect, useRef, useState } from "react";
import { api } from "../../../shared/api/client";
import { browserPollingEnvironment, startPolling } from "../../../shared/api/polling";
import { refreshDeadline, refreshSeconds, type SourceRefreshState,
  type SourceRefreshResult } from "./source-refresh";

export function useSourceRefresh(refreshCache: () => void, interval: number) {
  const [state, setState] = useState<SourceRefreshState | null>(null);
  const [deadline, setDeadline] = useState(0);
  const [pending, setPending] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
  const [message, setMessage] = useState<string | null>(null);
  const readPoll = useRef<ReturnType<typeof startPolling> | null>(null);
  const action = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const mounted = useRef(false);
  const onRefresh = useRef(refreshCache);
  onRefresh.current = refreshCache;

  const accept = (next: SourceRefreshState) => {
    setState(next);
    setDeadline(refreshDeadline(next, performance.now()));
    setUnavailable(false);
  };

  useEffect(() => {
    mounted.current = true;
    const connection = () => setOnline(navigator.onLine);
    window.addEventListener("online", connection);
    window.addEventListener("offline", connection);
    const poll = startPolling(async signal => {
      const version = generation.current;
      try {
        const next = await api<SourceRefreshState>("/fleet/refresh", { signal });
        if (!signal.aborted && version === generation.current) accept(next);
      } catch (error) {
        if (!signal.aborted && version === generation.current) setUnavailable(true);
        throw error;
      }
    }, browserPollingEnvironment(), undefined, interval);
    readPoll.current = poll;
    return () => {
      mounted.current = false;
      poll.dispose();
      readPoll.current = null;
      action.current?.abort();
      window.removeEventListener("online", connection);
      window.removeEventListener("offline", connection);
    };
  }, [interval]);

  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(() => setMessage(null), 6000);
    return () => clearTimeout(timer);
  }, [message]);

  const run = async () => {
    if (action.current) return;
    if (!navigator.onLine) { setMessage("Brak połączenia z siecią."); return; }
    if (!state || unavailable) {
      setMessage("Sprawdzam dostępność odświeżania…");
      readPoll.current?.refresh();
      return;
    }
    if (!state.enabled) { setMessage("Synchronizacja jest wyłączona."); return; }
    if (state.running) { setMessage("Odświeżanie już trwa."); return; }
    const remaining = refreshSeconds(deadline, performance.now());
    if (remaining) { setMessage("Poczekaj na koniec odliczania."); return; }
    const controller = new AbortController();
    action.current = controller;
    generation.current += 1;
    setPending(true);
    setMessage("Pobieranie danych…");
    try {
      const result = await api<SourceRefreshResult>("/fleet/refresh", {
        method: "POST", signal: controller.signal,
      });
      if (controller.signal.aborted || !mounted.current) return;
      generation.current += 1;
      accept(result);
      const messages: Record<SourceRefreshResult["result"], string> = {
        updated: "Sprawdzono najnowsze dane floty.",
        cooldown: "Poczekaj na koniec odliczania.",
        busy: "Odświeżanie już trwa.",
        failed: "Odczyt się nie udał. Zachowaliśmy ostatnie dane.",
        disabled: "Synchronizacja jest wyłączona.",
      };
      setMessage(messages[result.result]);
      onRefresh.current();
    } catch {
      if (!controller.signal.aborted && mounted.current) {
        generation.current += 1;
        setMessage("Odczyt się nie udał. Zachowaliśmy ostatnie dane.");
        onRefresh.current();
      }
    } finally {
      if (action.current === controller) action.current = null;
      if (mounted.current && !controller.signal.aborted) {
        setPending(false);
        readPoll.current?.refresh();
      }
    }
  };

  return { state, deadline, pending, unavailable, online, message, run };
}
