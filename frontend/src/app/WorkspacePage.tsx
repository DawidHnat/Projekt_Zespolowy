import type { AppSection } from "./navigation";
import { FleetMapPage } from "../features/fleet/components/FleetMapPage";
import { EmptyState } from "../shared/components/EmptyState";
import { WidgetFrame } from "../shared/components/WidgetFrame";

export function WorkspacePage({ section }: { section: AppSection }) {
  if (section.id === "map") return <FleetMapPage />;
  if (!("placeholder" in section)) return null;

  return (
    <WidgetFrame
      title={section.title}
      icon={section.icon}
      badge="W przygotowaniu"
      className="planned-page"
    >
      <EmptyState
        icon={section.icon}
        title={section.placeholder.title}
        description={section.placeholder.description}
      />
    </WidgetFrame>
  );
}
