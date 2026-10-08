import { type LucideIcon } from "lucide-react";
import { useId, type ReactNode } from "react";

type Props = {
  title: string;
  icon: LucideIcon;
  children: ReactNode;
  className?: string;
  badge?: string;
};
export function WidgetFrame({
  title,
  icon: Icon,
  children,
  className = "",
  badge,
}: Props) {
  const titleId = useId();
  return (
    <section className={`widget ${className}`} aria-labelledby={titleId}>
      <header className="widget-header">
        <h2 id={titleId}>
          <Icon size={17} aria-hidden="true" />
          {title}
        </h2>
        <div className="widget-actions">
          {badge && <span className="widget-badge">{badge}</span>}
        </div>
      </header>
      <div className="widget-content">
        <div className="widget-content-inner">{children}</div>
      </div>
    </section>
  );
}
