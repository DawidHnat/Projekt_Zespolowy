import { useEffect, useRef, useState } from "react";
import { Settings2 } from "lucide-react";
import { api, ApiError } from "../../../shared/api/client";
import type { Rule, RuleList } from "../../../shared/api/generated/contracts";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";
import { ListPagination } from "../../../shared/components/ListPagination";
import { useAuth } from "../../auth/AuthProvider";
import { useFleet } from "../../fleet/model/FleetProvider";
import { RuleVehiclePicker } from "./RuleVehiclePicker";

export function RulesPanel({ onChanged }: { onChanged: () => void }) {
  const { user } = useAuth();
  const fleet = useFleet();
  const canEdit = user?.role === "admin" || user?.role === "editor";
  const [data, setData] = useState<RuleList | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setSize] = useState(10);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [editing, setEditing] = useState<Rule | "new" | null>(null);
  const [threshold, setThreshold] = useState("");
  const [active, setActive] = useState(true);
  const [scope, setScope] = useState("fleet");
  const [vehicle, setVehicle] = useState<{ id: string; name: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const thresholdInput = useRef<HTMLInputElement>(null);
  const write = useRef<AbortController | null>(null);
  const opener = useRef<HTMLButtonElement | null>(null);
  useEffect(() => () => write.current?.abort(), []);
  useEffect(() => { if (editing) thresholdInput.current?.focus(); }, [editing]);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null);
    api<RuleList>(`/analytics/rules?page=${page}&page_size=${pageSize}`, { signal: controller.signal })
      .then(result => { if (!controller.signal.aborted) setData(result); })
      .catch(() => { if (!controller.signal.aborted) setError("Nie można pobrać reguł. Ponów odczyt."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [page, pageSize, revision]);
  const edit = (rule: Rule | "new", button: HTMLButtonElement) => {
    opener.current = button;
    setEditing(rule); setSaved(false); setError(null);
    setThreshold(rule === "new" ? "" : String(rule.threshold_km));
    setActive(rule === "new" ? true : rule.active);
    setScope(rule !== "new" && rule.vehicle_id ? "vehicle" : "fleet");
    setVehicle(rule !== "new" && rule.vehicle_id ? { id: rule.vehicle_id, name: rule.vehicle_name || "Przypisany pojazd" } : null);
  };
  const save = async () => {
    if (!editing || busy) return;
    if (scope === "vehicle" && !vehicle) { setError("Wybierz pojazd reguły."); return; }
    setBusy(true); setError(null); setSaved(false);
    const controller = new AbortController();
    write.current = controller;
    try {
      await api<Rule>(editing === "new" ? "/analytics/rules" : `/analytics/rules/${editing.id}`, {
        method: editing === "new" ? "POST" : "PATCH", signal: controller.signal,
        body: JSON.stringify({ threshold_km: Number(threshold), active, vehicle_id: scope === "vehicle" ? vehicle!.id : null }),
      });
      if (controller.signal.aborted) return;
      setEditing(null); setSaved(true); setRevision(v => v + 1); onChanged();
      requestAnimationFrame(() => opener.current?.focus());
    } catch (err) {
      if (controller.signal.aborted) return;
      setError(err instanceof ApiError && err.status === 404 ? "Pojazd lub reguła są niedostępne. Wybierz aktywny pojazd i ponów zapis." :
        err instanceof ApiError && err.status === 403 ? "Brak uprawnień do zmiany reguły." :
        "Nie zapisano reguły. Sprawdź dodatni próg (maksymalnie jedno miejsce po przecinku) i ponów zapis. Dane formularza pozostały na ekranie.");
    } finally { write.current = null; if (!controller.signal.aborted) setBusy(false); }
  };
  return <WidgetFrame title="Reguły dziennego dystansu" icon={Settings2}>
    <p className="alert-note">Próg dotyczy dystansu zaobserwowanego w polskim dniu kalendarzowym. Równość nie tworzy alertu. Pokrycie pomiarami może być niepełne.</p>
    {!canEdit && <p>Masz dostęp do reguł tylko do odczytu. Możesz oznaczać własne alerty jako przeczytane.</p>}
    {loading && !data && <p role="status">Pobieranie reguł…</p>}
    {error && <p role="alert">{error}</p>}
    {saved && <p role="status">Reguła została zapisana.</p>}
    <div className="alert-controls">
      <button type="button" className="button button-secondary" disabled={loading || busy || !!editing} onClick={() => setRevision(v => v + 1)}>Odśwież reguły</button>
      {canEdit && <button className="button button-primary" disabled={busy || !!editing} onClick={e => edit("new", e.currentTarget)}>Dodaj regułę</button>}
    </div>
    {data && <>
      {!data.items.length && <p>Brak reguł dziennego dystansu.</p>}
      <ul className="rule-list">{data.items.map(rule => <li key={rule.id}>
        <strong>{rule.threshold_km.toLocaleString("pl-PL")} km · {rule.active ? "Włączona" : "Wyłączona"}</strong>
        {rule.vehicle_id ? <button className="alert-vehicle" onClick={() => fleet.inspect(rule.vehicle_id!)}>{rule.vehicle_name || "Przypisany pojazd"}{rule.license_plate ? ` · ${rule.license_plate}` : ""}</button> : <span>Cała flota</span>}
        {canEdit && <button className="button button-secondary" disabled={busy || !!editing} onClick={e => edit(rule, e.currentTarget)}>Edytuj regułę</button>}
      </li>)}</ul>
      <ListPagination label="Reguły alertów" page={page} pageSize={pageSize} total={data.total} loading={loading || busy || !!editing}
        onPage={setPage} onPageSize={size => { setSize(size); setPage(1); }} />
    </>}
    {editing && <form className="rule-form" aria-label={editing === "new" ? "Nowa reguła dystansu" : "Edycja reguły dystansu"}
      onSubmit={e => { e.preventDefault(); void save(); }}>
      <h3>{editing === "new" ? "Nowa reguła" : "Edycja reguły"}</h3>
      <label>Próg dziennego dystansu (km)<input ref={thresholdInput} type="number" required min="0.1" max="9999999999999.9" step="0.1" value={threshold} disabled={busy} onChange={e => setThreshold(e.target.value)} /></label>
      <label>Zakres reguły<select value={scope} disabled={busy} onChange={e => setScope(e.target.value)}><option value="fleet">Cała flota</option><option value="vehicle">Wybrany pojazd</option></select></label>
      {scope === "vehicle" && <RuleVehiclePicker selected={vehicle} onSelect={setVehicle} disabled={busy} />}
      <label className="rule-active"><input type="checkbox" checked={active} disabled={busy} onChange={e => setActive(e.target.checked)} />Reguła włączona</label>
      <div className="alert-controls"><button type="submit" className="button button-primary" disabled={busy}>{busy ? "Zapisywanie…" : "Zapisz regułę"}</button>
        <button type="button" className="button button-secondary" disabled={busy} onClick={() => { setEditing(null); requestAnimationFrame(() => opener.current?.focus()); }}>Anuluj regułę</button></div>
    </form>}
  </WidgetFrame>;
}
