import { ChevronLeft, ChevronRight } from "lucide-react";
import { PAGE_SIZES, normalizePageSize, pageWindow } from "./pagination-model";

type Props = {
  page: number;
  pageSize: number;
  total: number;
  loading?: boolean;
  label: string;
  onPage: (page: number) => void;
  onPageSize: (size: number) => void;
};
export function ListPagination({
  page,
  pageSize,
  total,
  loading = false,
  label,
  onPage,
  onPageSize,
}: Props) {
  const range = pageWindow(page, pageSize, total);
  return (
    <nav className="list-pagination" aria-label={`Strony: ${label}`}>
      <span className="list-range" aria-live="polite" aria-atomic="true">
        {range.from}–{range.to} z {range.total}
      </span>
      <label className="list-page-size">
        Na stronę
        <select
          aria-label={`Elementów na stronę: ${label}`}
          value={normalizePageSize(pageSize)}
          disabled={loading}
          onChange={(e) =>
            onPageSize(normalizePageSize(Number(e.target.value)))
          }
        >
          {PAGE_SIZES.map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
      </label>
      <div className="list-page-navigation">
        <button
          className="icon-button"
          aria-label={`Poprzednia strona: ${label}`}
          disabled={loading || range.page <= 1}
          onClick={() => onPage(range.page - 1)}
        >
          <ChevronLeft size={17} />
        </button>
        <span aria-label={`Strona ${range.page} z ${range.pages}`}>
          {range.page} / {range.pages}
        </span>
        <button
          className="icon-button"
          aria-label={`Następna strona: ${label}`}
          disabled={loading || range.page >= range.pages}
          onClick={() => onPage(range.page + 1)}
        >
          <ChevronRight size={17} />
        </button>
      </div>
    </nav>
  );
}
