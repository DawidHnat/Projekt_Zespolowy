import { useEffect, useState } from "react";
import { Bell, RefreshCw } from "lucide-react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { EmptyState } from "../../../shared/components/EmptyState";
import { ListPagination } from "../../../shared/components/ListPagination";
import { useAlerts, type ReadFilter } from "../model/useAlerts";
import { AlertRows } from "./AlertRows";
import { RulesPanel } from "./RulesPanel";

export function AlertsPage() {
  const [read, setRead] = useState<ReadFilter>("all");
  const [page, setPage] = useState(1);
  const [pageSize, setSize] = useState(25);
  const alerts = useAlerts(read, page, pageSize);
  useEffect(() => { if (alerts.data && page > 1 && !alerts.data.items.length) setPage(1); }, [alerts.data, page]);
  return <div className="alerts-page">
    <WidgetFrame title="Alerty dziennego dystansu" icon={Bell}>
      <div className="alert-controls">
        <label>Stan odczytu<select aria-label="Stan odczytu alertów" value={read} disabled={!!alerts.saving}
          onChange={e => { setRead(e.target.value as ReadFilter); setPage(1); }}>
          <option value="all">Wszystkie</option><option value="unread">Nieprzeczytane</option><option value="read">Przeczytane</option>
        </select></label>
        <button className="button button-secondary" disabled={alerts.loading || !!alerts.saving} onClick={alerts.refresh}>
          <RefreshCw size={15} aria-hidden="true" />Odśwież
        </button>
      </div>
      <p className="alert-note">Odczyt zapisuje się dla Twojego konta. Przeczytany alert nie oznacza rozwiązania sprawy.</p>
      {alerts.loading && !alerts.data && <p role="status">Pobieranie alertów…</p>}
      {alerts.error && <p role="alert">{alerts.error}</p>}
      {alerts.saved && <p role="status">{alerts.saved}</p>}
      {alerts.data && <>
        {alerts.data.items.length ? <AlertRows items={alerts.data.items} saving={alerts.saving} onReceipt={item => void alerts.receipt(item)} /> :
          <EmptyState icon={Bell} title="Brak alertów w tym widoku" description="Zmień stan odczytu lub sprawdź reguły. Alert pojawi się po odebraniu pomiarów przekraczających próg." />}
        <ListPagination label="Alerty" page={page} pageSize={pageSize} total={alerts.data.total} loading={alerts.loading || !!alerts.saving}
          onPage={setPage} onPageSize={size => { setSize(size); setPage(1); }} />
      </>}
    </WidgetFrame>
    <RulesPanel onChanged={alerts.refresh} />
  </div>;
}
