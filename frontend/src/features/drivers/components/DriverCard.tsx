import { Grip, MoveDiagonal2, Settings2 } from "lucide-react";
import type { CSSProperties } from "react";
import type { DriverProfile } from "../../../shared/api/generated/contracts";
import { useCardResize } from "../../../shared/hooks/useCardResize";
import type { CardSize } from "../../../shared/model/card-layout";

export function DriverCard({
  profile,
  size,
  editing,
  selected,
  canEdit,
  onSelect,
  onOpen,
  onEdit,
  onSize,
  onResize,
  onMove,
  onDrag,
}: {
  profile: DriverProfile;
  size: CardSize;
  editing: boolean;
  selected: boolean;
  canEdit: boolean;
  onSelect: () => void;
  onOpen: (assignments?: boolean) => void;
  onEdit: () => void;
  onSize: () => void;
  onResize: (size: CardSize) => void;
  onMove: (direction: -1 | 1) => void;
  onDrag: (source: string, destination: string) => void;
}) {
  const resize = useCardResize(size, onResize);
  const style: CSSProperties = {
    width: (resize.live ?? size).width,
    height: (resize.live ?? size).height,
  };
  return (
    <article
      className={`driver-card widget ${selected ? "driver-card-selected" : ""}`}
      style={style}
      aria-label={`Kierowca: ${profile.display_name}`}
      onClick={(event) => {
        if (
          (event.target as HTMLElement).closest("button,a,input,select,label")
        )
          return;
        if (editing) onSelect();
        else onOpen();
      }}
      onDragOver={(event) => {
        if (editing) event.preventDefault();
      }}
      onDrop={(event) => {
        if (editing) {
          event.preventDefault();
          onDrag(event.dataTransfer.getData("text/plain"), profile.id);
        }
      }}
    >
      <header>
        <span className="driver-status">
          {profile.active ? "Aktywny" : "Nieaktywny"}
        </span>
        {editing ? (
          <label className="driver-checkbox">
            <input
              type="checkbox"
              aria-label={`Zaznacz kierowcę: ${profile.display_name}`}
              checked={selected}
              onChange={onSelect}
            />
            Wybierz
          </label>
        ) : (
          <button className="driver-name" onClick={() => onOpen()}>
            {profile.display_name}
          </button>
        )}
        {editing && <strong>{profile.display_name}</strong>}
        <small>{profile.identifier || "Identyfikator do uzupełnienia"}</small>
      </header>
      <dl>
        <div>
          <dt>Telefon</dt>
          <dd>
            {profile.phone ? (
              <a
                href={`tel:${profile.phone.replace(/[^+0-9]/g, "")}`}
                title={profile.phone}
              >
                {profile.phone}
              </a>
            ) : (
              "Nie podano"
            )}
          </dd>
        </div>
        <div>
          <dt>E-mail</dt>
          <dd>
            {profile.email ? (
              <a
                href={`mailto:${encodeURIComponent(profile.email)}`}
                title={profile.email}
              >
                {profile.email}
              </a>
            ) : (
              "Nie podano"
            )}
          </dd>
        </div>
        <div>
          <dt>Wpisane kategorie</dt>
          <dd>{profile.categories.join(", ") || "Brak wpisanych kategorii"}</dd>
        </div>
        <div>
          <dt>Pojazdy ({profile.vehicles_total})</dt>
          <dd>
            {profile.first_vehicle ? (
              <>
                <span title={profile.first_vehicle.name}>
                  {profile.first_vehicle.name}
                  {!profile.first_vehicle.active ? " · Nieaktywny" : ""}
                </span>
                {profile.vehicles_total > 1 && (
                  <button
                    className="driver-more"
                    disabled={editing}
                    aria-label={`+${profile.vehicles_total - 1} poj. — pozostałe pojazdy: ${profile.display_name}`}
                    onClick={() => onOpen(true)}
                  >
                    +{profile.vehicles_total - 1} poj.
                  </button>
                )}
              </>
            ) : (
              "Brak pojazdów"
            )}
          </dd>
        </div>
      </dl>
      <footer className="driver-actions">
        {!editing ? (
          <>
            <button
              className="button button-secondary"
              onClick={() => onOpen()}
            >
              Szczegóły
            </button>
            {canEdit && (
              <button className="button button-secondary" onClick={onEdit}>
                Edytuj
              </button>
            )}
          </>
        ) : (
          <>
            <button
              className="icon-button"
              draggable
              aria-label={`Przenieś kafelek: ${profile.display_name}`}
              title="Przeciągnij lub użyj przycisków Wyżej/Niżej"
              onDragStart={(event) =>
                event.dataTransfer.setData("text/plain", profile.id)
              }
            >
              <Grip size={18} aria-hidden="true" />
            </button>
            <button
              className="button button-secondary"
              onClick={() => onMove(-1)}
            >
              Wyżej
            </button>
            <button
              className="button button-secondary"
              onClick={() => onMove(1)}
            >
              Niżej
            </button>
            <button
              className="icon-button"
              aria-label={`Rozmiar kafelka kierowcy: ${profile.display_name}`}
              onClick={onSize}
            >
              <Settings2 size={17} aria-hidden="true" />
            </button>
            <button
              className="icon-button driver-card-resize"
              aria-label={`Zmień rozmiar kierowcy: ${profile.display_name}`}
              {...resize.handle}
              onKeyDown={(event) => {
                if (
                  !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(
                    event.key,
                  )
                )
                  return;
                event.preventDefault();
                onResize({
                  width:
                    size.width +
                    (event.key === "ArrowLeft"
                      ? -10
                      : event.key === "ArrowRight"
                        ? 10
                        : 0),
                  height:
                    size.height +
                    (event.key === "ArrowUp"
                      ? -10
                      : event.key === "ArrowDown"
                        ? 10
                        : 0),
                });
              }}
            >
              <MoveDiagonal2 size={18} aria-hidden="true" />
            </button>
          </>
        )}
      </footer>
    </article>
  );
}
