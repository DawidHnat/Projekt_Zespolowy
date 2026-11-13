import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { advanceSessionVersion, api, onSessionExpired } from "../../shared/api/client";
import { listenForSessionChanges } from "./session-changes";

type User = {
  id: string;
  username: string;
  display_name: string;
  role: string;
};
type AuthState = {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  retry: () => void;
  clearSession: () => void;
};
const AuthContext = createContext<AuthState | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pendingSession = useRef<AbortController | null>(null);
  const changes = useRef<ReturnType<typeof listenForSessionChanges> | null>(null);
  const finishSession = useCallback((next: User | null, message: string | null = null) => {
    advanceSessionVersion();
    pendingSession.current?.abort();
    setUser(next);
    setLoading(false);
    setError(message);
  }, []);
  const checkSession = useCallback(() => {
    advanceSessionVersion();
    pendingSession.current?.abort();
    const controller = new AbortController();
    pendingSession.current = controller;
    setUser(null);
    setLoading(true);
    setError(null);
    api<{ user: User }>("/auth/me", { signal: controller.signal }, false)
      .then((data) => {
        if (!controller.signal.aborted) setUser(data.user);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setUser(null);
        if (err.status !== 401)
          setError("Nie można połączyć się z serwerem Fleet-Flow.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  }, []);
  useEffect(() => {
    changes.current = listenForSessionChanges(checkSession);
    const onRestore = (event: PageTransitionEvent) => {
      if (event.persisted) checkSession();
    };
    window.addEventListener("pageshow", onRestore);
    const unsubscribe = onSessionExpired(() =>
      finishSession(null, "Sesja wygasła. Zaloguj się ponownie."),
    );
    checkSession();
    return () => {
      pendingSession.current?.abort();
      changes.current?.close();
      changes.current = null;
      window.removeEventListener("pageshow", onRestore);
      unsubscribe();
    };
  }, [checkSession, finishSession]);
  const login = async (username: string, password: string) => {
    const data = await api<{ user: User }>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ username, password }),
      },
      false,
    );
    finishSession(data.user);
    changes.current?.notify();
  };
  const logout = async () => {
    await api("/auth/logout", { method: "POST" }, false);
    finishSession(null);
    changes.current?.notify();
  };
  return (
    <AuthContext
      value={{
        user,
        loading,
        error,
        login,
        logout,
        retry: checkSession,
        clearSession: () => {
          finishSession(null);
          changes.current?.notify();
        },
      }}
    >
      {children}
    </AuthContext>
  );
}
export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("AuthProvider required");
  return value;
}
