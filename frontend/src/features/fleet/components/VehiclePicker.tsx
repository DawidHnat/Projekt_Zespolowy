import { useEffect, useId, useState } from "react";
import { api } from "../../../shared/api/client";
import type { VehicleList } from "../../../shared/api/generated/contracts";
import { ListPagination } from "../../../shared/components/ListPagination";

type Selection = { id: string; name: string };
export function VehiclePicker({
  selected,
  onSelect,
  disabled,
  legend = "Pojazd",
  searchLabel = "Szukaj pojazdu",
  paginationLabel = "Wybór pojazdu",
}: {
  selected: Selection | null;
  onSelect: (value: Selection) => void;
  disabled: boolean;
  legend?: string;
  searchLabel?: string;
  paginationLabel?: string;
}) {
  const group = useId();
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setSize] = useState(10);
  const [revision, setRevision] = useState(0);
  const [data, setData] = useState<VehicleList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(false);
    const timer = setTimeout(() => {
      const query = new URLSearchParams({
        q,
        page: String(page),
        page_size: String(pageSize),
      });
      api<VehicleList>(`/fleet/vehicles?${query}`, {
        signal: controller.signal,
      })
        .then((result) => {
          if (!controller.signal.aborted) setData(result);
        })
        .catch(() => {
          if (!controller.signal.aborted) {
            setData(null);
            setError(true);
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [q, page, pageSize, revision]);
  return (
    <fieldset className="rule-vehicle-picker" disabled={disabled}>
      <legend>{legend}</legend>
      <p>Wybrany: {selected?.name || "Wybierz pojazd z listy"}</p>
      <label>
        {searchLabel}
        <input
          type="search"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(1);
          }}
        />
      </label>
      {loading ? (
        <p role="status">Pobieranie pojazdów…</p>
      ) : error ? (
        <div role="alert">
          <p>Nie można pobrać pojazdów.</p>
          <button
            type="button"
            className="button button-secondary"
            onClick={() => setRevision((v) => v + 1)}
          >
            Ponów listę pojazdów
          </button>
        </div>
      ) : (
        <>
          {!data?.items.length && <p>Brak pasujących pojazdów.</p>}
          <ul>
            {data?.items.map((vehicle) => (
              <li key={vehicle.id}>
                <label>
                  <input
                    type="radio"
                    name={group}
                    checked={selected?.id === vehicle.id}
                    onChange={() =>
                      onSelect({ id: vehicle.id, name: vehicle.name })
                    }
                  />
                  <span>
                    {vehicle.name}
                    {vehicle.license_plate ? ` · ${vehicle.license_plate}` : ""}
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </>
      )}
      {data && (
        <ListPagination
          page={page}
          pageSize={pageSize}
          total={data.total}
          label={paginationLabel}
          loading={loading || disabled}
          onPage={setPage}
          onPageSize={(size) => {
            setSize(size);
            setPage(1);
          }}
        />
      )}
    </fieldset>
  );
}
