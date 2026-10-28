import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { CarFront, Users, Wrench, Route, X } from "lucide-react";
import { useFleet } from "../model/FleetProvider";
import { useVehiclePreferences } from "../model/VehiclePreferences";
import { statusLabels, type Vehicle } from "../model/types";
import { VehiclePhoto } from "./VehiclePhoto";
import { EmptyState } from "../../../shared/components/EmptyState";
import { VehicleTrips } from "../../trips/components/VehicleTrips";
import { useTripDay } from "../../trips/model/useTripDay";

const tabs = [
  {
    id: "vehicle",
    title: "Pojazd",
    icon: CarFront,
    heading: "Szczegóły pojazdu",
    description: "Tu znajdą się informacje o wybranym pojeździe.",
  },
  {
    id: "driver",
    title: "Kierowca",
    icon: Users,
    heading: "Kierowca pojazdu",
    description: "Tu znajdą się dane kierowcy przypisanego do tego pojazdu.",
  },
  {
    id: "service",
    title: "Przegląd",
    icon: Wrench,
    heading: "Przeglądy i serwis",
    description: "Tu znajdą się terminy i historia przeglądów tego pojazdu.",
  },
  {
    id: "trips",
    title: "Podróże",
    icon: Route,
    heading: "Podróże pojazdu",
    description: "Tu znajdą się trasy i postoje tego pojazdu z wybranego dnia.",
  },
] as const;

function VehicleDetailsContent({ vehicle, unsaved, onUnsaved, mayLeave }: {
  vehicle: Vehicle; unsaved: boolean; onUnsaved: (value: boolean) => void; mayLeave: () => boolean;
}) {
  const [active, setActive] = useState(0);
  const id = useId();
  const day = useTripDay();
  const current = tabs[active];
  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    let next: number;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft") next = (index + tabs.length - 1) % tabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tabs.length - 1;
    else return;
    event.preventDefault();
    if (unsaved && !mayLeave()) return;
    setActive(next);
    document.getElementById(`${id}-tab-${tabs[next].id}`)?.focus();
  };
  return (
    <>
      <div
        className="vehicle-details-tabs"
        role="tablist"
        aria-label={`Informacje o pojeździe ${vehicle.name}`}
      >
        {tabs.map(({ id: tabId, title, icon: Icon }, index) => (
          <button
            key={tabId}
            role="tab"
            id={`${id}-tab-${tabId}`}
            aria-selected={index === active}
            aria-controls={`${id}-panel-${tabId}`}
            tabIndex={index === active ? 0 : -1}
            onClick={() => { if (index === active || !unsaved || mayLeave()) setActive(index); }}
            onKeyDown={(event) => onKeyDown(event, index)}
          >
            <Icon size={16} aria-hidden="true" />
            {title}
          </button>
        ))}
      </div>
      {tabs.map((tab, index) => (
        <section
          key={tab.id}
          className="vehicle-details-content"
          role="tabpanel"
          id={`${id}-panel-${tab.id}`}
          aria-labelledby={`${id}-tab-${tab.id}`}
          hidden={index !== active}
          tabIndex={0}
        >
          {index === active && (
            <>
              {current.id === "trips" ? (
                <VehicleTrips
                  vehicleId={vehicle.id}
                  day={day.value}
                  today={day.today}
                  onDay={day.select}
                  onUnsaved={onUnsaved}
                />
              ) : <>
              <EmptyState
                icon={current.icon}
                title={current.heading}
                description={current.description}
              />
              <span className="vehicle-details-pending">W przygotowaniu</span>
              </>}
            </>
          )}
        </section>
      ))}
    </>
  );
}

export function VehicleDetailsDialog() {
  const fleet = useFleet();
  const preferences = useVehiclePreferences();
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [unsaved, setUnsaved] = useState(false);
  const mayLeave = () => !unsaved || window.confirm("Masz niezapisany cel lub opis przejazdu. Odrzucić zmiany?");
  const vehicle = fleet.selected?.id === fleet.selectedId ? fleet.selected : null;
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (fleet.detailsOpen && fleet.selectedId && !dialog.open) dialog.showModal();
    else if ((!fleet.detailsOpen || !fleet.selectedId) && dialog.open) dialog.close();
  }, [fleet.detailsOpen, fleet.selectedId]);
  return (
    <dialog
      ref={ref}
      className="widget-settings-dialog vehicle-details-dialog"
      aria-labelledby={titleId}
      onClose={fleet.closeDetails}
      onCancel={event => { if (!mayLeave()) event.preventDefault(); }}
    >
      {fleet.detailsOpen && (
        <>
          <header className="vehicle-details-header">
            {vehicle && (
              <VehiclePhoto
                src={preferences.photos[vehicle.id]}
                name={vehicle.name}
              />
            )}
            <div className="vehicle-details-identity">
              <span className="eyebrow">TWOJA FLOTA</span>
              <h2 id={titleId}>{vehicle?.name || "Ładowanie pojazdu…"}</h2>
              {vehicle && (
                <div>
                  <span>
                    {vehicle.license_plate || vehicle.number || "Brak rejestracji"}
                  </span>
                  <span className={`vehicle-status status-${vehicle.status}`}>
                    {statusLabels[vehicle.status]}
                  </span>
                </div>
              )}
            </div>
            <button
              className="icon-button"
              aria-label="Zamknij szczegóły pojazdu"
              title="Zamknij"
              onClick={() => { if (mayLeave()) fleet.closeDetails(); }}
              autoFocus
            >
              <X size={20} aria-hidden="true" />
            </button>
          </header>
          {vehicle ? (
            <VehicleDetailsContent key={vehicle.id} vehicle={vehicle} unsaved={unsaved} onUnsaved={setUnsaved} mayLeave={mayLeave} />
          ) : (
            <div className="vehicle-details-loading" role="status">
              {fleet.error ? <><p>{fleet.error}</p><button className="button button-secondary" onClick={fleet.refresh}>Spróbuj ponownie</button></> : "Pobieranie danych pojazdu…"}
            </div>
          )}
        </>
      )}
    </dialog>
  );
}
