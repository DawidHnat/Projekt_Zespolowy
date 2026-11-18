import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api } from "../../../shared/api/client";
import type {
  DriverCategoryCatalog,
  DriverList,
} from "../../../shared/api/generated/contracts";
import {
  browserPollingEnvironment,
  startPolling,
} from "../../../shared/api/polling";

export type DriverSort =
  | "name_asc"
  | "name_desc"
  | "vehicles_asc"
  | "vehicles_desc"
  | "custom";
export type DriverFilters = {
  q: string;
  active: "all" | "active" | "inactive";
  assigned: "all" | "with" | "without";
  category: string;
  sort: DriverSort;
};
const defaults: DriverFilters = {
  q: "",
  active: "all",
  assigned: "all",
  category: "",
  sort: "name_asc",
};
function useDriverData(customOrder: string[]) {
  const [filters, setFilters] = useState<DriverFilters>(defaults);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setSize] = useState(25);
  const [data, setData] = useState<DriverList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const polling = useRef<ReturnType<typeof startPolling> | null>(null);
  const [catalog, setCatalog] = useState<DriverCategoryCatalog | null>(null);
  const [catalogError, setCatalogError] = useState(false);
  const [catalogRevision, setCatalogRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setCatalogError(false);
    api<DriverCategoryCatalog>("/drivers/categories", {
      signal: controller.signal,
    })
      .then((value) => {
        if (!controller.signal.aborted) setCatalog(value);
      })
      .catch(() => {
        if (!controller.signal.aborted) setCatalogError(true);
      });
    return () => controller.abort();
  }, [catalogRevision]);
  useEffect(() => {
    const timer = setTimeout(() => setQuery(filters.q), 250);
    return () => clearTimeout(timer);
  }, [filters.q]);
  const body = JSON.stringify({
    q: query,
    active: filters.active === "all" ? null : filters.active === "active",
    assigned: filters.assigned === "all" ? null : filters.assigned === "with",
    category: filters.category === "missing" ? null : filters.category || null,
    missing_categories: filters.category === "missing" ? true : null,
    sort: filters.sort,
    custom_order: filters.sort === "custom" ? customOrder : [],
    page,
    page_size: pageSize,
  });
  useEffect(() => {
    setData(null);
    setError(null);
  }, [body]);
  useEffect(() => {
    const poll = startPolling(
      async (signal) => {
        setLoading(true);
        try {
          const result = await api<DriverList>("/drivers/search", {
            method: "POST",
            body,
            signal,
          });
          if (!signal.aborted) {
            setData(result);
            setError(null);
            if (page > 1 && !result.items.length) setPage(1);
          }
        } catch (err) {
          if (!signal.aborted)
            setError(
              err instanceof Error
                ? err.message
                : "Nie można pobrać kierowców.",
            );
          throw err;
        } finally {
          if (!signal.aborted) setLoading(false);
        }
      },
      browserPollingEnvironment(),
      () => setLoading(false),
    );
    polling.current = poll;
    return () => poll.dispose();
  }, [body, page]);
  const change = useCallback((patch: Partial<DriverFilters>) => {
    setFilters((value) => ({ ...value, ...patch }));
    setPage(1);
  }, []);
  const refresh = useCallback(() => polling.current?.refresh(), []);
  return {
    data,
    filters,
    loading,
    error,
    page,
    pageSize,
    change,
    setPage,
    setPageSize: (size: number) => {
      setSize(size);
      setPage(1);
    },
    refresh,
    catalog,
    catalogError,
    retryCatalog: () => setCatalogRevision((value) => value + 1),
  };
}
type DriverState = ReturnType<typeof useDriverData>;
const Context = createContext<DriverState | null>(null);
export function DriverProvider({
  children,
  customOrder,
}: {
  children: ReactNode;
  customOrder: string[];
}) {
  const state = useDriverData(customOrder);
  return <Context value={state}>{children}</Context>;
}
export function useDrivers() {
  const state = useContext(Context);
  if (!state) throw new Error("DriverProvider required");
  return state;
}
