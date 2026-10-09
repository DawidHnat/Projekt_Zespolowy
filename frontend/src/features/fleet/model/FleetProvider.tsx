import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api } from "../../../shared/api/client";
import type {
  FleetMap,
  Summary,
  Vehicle,
  VehicleList,
  VehicleStatus,
} from "./types";

type FleetState = {
  list: VehicleList | null;
  map: FleetMap | null;
  summary: Summary | null;
  loading: boolean;
  error: string | null;
  q: string;
  status: VehicleStatus | "";
  page: number;
  selectedId: string | null;
  selected: Vehicle | null;
  setQ: (q: string) => void;
  setStatus: (status: VehicleStatus | "") => void;
  setPage: (page: number) => void;
  select: (id: string) => void;
  refresh: () => void;
};
const Context = createContext<FleetState | null>(null);
export function FleetProvider({ children }: { children: ReactNode }) {
  const [list, setList] = useState<VehicleList | null>(null);
  const [map, setMap] = useState<FleetMap | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQuery] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [status, setFilter] = useState<VehicleStatus | "">("");
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Vehicle | null>(null);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQ(q), 250);
    return () => clearTimeout(timer);
  }, [q]);
  useEffect(() => {
    const controller = new AbortController();
    let running = false;
    const load = async () => {
      if (running) return;
      running = true;
      setLoading(true);
      const filter = new URLSearchParams({
        q: debouncedQ,
        ...(status ? { status } : {}),
      });
      try {
        const [nextList, nextMap, nextSummary] = await Promise.all([
          api<VehicleList>(
            `/fleet/vehicles?${filter}&page=${page}&page_size=25`,
            { signal: controller.signal },
          ),
          api<FleetMap>(`/fleet/map?${filter}`, { signal: controller.signal }),
          api<Summary>("/fleet/summary", { signal: controller.signal }),
        ]);
        if (controller.signal.aborted) return;
        setList(nextList);
        setMap(nextMap);
        setSummary(nextSummary);
        setError(null);
        if (page > 1 && nextList.items.length === 0 && nextList.total > 0)
          setPage(1);
      } catch (err) {
        if (!controller.signal.aborted)
          setError(
            err instanceof Error ? err.message : "Nie można pobrać floty.",
          );
      } finally {
        running = false;
        if (!controller.signal.aborted) setLoading(false);
      }
    };
    void load();
    const timer = setInterval(() => void load(), 60000);
    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, [debouncedQ, status, page, revision]);
  useEffect(() => {
    if (!selectedId) {
      setSelected(null);
      return;
    }
    const controller = new AbortController();
    api<Vehicle>(`/fleet/vehicles/${encodeURIComponent(selectedId)}`, {
      signal: controller.signal,
    })
      .then((vehicle) => {
        if (!controller.signal.aborted) setSelected(vehicle);
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setSelectedId(null);
          setSelected(null);
        }
      });
    return () => controller.abort();
  }, [selectedId, list]);
  const setQ = (value: string) => {
    setQuery(value);
    setPage(1);
    setSelectedId(null);
  };
  const setStatus = (value: VehicleStatus | "") => {
    setFilter(value);
    setPage(1);
    setSelectedId(null);
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
        selectedId,
        selected,
        setQ,
        setStatus,
        setPage,
        select: setSelectedId,
        refresh: () => setRevision((v) => v + 1),
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
