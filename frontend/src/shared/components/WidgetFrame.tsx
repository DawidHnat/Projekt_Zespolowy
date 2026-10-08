import { X, type LucideIcon } from "lucide-react";
import { useId, type ReactNode } from "react";

type Props = {
  title: string;
  icon: LucideIcon;
  children: ReactNode;
  onHide: () => void;
  className?: string;
  badge?: string;
};
export function WidgetFrame({
  title,
  icon: Icon,
  children,
  onHide,
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
          <button
            className="icon-button widget-hide"
            onClick={onHide}
            aria-label={`Ukryj moduł: ${title}`}
            title="Ukryj moduł"
          >
            <X size={15} />
          </button>
        </div>
      </header>
      {children}
    </section>
  );
}
