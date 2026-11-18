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
import { useVehiclePreferences } from "./VehiclePreferences";
import { useSourceRefresh } from "./useSourceRefresh";
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
  map: FleetMap | null;
  summary: Summary | null;
  loading: boolean;
  error: string | null;
  q: string;
  status: VehicleStatus | "";
  page: number;
  pageSize: number;
  preferencesLoading: boolean;
  selectedId: string | null;
  selected: Vehicle | null;
  detailsOpen: boolean;
  setQ: (q: string) => void;
  setStatus: (status: VehicleStatus | "") => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  select: (id: string | null) => void;
  inspect: (id: string) => void;
  closeDetails: () => void;
  refresh: () => void;
  sourceRefresh: ReturnType<typeof useSourceRefresh>;
};
const Context = createContext<FleetState | null>(null);
export function FleetProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  return user ? <AccountFleetProvider key={user.id}>{children}</AccountFleetProvider> : null;
}

function AccountFleetProvider({ children }: { children: ReactNode }) {
  const preferences = useVehiclePreferences();
  const [list, setList] = useState<VehicleList | null>(null);
  const [map, setMap] = useState<FleetMap | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const q = preferences.filters.q;
  const [debouncedQ, setDebouncedQ] = useState("");
  const status = preferences.filters.status as VehicleStatus | "";
  const sort = preferences.sort;
  const [page, setPage] = useState(1);
  const pageSize = preferences.pageSize;
  const setPageSize = (value: number) => {
    const next = normalizePageSize(value);
    preferences.updatePageSize(next);
    setPage(1);
  };
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Vehicle | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const listPoll = useRef<ReturnType<typeof startPolling> | null>(null);
  const detailPoll = useRef<ReturnType<typeof startPolling> | null>(null);
  const refresh = () => {
    listPoll.current?.refresh();
    detailPoll.current?.refresh();
  };
  const sourceRefresh = useSourceRefresh(refresh, fleetPollIntervalMs);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQ(q), 250);
    return () => clearTimeout(timer);
  }, [q]);
  useEffect(() => {
    if (preferences.cloud.loading) {
      setLoading(true);
      return;
    }
    const load = async (signal: AbortSignal) => {
      setLoading(true);
      const filter = new URLSearchParams({
        q: debouncedQ,
        ...(status ? { status } : {}),
      });
      const listFilter = new URLSearchParams(filter);
      listFilter.set("sort", sort);
      try {
        const [nextList, nextMap, nextSummary] = await Promise.all([
          api<VehicleList>(
            `/fleet/vehicles?${listFilter}&page=${page}&page_size=${pageSize}`,
            { signal },
          ),
          api<FleetMap>(`/fleet/map?${filter}`, { signal }),
          api<Summary>("/fleet/summary", { signal }),
        ]);
        if (signal.aborted) return;
        setList(nextList);
        setMap(nextMap);
        setSummary(nextSummary);
        setError(null);
        if (page > 1 && nextList.items.length === 0 && nextList.total > 0)
          setPage(1);
      } catch (err) {
        if (!signal.aborted)
          setError(
            err instanceof Error ? err.message : "Nie można pobrać floty.",
          );
        throw err;
      } finally {
        if (!signal.aborted) setLoading(false);
      }
    };
  const poll = startPolling(
    load,
    browserPollingEnvironment(),
    () => setLoading(false),
    fleetPollIntervalMs,
  );
    listPoll.current = poll;
    return () => {
      poll.dispose();
      listPoll.current = null;
    };
  }, [debouncedQ, status, sort, page, pageSize, preferences.cloud.loading]);
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
    preferences.updateFilters({ ...preferences.filters, q: value });
    setPage(1);
    setSelectedId(null);
    setDetailsOpen(false);
  };
  const setStatus = (value: VehicleStatus | "") => {
    preferences.updateFilters({ ...preferences.filters, status: value });
    setPage(1);
    setSelectedId(null);
    setDetailsOpen(false);
  };
  return (
    <Context
      value={{
        list,
        map,
        summary,
        loading,
        error,
        q,
        status,
        page,
        pageSize,
        preferencesLoading:
          preferences.cloud.loading || preferences.cloud.migrationAvailable,
        selectedId,
        selected: selected?.id === selectedId ? selected : null,
        detailsOpen,
        setQ,
        setStatus,
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
        refresh,
        sourceRefresh,
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
