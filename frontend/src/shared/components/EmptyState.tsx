import type { LucideIcon } from "lucide-react";
export function EmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <div className="empty-state">
      <span className="empty-icon">
        <Icon size={25} aria-hidden="true" />
      </span>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}
