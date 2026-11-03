import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, onSessionExpired } from "../../shared/api/client";

import type { User } from "../../shared/api/generated/contracts";
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
  const [revision, setRevision] = useState(0);
  useEffect(
    () =>
      onSessionExpired(() => {
        setUser(null);
        setError("Sesja wygasła. Zaloguj się ponownie.");
      }),
    [],
  );
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    api<{ user: User }>("/auth/me", { signal: controller.signal }, false)
      .then((data) => {
        setUser(data.user);
        setError(null);
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
    return () => controller.abort();
  }, [revision]);
  const login = async (username: string, password: string) => {
    const data = await api<{ user: User }>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({ username, password }),
      },
      false,
    );
    setUser(data.user);
    setError(null);
  };
  const logout = async () => {
    await api("/auth/logout", { method: "POST" }, false);
    setUser(null);
  };
  return (
    <AuthContext
      value={{
        user,
        loading,
        error,
        login,
        logout,
        retry: () => setRevision((v) => v + 1),
        clearSession: () => setUser(null),
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
