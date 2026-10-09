import { Search, ChevronLeft, ChevronRight } from "lucide-react";
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
  if (!f.list || f.list.total <= f.list.page_size) return null;
  const pages = Math.ceil(f.list.total / f.list.page_size);
  return (
    <div className="fleet-pagination">
      <button
        className="icon-button"
        aria-label="Poprzednia strona pojazdów"
        disabled={f.page <= 1 || f.loading}
        onClick={() => f.setPage(f.page - 1)}
      >
        <ChevronLeft size={18} />
      </button>
      <span>
        {f.page} / {pages}
      </span>
      <button
        className="icon-button"
        aria-label="Następna strona pojazdów"
        disabled={f.page >= pages || f.loading}
        onClick={() => f.setPage(f.page + 1)}
      >
        <ChevronRight size={18} />
      </button>
    </div>
  );
}
