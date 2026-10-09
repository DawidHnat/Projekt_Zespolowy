import { Search } from "lucide-react";
import { ListPagination } from "../../../shared/components/ListPagination";
import { useFleet } from "../model/FleetProvider";
import { statusLabels, type VehicleStatus } from "../model/types";

export function FleetFilters() {
  const f = useFleet();
  return (
    <div className="fleet-filters">
      <label className="fleet-search">
        <Search size={16} />
        <input
          type="search"
          aria-label="Szukaj pojazdu"
          placeholder="Nazwa lub rejestracja…"
          maxLength={100}
          value={f.q}
          onChange={(e) => f.setQ(e.target.value)}
        />
      </label>
      <select
        aria-label="Status pojazdu"
        value={f.status}
        onChange={(e) => f.setStatus(e.target.value as VehicleStatus | "")}
      >
        <option value="">Wszystkie statusy</option>
        {Object.entries(statusLabels).map(([key, label]) => (
          <option key={key} value={key}>
            {label}
          </option>
        ))}
      </select>
    </div>
  );
}
export function FleetPagination() {
  const f = useFleet();
  return (
    <ListPagination
      page={f.page}
      pageSize={f.pageSize}
      total={f.list?.total ?? 0}
      loading={f.loading}
      label="pojazdy"
      onPage={f.setPage}
      onPageSize={f.setPageSize}
    />
  );
}
