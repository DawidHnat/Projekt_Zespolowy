import { useEffect, useRef, useState } from "react";
import { api } from "../../../shared/api/client";
import type { Alert, AlertList, Receipt } from "../../../shared/api/generated/contracts";
import { browserPollingEnvironment, startPolling } from "../../../shared/api/polling";

export type ReadFilter = "all" | "unread" | "read";

export function useAlerts(read: ReadFilter, page: number, pageSize: number) {
  const [data, setData] = useState<AlertList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [writeError, setWriteError] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [revision, setRevision] = useState(0);
  const poll = useRef<ReturnType<typeof startPolling> | null>(null);
  const write = useRef<AbortController | null>(null);
  useEffect(() => () => { write.current?.abort(); }, []);
  useEffect(() => { setData(null); setSaved(null); setWriteError(null); }, [read, page, pageSize]);
  useEffect(() => {
    const query = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (read !== "all") query.set("read", String(read === "read"));
    const controller = startPolling(async signal => {
      setLoading(true);
      try {
        const result = await api<AlertList>(`/analytics/alerts?${query}`, { signal });
        if (!signal.aborted) { setData(result); setError(null); }
      } catch (err) {
        if (!signal.aborted) setError(err instanceof Error ? err.message : "Nie można pobrać alertów.");
        throw err;
      } finally { if (!signal.aborted) setLoading(false); }
    }, browserPollingEnvironment(), () => setLoading(false));
    poll.current = controller;
    return () => controller.dispose();
  }, [read, page, pageSize, revision]);
  const receipt = async (alert: Alert) => {
    if (write.current) return;
    const controller = new AbortController();
    write.current = controller;
    setSaving(alert.id); setWriteError(null); setSaved(null);
    // An earlier GET must not overwrite the confirmed receipt.
    poll.current?.dispose();
    try {
      await api<Receipt>(`/analytics/alerts/${alert.id}/receipt`, {
        method: "PATCH", signal: controller.signal, body: JSON.stringify({ read: !alert.read_at }),
      });
      if (!controller.signal.aborted) setSaved(alert.read_at ? "Oznaczono jako nieprzeczytany." : "Oznaczono jako przeczytany.");
    } catch {
      if (!controller.signal.aborted) setWriteError("Nie udało się potwierdzić zapisu odczytu. Sprawdź bieżący stan i spróbuj ponownie.");
    } finally {
      write.current = null;
      if (!controller.signal.aborted) { setSaving(null); setRevision(v => v + 1); }
    }
  };
  return { data, loading, error: writeError || error, saving, saved, receipt, refresh: () => poll.current?.refresh() };
}
