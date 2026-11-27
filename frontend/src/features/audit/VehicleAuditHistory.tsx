import { useEffect, useState } from "react";
import { History } from "lucide-react";
import { api } from "../../shared/api/client";
import type { AuditEventList } from "../../shared/api/generated/contracts";
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

export function VehicleAuditHistory({ vehicleId }: { vehicleId: string }) {
  const [data, setData] = useState<AuditEventList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    const params = new URLSearchParams({
      vehicle_id: vehicleId,
      page: String(page),
      page_size: String(pageSize),
    });
    api<AuditEventList>(`/audit/events?${params}`, { signal: controller.signal })
      .then((res) => {
        if (!controller.signal.aborted) setData(res);
      })
      .catch((err) => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "Nie udało się pobrać historii zmian.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [vehicleId, page, pageSize, revision]);

  return (
    <div className="vehicle-audit-history" aria-busy={loading}>
      <div className="driver-actions">
        <h3>Historia zmian pojazdu</h3>
        <button
          type="button"
          className="button button-secondary"
          disabled={loading}
          onClick={() => setRevision((v) => v + 1)}
        >
          Odśwież historię
        </button>
      </div>
      <p>
        Zdarzenia kartoteki pojazdu, przebiegu, dokumentów, przypisań kierowców oraz ewidencji
        przejazdów w trybie tylko do odczytu.
      </p>
      {loading && <p role="status">Pobieranie historii zmian…</p>}
      {error && (
        <div role="alert">
          <p>{error}</p>
          <button
            type="button"
            className="button button-secondary"
            onClick={() => setRevision((v) => v + 1)}
          >
            Ponów odczyt
          </button>
        </div>
      )}
      {data && (
        <>
          {data.items.length === 0 ? (
            <EmptyState
              icon={History}
              title="Brak zapisanych zmian"
              description="Zmiany kartoteki, przebiegu, przypisań oraz ewidencji pojawią się tutaj automatycznie."
            />
          ) : (
            <ul className="driver-assignment-list" aria-label="Zdarzenia pojazdu">
              {data.items.map((item) => {
                const entries = Object.entries(
                  (item.changes ?? {}) as unknown as Record<string, ChangeEntry>,
                );
                return (
                  <li key={item.id}>
                    <strong>{OPERATION_LABELS[item.operation] || item.operation}</strong>
                    <span>
                      {formatAuditTimestamp(item.occurred_at)} · Autor:{" "}
                      {formatActorLabel(item.actor_type, item.actor)} ·{" "}
                      {ENTITY_LABELS[item.entity_type] || item.entity_type}
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
                    <small>Korelacja: {item.correlation_id}</small>
                  </li>
                );
              })}
            </ul>
          )}
          <ListPagination
            label="Historia zmian pojazdu"
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
    </div>
  );
}
