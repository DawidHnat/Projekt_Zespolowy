import { Check, Grip, Plus, RotateCcw } from "lucide-react";

type LayoutEditorBarProps = {
  title: string;
  onSave: () => void;
  onCancel: () => void;
  onReset: () => void;
  onWidgets?: () => void;
};

export function LayoutEditorBar({
  title, onSave, onCancel, onReset, onWidgets,
}: LayoutEditorBarProps) {
  return (
    <div className="layout-edit-bar" role="region" aria-label={`Edycja układu — ${title}`}>
      <div className="edit-bar-intro">
        <span className="edit-bar-icon"><Grip size={19} /></span>
        <div>
          <strong>Ułóż po swojemu</strong>
          <p>Chwyć kafelek w dowolnym miejscu · obrys pokazuje miejsce upuszczenia</p>
        </div>
      </div>
      <div className="edit-bar-actions">
        {onWidgets && (
          <button
            className="icon-button"
            aria-label="Wybierz widgety"
            title="Wybierz widgety"
            onClick={onWidgets}
          >
            <Plus size={19} />
          </button>
        )}
        <button
          className="icon-button"
          aria-label="Przywróć układ tego widoku"
          title="Przywróć układ tego widoku"
          onClick={onReset}
        >
          <RotateCcw size={17} />
        </button>
        <button className="button button-secondary" onClick={onCancel}>Anuluj</button>
        <button className="button button-primary" onClick={onSave}>
          <Check size={16} /> Zapisz układ
        </button>
      </div>
    </div>
  );
}
