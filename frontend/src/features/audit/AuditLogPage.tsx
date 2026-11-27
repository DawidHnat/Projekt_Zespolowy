import { useEffect, useId, useState } from "react";
import { History } from "lucide-react";
import { api } from "../../shared/api/client";
import type { AuditActorList, AuditEventList } from "../../shared/api/generated/contracts";
import { DatePicker } from "../../shared/components/DatePicker";
import { EmptyState } from "../../shared/components/EmptyState";
import { ListPagination } from "../../shared/components/ListPagination";
import {
  ENTITY_LABELS,
  FIELD_LABELS,
  OPERATION_LABELS,
  formatActorLabel,
  formatAuditTimestamp,
  formatAuditValue,
} from "./audit-labels";

type ChangeEntry = { before?: unknown; after?: unknown };

export function AuditLogPage() {
  const id = useId();
  const [entityType, setEntityType] = useState("");
  const [actorId, setActorId] = useState("");
  const [actorType, setActorType] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [revision, setRevision] = useState(0);

  const [actors, setActors] = useState<Array<{ id: string; display_name: string }>>([]);
  const [data, setData] = useState<AuditEventList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    api<AuditActorList>("/audit/actors", { signal: controller.signal })
      .then((res) => {
        if (!controller.signal.aborted) setActors(res.items);
      })
      .catch(() => {
        if (!controller.signal.aborted) setActors([]);
      });
    return () => controller.abort();
  }, [revision]);

  useEffect(() => {
    if (fromDate && toDate && fromDate > toDate) {
      setError("Data początkowa nie może być późniejsza niż data końcowa.");
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (entityType) params.set("entity_type", entityType);
    if (actorId) params.set("actor_id", actorId);
    if (actorType) params.set("actor_type", actorType);
    if (fromDate) params.set("from", fromDate);
    if (toDate) params.set("to", toDate);

    api<AuditEventList>(`/audit/events?${params}`, { signal: controller.signal })
      .then((res) => {
        if (!controller.signal.aborted) setData(res);
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "Nie udało się pobrać dziennika zmian.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [entityType, actorId, actorType, fromDate, toDate, page, pageSize, revision]);

  const resetFilters = () => {
    setEntityType("");
    setActorId("");
    setActorType("");
    setFromDate("");
    setToDate("");
    setPage(1);
  };

  return (
    <section
      className="widget driver-directory"
      aria-label="Dziennik historii zmian"
      aria-busy={loading}
    >
      <header className="driver-directory-header">
        <h2>Wspólny dziennik zmian</h2>
        <div className="driver-actions">
          <button
            type="button"
            className="button button-secondary"
            disabled={loading}
            onClick={() => setRevision((v) => v + 1)}
          >
            Odśwież dziennik
          </button>
          <button
            type="button"
            className="button button-secondary"
            disabled={!entityType && !actorId && !actorType && !fromDate && !toDate}
            onClick={resetFilters}
          >
            Wyczyść filtry
          </button>
        </div>
      </header>

      <div className="driver-filters">
        <div>
          <span>Od daty</span>
          <DatePicker
            id={`${id}-from`}
            label="Od daty"
            value={fromDate}
            maxDate={toDate || undefined}
            onChange={(val) => {
              setFromDate(val);
              setPage(1);
            }}
            allowClear
          />
        </div>
        <div>
          <span>Do daty</span>
          <DatePicker
            id={`${id}-to`}
            label="Do daty"
            value={toDate}
            minDate={fromDate || undefined}
            onChange={(val) => {
              setToDate(val);
              setPage(1);
            }}
            allowClear
          />
        </div>
        <label>
          Rodzaj obiektu
          <select
            aria-label="Filtr rodzaju obiektu"
            value={entityType}
            onChange={(event) => {
              setEntityType(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Wszystkie obiekty</option>
            <option value="vehicle">Kartoteka pojazdu</option>
            <option value="vehicle_odometer">Przebieg ręczny</option>
            <option value="vehicle_document">Dokument / zdjęcie pojazdu</option>
            <option value="driver">Kartoteka kierowcy</option>
            <option value="driver_assignment">Przypisanie kierowcy</option>
            <option value="trip_annotation">Adnotacja podróży</option>
            <option value="user_account">Konto użytkownika</option>
            <option value="user_session">Sesja i uwierzytelnianie</option>
          </select>
        </label>
        <label>
          Autor
          <select
            aria-label="Filtr autora zmiany"
            value={actorId}
            onChange={(event) => {
              setActorId(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Wszyscy autorzy</option>
            {actors.map((person) => (
              <option key={person.id} value={person.id}>
                {person.display_name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Źródło zmiany
          <select
            aria-label="Filtr źródła zmiany"
            value={actorType}
            onChange={(event) => {
              setActorType(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Wszystkie źródła</option>
            <option value="user">Ręczna zmiana użytkownika</option>
            <option value="import">Import WEBFLEET</option>
          </select>
        </label>
      </div>

      <p className="driver-note">
        Dziennik jest tylko do odczytu (append-only). Hasła, tokeny, klucze API, kody PIN, pełne
        numery kart oraz surowe współrzędne GPS nie są zapisywane.
      </p>

      {error && (
        <div role="alert">
          <p className="form-error">{error}</p>
        </div>
      )}
      {loading && <p role="status">Pobieranie wpisów dziennika…</p>}

      {data && !error && (
        <>
          {data.items.length === 0 ? (
            <EmptyState
              icon={History}
              title="Brak wpisów dla wybranych filtrów"
              description="Zmień zakres dat lub filtry obiektu i autora, aby wyświetlić inne zdarzenia."
            />
          ) : (
            <ul className="driver-assignment-list" aria-label="Lista zdarzeń dziennika">
              {data.items.map((item) => {
                const entries = Object.entries(
                  (item.changes ?? {}) as unknown as Record<string, ChangeEntry>,
                );
                return (
                  <li key={item.id}>
                    <strong>
                      {OPERATION_LABELS[item.operation] || item.operation}
                      {item.vehicle
                        ? ` · ${item.vehicle.name}${item.vehicle.license_plate ? ` (${item.vehicle.license_plate})` : ""}`
                        : ""}
                    </strong>
                    <span>
                      {formatAuditTimestamp(item.occurred_at)} · Autor:{" "}
                      {formatActorLabel(item.actor_type, item.actor)} · Obiekt:{" "}
                      {ENTITY_LABELS[item.entity_type] || item.entity_type} · Wynik:{" "}
                      {item.outcome === "succeeded"
                        ? "zapisano"
                        : item.outcome === "denied"
                          ? "odmowa"
                          : "błąd"}
                    </span>
                    {entries.length > 0 && (
                      <span>
                        {entries
                          .map(
                            ([field, delta]) =>
                              `${FIELD_LABELS[field] || field}: ${formatAuditValue(delta?.before)} → ${formatAuditValue(delta?.after)}`,
                          )
                          .join(" · ")}
                      </span>
                    )}
                    <small>
                      ID obiektu: {item.entity_id} · Korelacja: {item.correlation_id}
                    </small>
                  </li>
                );
              })}
            </ul>
          )}
          <ListPagination
            label="Dziennik historii zmian"
            page={page}
            pageSize={pageSize}
            total={data.total}
            loading={loading}
            onPage={setPage}
            onPageSize={(size) => {
              setPageSize(size);
              setPage(1);
            }}
          />
        </>
      )}
    </section>
  );
}
