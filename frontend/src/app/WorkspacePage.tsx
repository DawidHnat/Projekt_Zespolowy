import type { AppSection } from "./navigation";
import { EmptyState } from "../shared/components/EmptyState";
import { WidgetFrame } from "../shared/components/WidgetFrame";

export function WorkspacePage({ section }: { section: AppSection }) {
  if (!("placeholder" in section)) return null;

  return (
    <WidgetFrame
      title={section.title}
      icon={section.icon}
      badge="Planowane"
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
