import { Map, MapPin, Navigation } from "lucide-react";
import { useId } from "react";
import { WidgetFrame } from "../../../shared/components/WidgetFrame";

export function FleetMapWidget() {
  const gridId = useId();
  return (
    <WidgetFrame
      title="Mapa floty"
      icon={Map}
      badge="Pozycje pojazdów"
      className="map-widget"
    >
      <div className="map-canvas">
        <svg
          className="map-illustration"
          viewBox="0 0 900 380"
          preserveAspectRatio="xMidYMid slice"
          aria-hidden="true"
        >
          <defs>
            <pattern
              id={gridId}
              width="72"
              height="62"
              patternUnits="userSpaceOnUse"
              patternTransform="rotate(-15)"
            >
              <rect width="72" height="62" fill="var(--map-land)" />
              <path
                d="M0 0H72M0 0V62"
                stroke="var(--map-street)"
                strokeWidth="7"
              />
              <rect
                x="14"
                y="14"
                width="42"
                height="34"
                rx="5"
                fill="var(--map-block)"
              />
            </pattern>
          </defs>
          <rect width="900" height="380" fill={`url(#${gridId})`} />
          <path
            d="M-60 300C130 410 210 130 390 200S610 440 940 80"
            fill="none"
            stroke="var(--map-water)"
            strokeWidth="58"
          />
          <path
            d="M-40 60L480 160L960 320M100 420L380-30M640 420L730-30"
            fill="none"
            stroke="var(--map-street)"
            strokeWidth="18"
          />
          <path
            d="M-40 60L480 160L960 320M100 420L380-30M640 420L730-30"
            fill="none"
            stroke="var(--map-road)"
            strokeWidth="2"
            strokeDasharray="8 9"
          />
          <path d="M650 22L834 58L814 142L620 118Z" fill="var(--map-park)" />
          <path d="M24 230L166 258L138 344L8 302Z" fill="var(--map-park)" />
        </svg>
        <div className="map-note">
          <Navigation size={14} />
          <span>Widok pozycji pojazdów</span>
        </div>
        <div className="map-empty">
          <span className="map-pin">
            <MapPin size={28} />
          </span>
          <h3>Tu zaczyna się Twoja flota</h3>
          <p>Pozycje pojawią się po podłączeniu danych.</p>
        </div>
        <span className="map-caption">
          Ilustracja układu · mapa nie jest jeszcze podłączona
        </span>
      </div>
    </WidgetFrame>
  );
}
