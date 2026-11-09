import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { ApiError, api } from "../../../shared/api/client";
import { browserPollingEnvironment, startPolling } from "../../../shared/api/polling";
import { useAuth } from "../../auth/AuthProvider";
import { normalizePageSize } from "../../../shared/components/pagination-model";
import { fleetPollInterval } from "./types";
import type {
  FleetMap,
  Summary,
  Vehicle,
  VehicleList,
  VehicleStatus,
} from "./types";

const fleetPollIntervalMs = fleetPollInterval(
  import.meta.env.VITE_FLEET_POLL_INTERVAL_MS,
);

type FleetState = {
  list: VehicleList | null;
  total: number;
  map: FleetMap | null;
  summary: Summary | null;
  loading: boolean;
  error: string | null;
  q: string;
  status: VehicleStatus | "";
  page: number;
  pageSize: number;
  selectedId: string | null;
  selected: Vehicle | null;
  detailsOpen: boolean;
  setQ: (q: string) => void;
  setStatus: (status: VehicleStatus | "") => void;
  clearFilters: () => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  select: (id: string | null) => void;
  inspect: (id: string) => void;
  closeDetails: () => void;
  refresh: () => void;
};
const Context = createContext<FleetState | null>(null);
type FleetSnapshot = {
  requestKey: string;
  filterKey: string;
  list: VehicleList;
  map: FleetMap;
  summary: Summary;
};
type RequestState = { key: string; loading: boolean; error: string | null };
export function FleetProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  return user ? <AccountFleetProvider key={user.id}>{children}</AccountFleetProvider> : null;
}

function AccountFleetProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const storageKey = `fleet-flow.list-page-size.v1.${user?.id}`;
  const [snapshot, setSnapshot] = useState<FleetSnapshot | null>(null);
  const [request, setRequest] = useState<RequestState | null>(null);
  const [q, setQuery] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [status, setFilter] = useState<VehicleStatus | "">("");
  const [page, setPage] = useState(1);
  const [pageSize, setSize] = useState(() => {
    try {
      return normalizePageSize(Number(localStorage.getItem(storageKey)));
    } catch {
      return 25;
    }
  });
  const setPageSize = (value: number) => {
    const next = normalizePageSize(value);
    setSize(next);
    setPage(1);
    try {
      localStorage.setItem(storageKey, String(next));
    } catch {
      /* Session-only preference. */
    }
  };
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Vehicle | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const listPoll = useRef<ReturnType<typeof startPolling> | null>(null);
  const detailPoll = useRef<ReturnType<typeof startPolling> | null>(null);
  const filterKey = JSON.stringify([q.trim(), status]);
  const requestKey = JSON.stringify([filterKey, page, pageSize]);
  // Cached results belong to the criteria that produced them, including while
  // the next query is debouncing or fails. Map results do not depend on the page.
  const list = snapshot?.requestKey === requestKey ? snapshot.list : null;
  const map = snapshot?.filterKey === filterKey ? snapshot.map : null;
  const total = snapshot?.filterKey === filterKey ? snapshot.list.total : 0;
  const loading = request?.key !== requestKey || request.loading;
  const error = request?.key === requestKey ? request.error : null;
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQ(q.trim()), 250);
    return () => clearTimeout(timer);
  }, [q]);
  useEffect(() => {
    const activeFilterKey = JSON.stringify([debouncedQ, status]);
    const activeKey = JSON.stringify([activeFilterKey, page, pageSize]);
    const load = async (signal: AbortSignal) => {
      setRequest({ key: activeKey, loading: true, error: null });
      const filter = new URLSearchParams({
        q: debouncedQ,
        ...(status ? { status } : {}),
      });
      try {
        const [nextList, nextMap, nextSummary] = await Promise.all([
          api<VehicleList>(
            `/fleet/vehicles?${filter}&page=${page}&page_size=${pageSize}`,
            { signal },
          ),
          api<FleetMap>(`/fleet/map?${filter}`, { signal }),
          api<Summary>("/fleet/summary", { signal }),
        ]);
        if (signal.aborted) return;
        setSnapshot({
          requestKey: activeKey,
          filterKey: activeFilterKey,
          list: nextList,
          map: nextMap,
          summary: nextSummary,
        });
        if (page > 1 && nextList.items.length === 0 && nextList.total > 0)
          setPage(1);
      } catch (err) {
        if (!signal.aborted)
          setRequest({
            key: activeKey,
            loading: false,
            error: err instanceof Error ? err.message : "Nie można pobrać floty.",
          });
        throw err;
      } finally {
        if (!signal.aborted)
          setRequest(current =>
            current?.key === activeKey ? { ...current, loading: false } : current,
          );
      }
    };
    const poll = startPolling(
      load,
      browserPollingEnvironment(),
      () => setRequest(current => ({
        key: activeKey,
        loading: false,
        error: current?.key === activeKey ? current.error : null,
      })),
      fleetPollIntervalMs,
    );
    listPoll.current = poll;
    return () => {
      poll.dispose();
      listPoll.current = null;
    };
  }, [debouncedQ, status, page, pageSize]);
  useEffect(() => {
    if (!selectedId) {
      setSelected(null);
      return;
    }
    const poll = startPolling(
      async signal => {
        try {
          const vehicle = await api<Vehicle>(`/fleet/vehicles/${encodeURIComponent(selectedId)}`, { signal });
          if (!signal.aborted) setSelected(vehicle);
        } catch (err) {
          if (!signal.aborted && err instanceof ApiError && err.status === 404) {
            setSelectedId(null);
            setSelected(null);
            setDetailsOpen(false);
          }
          // Keep the last detail and mounted editor on a transient failure.
          throw err;
        }
      },
      browserPollingEnvironment(),
      undefined,
      fleetPollIntervalMs,
    );
    detailPoll.current = poll;
    return () => {
      poll.dispose();
      detailPoll.current = null;
    };
  }, [selectedId]);
  const setQ = (value: string) => {
    setQuery(value);
    setPage(1);
    setSelectedId(null);
    setDetailsOpen(false);
  };
  const setStatus = (value: VehicleStatus | "") => {
    setFilter(value);
    setPage(1);
    setSelectedId(null);
    setDetailsOpen(false);
  };
  return (
    <Context
      value={{
        list,
        total,
        map,
        summary: snapshot?.summary ?? null,
        loading,
        error,
        q,
        status,
        page,
        pageSize,
        selectedId,
        selected: selected?.id === selectedId ? selected : null,
        detailsOpen,
        setQ,
        setStatus,
        clearFilters: () => {
          setQ("");
          setDebouncedQ("");
          setFilter("");
        },
        setPage,
        setPageSize,
        select: (id) => {
          setSelectedId(id);
          setDetailsOpen(false);
        },
        inspect: (id) => {
          setSelectedId(id);
          setDetailsOpen(true);
        },
        closeDetails: () => setDetailsOpen(false),
        refresh: () => {
          listPoll.current?.refresh();
          detailPoll.current?.refresh();
        },
      }}
    >
      {children}
    </Context>
  );
}
export function useFleet() {
  const state = useContext(Context);
  if (!state) throw new Error("FleetProvider required");
  return state;
}
