import { useState } from "react";
export const vehicleFallback = `${import.meta.env.BASE_URL}brand/vehicle-fallback.svg`;
export function VehiclePhoto({ src, name }: { src?: string; name: string }) {
  const [failed, setFailed] = useState<string | undefined>();
  const photo = src && src !== failed;
  return (
    <div className={`vehicle-photo ${photo ? "has-photo" : ""}`}>
      <img
        src={photo ? src : vehicleFallback}
        alt={photo ? `Zdjęcie: ${name}` : ""}
        draggable={false}
        onError={() => setFailed(src)}
      />
      {!photo && <span>Twoja flota</span>}
    </div>
  );
}
