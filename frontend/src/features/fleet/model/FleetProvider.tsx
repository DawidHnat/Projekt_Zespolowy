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
  detailsLoading: boolean;
  detailsError: string | null;
  detailsOpen: boolean;
  setQ: (q: string) => void;
  setStatus: (status: VehicleStatus | "") => void;
  clearFilters: () => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  select: (id: string | null) => void;
  inspect: (id: string) => void;
  retryDetails: () => void;
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
type DetailRequestState = {
  id: string;
  loading: boolean;
  error: string | null;
};
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
  const [detailRequest, setDetailRequest] = useState<DetailRequestState | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const listPoll = useRef<ReturnType<typeof startPolling> | null>(null);
  const detailPoll = useRef<ReturnType<typeof startPolling> | null>(null);
  const selectedIdRef = useRef<string | null>(null);
  selectedIdRef.current = selectedId;
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
    const environment = browserPollingEnvironment();
    const pause = () => {
      setRequest(current => ({
        key: activeKey,
        loading: false,
        error: !navigator.onLine
          ? "Brak połączenia z siecią. Pobieranie wznowi się po odzyskaniu połączenia."
          : current?.key === activeKey ? current.error : null,
      }));
    };
    const poll = startPolling(
      load,
      environment,
      pause,
      fleetPollIntervalMs,
    );
    // A provider can mount (or change criteria) after the offline event fired.
    // No request starts then, so there is no pending request to finish loading.
    if (!environment.available()) pause();
    listPoll.current = poll;
    return () => {
      poll.dispose();
      listPoll.current = null;
    };
  }, [debouncedQ, status, page, pageSize]);
  useEffect(() => {
    if (!selectedId) {
      setSelected(null);
      setDetailRequest(null);
      return;
    }
    const id = selectedId;
    const poll = startPolling(
      async signal => {
        try {
          const vehicle = await api<Vehicle>(`/fleet/vehicles/${encodeURIComponent(id)}`, { signal });
          if (signal.aborted || selectedIdRef.current !== id) return;
          setSelected(vehicle);
          setDetailRequest({ id, loading: false, error: null });
        } catch (err) {
          if (signal.aborted || selectedIdRef.current !== id) throw err;
          if (err instanceof ApiError && err.status === 404) {
            selectedIdRef.current = null;
            setSelectedId(null);
            setSelected(null);
            setDetailRequest(null);
            setDetailsOpen(false);
          } else if (!(err instanceof ApiError && err.status === 401)) {
            setDetailRequest({
              id,
              loading: false,
              error: err instanceof Error
                ? err.message
                : "Nie można pobrać szczegółów pojazdu.",
            });
          }
          throw err;
        }
      },
      browserPollingEnvironment(),
      () => {
        if (selectedIdRef.current !== id) return;
        const message = !navigator.onLine
          ? "Brak połączenia z siecią. Szczegóły zostaną odświeżone po odzyskaniu połączenia."
          : "Odświeżanie szczegółów zostanie wznowione po powrocie do aplikacji.";
        setDetailRequest(current => ({
          id,
          loading: false,
          error: current?.id === id && current.error ? current.error : message,
        }));
      },
      fleetPollIntervalMs,
    );
    if (!document || document.visibilityState === "hidden" || !navigator.onLine) {
      const message = !navigator.onLine
        ? "Brak połączenia z siecią. Szczegóły zostaną odświeżone po odzyskaniu połączenia."
        : "Odświeżanie szczegółów zostanie wznowione po powrocie do aplikacji.";
      setDetailRequest(current => ({ id, loading: false, error: current?.error ?? message }));
    }
    detailPoll.current = poll;
    return () => {
      poll.dispose();
      detailPoll.current = null;
    };
  }, [selectedId]);
  const chooseVehicle = (id: string | null, open: boolean) => {
    if (selectedIdRef.current !== id) {
      selectedIdRef.current = id;
      setDetailRequest(id ? { id, loading: true, error: null } : null);
      if (!id) setSelected(null);
    }
    setSelectedId(id);
    setDetailsOpen(open);
  };
  const setQ = (value: string) => {
    setQuery(value);
    setPage(1);
    chooseVehicle(null, false);
  };
  const setStatus = (value: VehicleStatus | "") => {
    setFilter(value);
    setPage(1);
    chooseVehicle(null, false);
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
        detailsLoading: detailRequest?.id === selectedId && detailRequest.loading,
        detailsError: detailRequest?.id === selectedId ? detailRequest.error : null,
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
        select: id => chooseVehicle(id, false),
        inspect: id => chooseVehicle(id, true),
        retryDetails: () => {
          if (!selectedId) return;
          if (!navigator.onLine) {
            setDetailRequest({
              id: selectedId,
              loading: false,
              error: "Brak połączenia z siecią. Szczegóły zostaną odświeżone po odzyskaniu połączenia.",
            });
            return;
          }
          setDetailRequest({
            id: selectedId,
            loading: !selected || selected.id !== selectedId,
            error: null,
          });
          detailPoll.current?.refresh();
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
