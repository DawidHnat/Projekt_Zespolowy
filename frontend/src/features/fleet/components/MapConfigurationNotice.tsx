import { MapPin } from "lucide-react";
import { EmptyState } from "../../../shared/components/EmptyState";

export default function MapConfigurationNotice() {
  return (
    <div className="map-canvas">
      <EmptyState
        icon={MapPin}
        title="Mapa czeka na konfigurację"
        description="Administrator musi skonfigurować dostęp do mapy. Lista pojazdów jest dostępna."
      />
    </div>
  );
}
