import { useEffect, useState } from "react";
import { api, ApiError } from "../../../shared/api/client";
import type {
  DriverAssignmentList,
  DriverAssignmentResult,
  DriverProfile,
} from "../../../shared/api/generated/contracts";
import { ListPagination } from "../../../shared/components/ListPagination";
import { VehiclePicker } from "../../fleet/components/VehiclePicker";
import { useFleet } from "../../fleet/model/FleetProvider";

const time = (value: string | null) =>
  value
    ? new Intl.DateTimeFormat("pl-PL", {
        timeZone: "Europe/Warsaw",
        dateStyle: "short",
        timeStyle: "short",
      }).format(new Date(value))
    : "Nieznana data";
export function DriverAssignments({
  profile,
  canEdit,
  onProfile,
  onDirty,
}: {
  profile: DriverProfile;
  canEdit: boolean;
  onProfile: (value: DriverProfile) => void;
  onDirty: (value: boolean) => void;
}) {
  const fleet = useFleet();
  const [filter, setFilter] = useState("current");
  const [page, setPage] = useState(1);
  const [pageSize, setSize] = useState(10);
  const [data, setData] = useState<DriverAssignmentList | null>(null);
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selection, setSelection] = useState<{
    id: string;
    name: string;
  } | null>(null);
  const [adding, setAdding] = useState(false);
  useEffect(() => {
    onDirty(!!selection || busy);
    return () => onDirty(false);
  }, [selection, busy, onDirty]);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setData(null);
    const query = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (filter !== "all") query.set("active", String(filter === "current"));
    api<DriverAssignmentList>(`/drivers/${profile.id}/assignments?${query}`, {
      signal: controller.signal,
    })
      .then((value) => {
        if (!controller.signal.aborted) {
          setData(value);
          if (page > 1 && !value.items.length) setPage(1);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError("Nie można pobrać przypisań. Ponów odczyt.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [profile.id, page, pageSize, filter, revision]);
  const refresh = async () => {
    setError(null);
    setBusy(true);
    try {
      onProfile(await api<DriverProfile>(`/drivers/${profile.id}`));
      setRevision((value) => value + 1);
    } catch {
      setError("Nie można odświeżyć kierowcy. Zachowano widoczne dane.");
    } finally {
      setBusy(false);
    }
  };
  const mutate = async (assignmentId?: string) => {
    if (busy || (!assignmentId && !selection)) return;
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      const result = await api<DriverAssignmentResult>(
        assignmentId
          ? `/drivers/${profile.id}/assignments/${assignmentId}/close`
          : `/drivers/${profile.id}/assignments`,
        {
          method: assignmentId ? "PATCH" : "POST",
          body: JSON.stringify({
            version: profile.version,
            ...(!assignmentId ? { vehicle_id: selection!.id } : {}),
          }),
        },
      );
      onProfile({ ...profile, version: result.driver_version });
      setSelection(null);
      setAdding(false);
      onDirty(false);
      setNotice(
        assignmentId
          ? "Zakończono przypisanie. Historia została zachowana."
          : "Pojazd został przypisany.",
      );
      setRevision((value) => value + 1);
      try {
        onProfile(await api<DriverProfile>(`/drivers/${profile.id}`));
      } catch {
        setError(
          "Zapis został potwierdzony. Odśwież dane kierowcy, aby zobaczyć aktualne podsumowanie.",
        );
      }
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 409
          ? "Dane zmieniły się lub przypisanie już istnieje. Odśwież przypisania przed ponowieniem. Twój wybór został zachowany."
          : "Nie udało się potwierdzić zapisu. Odśwież przypisania i sprawdź bieżący stan. Twój wybór został zachowany.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <section
      className="driver-assignments"
      aria-label="Pojazdy i historia kierowcy"
    >
      <h3>Pojazdy i historia przypisań</h3>
      <p>
        Bieżące przypisania: {profile.vehicles_total}. Zmiana nie usuwa
        wcześniejszej historii.
      </p>
      <div className="driver-actions">
        <label>
          Stan przypisań
          <select
            aria-label="Stan przypisań"
            value={filter}
            disabled={busy}
            onChange={(event) => {
              setFilter(event.target.value);
              setPage(1);
              setData(null);
            }}
          >
            <option value="current">Bieżące</option>
            <option value="history">Zakończone</option>
            <option value="all">Wszystkie</option>
          </select>
        </label>
        <button
          className="button button-secondary"
          disabled={busy}
          onClick={() => void refresh()}
        >
          Odśwież przypisania
        </button>
        {canEdit && profile.active && (
          <button
            className="button button-secondary"
            disabled={busy || adding}
            onClick={() => setAdding(true)}
          >
            Przypisz pojazd
          </button>
        )}
      </div>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {loading && <p role="status">Pobieranie przypisań…</p>}
      {data && (
        <>
          {!data.items.length && <p>Brak przypisań w tym widoku.</p>}
          <ul className="driver-assignment-list">
            {data.items.map((item) => (
              <li key={item.id}>
                <strong>
                  {item.vehicle.name}
                  {item.vehicle.license_plate
                    ? ` · ${item.vehicle.license_plate}`
                    : ""}
                </strong>
                <span>
                  {item.active ? "Bieżące" : "Zakończone"}
                  {!item.vehicle.active ? " · Pojazd nieaktywny" : ""}
                </span>
                <span>
                  Od: {time(item.started_at)}
                  {!item.active ? ` · Do: ${time(item.ended_at)}` : ""}
                </span>
                {!item.start_known && (
                  <small>Początek starego przypisania nie jest znany.</small>
                )}
                <div className="driver-actions">
                  <button
                    className="button button-secondary"
                    disabled={!item.vehicle.active}
                    onClick={() => fleet.inspect(item.vehicle.id)}
                  >
                    Szczegóły pojazdu
                  </button>
                  {canEdit && item.active && (
                    <button
                      className="button button-secondary"
                      disabled={busy}
                      onClick={() => void mutate(item.id)}
                    >
                      Zakończ przypisanie
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
          <ListPagination
            label="Przypisania kierowcy"
            page={page}
            pageSize={pageSize}
            total={data.total}
            loading={loading || busy}
            onPage={setPage}
            onPageSize={(size) => {
              setSize(size);
              setPage(1);
            }}
          />
        </>
      )}
      {adding && (
        <div className="driver-assign-form">
          <VehiclePicker
            selected={selection}
            onSelect={setSelection}
            disabled={busy}
            legend="Pojazd do przypisania"
            searchLabel="Znajdź pojazd do przypisania"
            paginationLabel="Pojazdy do przypisania"
          />
          <p>
            Przypisanie zacznie obowiązywać po zapisie. Pojazd może mieć także
            innych kierowców.
          </p>
          <div className="driver-actions">
            <button
              className="button button-primary"
              disabled={!selection || busy}
              onClick={() => void mutate()}
            >
              Zapisz przypisanie
            </button>
            <button
              className="button button-secondary"
              disabled={busy}
              onClick={() => {
                setAdding(false);
                setSelection(null);
              }}
            >
              Anuluj przypisanie
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
