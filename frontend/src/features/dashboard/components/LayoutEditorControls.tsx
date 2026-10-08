import { Check, Grip, Plus, RotateCcw } from "lucide-react";

type LayoutEditorControlsProps = {
  title: string;
  editing: boolean;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onReset: () => void;
  onWidgets?: () => void;
};

export function LayoutEditorControls({
  title, editing, onEdit, onSave, onCancel, onReset, onWidgets,
}: LayoutEditorControlsProps) {
  return (
    <div
      className="layout-editor-controls"
      role={editing ? "group" : undefined}
      aria-label={editing ? `Edycja układu — ${title}` : undefined}
    >
      {editing ? (
        <>
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
          <button className="button button-secondary" onClick={onCancel}>
            Anuluj
          </button>
          <button className="button button-primary" onClick={onSave}>
            <Check size={16} /> Zapisz układ
          </button>
        </>
      ) : (
        <button className="button button-primary" onClick={onEdit}>
          <Grip size={17} /> Edytuj układ
        </button>
      )}
    </div>
  );
}
