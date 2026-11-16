import React from "react";
import ReactDOM from "react-dom/client";
import "@fontsource-variable/inter";
import { AuthProvider } from "./features/auth/AuthProvider";
import { AuthGate } from "./features/auth/AuthGate";
import { DashboardPreferencesProvider } from "./app/preferences";
import { FleetProvider } from "./features/fleet/model/FleetProvider";
import { VehiclePreferencesProvider } from "./features/fleet/model/VehiclePreferences";
import "./app/fleet-data.css";
import "./app/vehicle-gallery.css";
import { App } from "./app/App";
import { ErrorBoundary } from "./shared/components/ErrorBoundary";
import "./app/styles.css";
import "./app/dashboard-editor.css";
import "./app/glass.css";
import "./app/backgrounds.css";
import "./app/workspace-pages.css";
import "./app/settings.css";
import "./app/profile.css";
import "./app/vehicle-details.css";
import "./app/map-preview.css";
import "./app/trips.css";
import "./shared/components/list-pagination.css";
import "./app/build-version.css";
import "./app/account-preferences.css";

function AppErrorFallback() {
  return (
    <main className="app-error-fallback" role="alert">
      <h1>Nie udało się uruchomić aplikacji</h1>
      <p>
        Odśwież stronę, aby spróbować ponownie. Niezapisane zmiany mogą nie
        zostać zachowane.
      </p>
      <button
        className="button button-primary"
        type="button"
        onClick={() => window.location.reload()}
      >
        Odśwież stronę
      </button>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <ErrorBoundary fallback={<AppErrorFallback />}>
    <React.StrictMode>
      <AuthProvider>
        <DashboardPreferencesProvider>
          <AuthGate>
            <VehiclePreferencesProvider>
              <FleetProvider>
                <App />
              </FleetProvider>
            </VehiclePreferencesProvider>
          </AuthGate>
        </DashboardPreferencesProvider>
      </AuthProvider>
    </React.StrictMode>
  </ErrorBoundary>,
);
