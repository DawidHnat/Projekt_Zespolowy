export const PAGE_SIZES = [10, 25, 50, 100] as const;
export function normalizePageSize(value: unknown): number {
  return PAGE_SIZES.some((size) => size === value) ? (value as number) : 25;
}
export function pageWindow(page: number, pageSize: number, total: number) {
  const count = Number.isFinite(total) ? Math.max(0, Math.floor(total)) : 0;
  const size = normalizePageSize(pageSize);
  const pages = Math.max(1, Math.ceil(count / size));
  const current = Math.max(
    1,
    Math.min(pages, Number.isFinite(page) ? Math.floor(page) : 1),
  );
  return {
    page: current,
    pages,
    from: count ? (current - 1) * size + 1 : 0,
    to: Math.min(current * size, count),
    total: count,
  };
}
