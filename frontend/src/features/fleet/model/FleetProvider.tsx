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
import { useVehiclePreferences, type VehicleArchiveScope } from "./VehiclePreferences";
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
  total: number;
  map: FleetMap | null;
  summary: Summary | null;
  loading: boolean;
  error: string | null;
  mapLoading: boolean;
  mapError: string | null;
  summaryLoading: boolean;
  summaryError: string | null;
  q: string;
  status: VehicleStatus | "";
  archive: VehicleArchiveScope;
  page: number;
  pageSize: number;
  preferencesLoading: boolean;
  selectedId: string | null;
  selected: Vehicle | null;
  detailsLoading: boolean;
  detailsError: string | null;
  detailsOpen: boolean;
  setQ: (q: string) => void;
  setStatus: (status: VehicleStatus | "") => void;
  setArchive: (archive: VehicleArchiveScope) => void;
  clearFilters: () => void;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  select: (id: string | null) => void;
  inspect: (id: string) => void;
  retryDetails: () => void;
  closeDetails: () => void;
  refresh: () => void;
  sourceRefresh: ReturnType<typeof useSourceRefresh>;
};
const Context = createContext<FleetState | null>(null);
type RequestState = { path: string; loading: boolean; error: string | null };
type FleetSnapshot<T> = { path: string; scope: string; payload: T };

function useFleetRead<T>(path: string, scope: string, enabled: boolean) {
  const [snapshot, setSnapshot] = useState<FleetSnapshot<T> | null>(null);
  const [request, setRequest] = useState<RequestState | null>(null);
  const currentPoll = useRef<ReturnType<typeof startPolling> | null>(null);
  useEffect(() => {
    if (!enabled) return;
    const environment = browserPollingEnvironment();
    const pause = () => setRequest(current => ({
      path,
      loading: false,
      error: !navigator.onLine
        ? "Brak połączenia z siecią. Pobieranie wznowi się po odzyskaniu połączenia."
        : current?.path === path ? current.error : null,
    }));
    const load = async (signal: AbortSignal) => {
      setRequest({ path, loading: true, error: null });
      try {
        const payload = await api<T>(path, { signal });
        if (!signal.aborted) setSnapshot({ path, scope, payload });
      } catch (err) {
        if (!signal.aborted) setRequest({
          path,
          loading: false,
          error: err instanceof Error ? err.message : "Nie można pobrać floty.",
        });
        throw err;
      } finally {
        if (!signal.aborted) setRequest(current =>
          current?.path === path ? { ...current, loading: false } : current,
        );
      }
    };
    const poll = startPolling(load, environment, pause, fleetPollIntervalMs);
    if (!environment.available()) pause();
    currentPoll.current = poll;
    return () => {
      poll.dispose();
      currentPoll.current = null;
    };
  }, [path, scope, enabled]);

  return {
    value: snapshot?.path === path ? snapshot.payload : null,
    cached: snapshot?.scope === scope ? snapshot.payload : null,
    loading: !enabled || request?.path !== path || request.loading,
    error: request?.path === path ? request.error : null,
    refresh: () => currentPoll.current?.refresh(),
  };
}

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
  const preferences = useVehiclePreferences();
  const q = preferences.filters.q;
  const [debouncedQ, setDebouncedQ] = useState("");
  const status = preferences.filters.status as VehicleStatus | "";
  const archive = preferences.filters.archive ?? "active";
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
  const [detailRequest, setDetailRequest] = useState<DetailRequestState | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const detailPoll = useRef<ReturnType<typeof startPolling> | null>(null);
  const selectedIdRef = useRef<string | null>(null);
  selectedIdRef.current = selectedId;
  const termPending = debouncedQ !== q.trim();
  const enabled = !preferences.cloud.loading;
  const filter = new URLSearchParams({
    q: debouncedQ,
    ...(status ? { status } : {}),
    ...(archive !== "active" ? { archive } : {}),
  });
  const listQuery = new URLSearchParams(filter);
  listQuery.set("sort", sort);
  listQuery.set("page", String(page));
  listQuery.set("page_size", String(pageSize));
  const listRead = useFleetRead<VehicleList>(`/fleet/vehicles?${listQuery}`, filter.toString(), enabled);
  const mapRead = useFleetRead<FleetMap>(`/fleet/map?${filter}`, filter.toString(), enabled);
  const summaryRead = useFleetRead<Summary>("/fleet/summary", "summary", enabled);
  const list = termPending ? null : listRead.value;
  const map = termPending ? null : mapRead.value;
  const total = termPending ? 0 : listRead.cached?.total ?? 0;
  const refresh = () => {
    listRead.refresh();
    mapRead.refresh();
    summaryRead.refresh();
    detailPoll.current?.refresh();
  };
  const sourceRefresh = useSourceRefresh(refresh, fleetPollIntervalMs);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQ(q.trim()), 250);
    return () => clearTimeout(timer);
  }, [q]);
  useEffect(() => {
    if (page > 1 && list && !list.items.length && list.total > 0) setPage(1);
  }, [list, page]);
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
    preferences.updateFilters({ ...preferences.filters, q: value });
    setPage(1);
    chooseVehicle(null, false);
  };
  const setStatus = (value: VehicleStatus | "") => {
    preferences.updateFilters({ ...preferences.filters, status: value });
    setPage(1);
    chooseVehicle(null, false);
  };
  const setArchive = (value: VehicleArchiveScope) => {
    preferences.updateFilters({ ...preferences.filters, archive: value });
    setPage(1);
    chooseVehicle(null, false);
  };
  return (
    <Context
      value={{
        list,
        total,
        map,
        summary: summaryRead.value,
        loading: termPending || listRead.loading,
        error: termPending ? null : listRead.error,
        mapLoading: termPending || mapRead.loading,
        mapError: termPending ? null : mapRead.error,
        summaryLoading: summaryRead.loading,
        summaryError: summaryRead.error,
        q,
        status,
        archive,
        page,
        pageSize,
        preferencesLoading:
          preferences.cloud.loading || preferences.cloud.migrationAvailable,
        selectedId,
        selected: selected?.id === selectedId ? selected : null,
        detailsLoading: detailRequest?.id === selectedId && detailRequest.loading,
        detailsError: detailRequest?.id === selectedId ? detailRequest.error : null,
        detailsOpen,
        setQ,
        setStatus,
        setArchive,
        clearFilters: () => {
          preferences.updateFilters({ q: "", status: "", archive: "active" });
          setDebouncedQ("");
          setPage(1);
          chooseVehicle(null, false);
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
