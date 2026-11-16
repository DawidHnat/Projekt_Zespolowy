import { Check, Grip, Plus, RotateCcw } from "lucide-react";

type LayoutEditorControlsProps = {
  title: string;
  editing: boolean;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onReset: () => void;
  onWidgets?: () => void;
  disabled?: boolean;
  saving?: boolean;
};

export function LayoutEditorControls({
  title, editing, onEdit, onSave, onCancel, onReset, onWidgets, disabled = false, saving = false,
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
              disabled={disabled || saving}
            >
              <Plus size={19} />
            </button>
          )}
          <button
            className="icon-button"
            aria-label="Przywróć układ tego widoku"
            title="Przywróć układ tego widoku"
            onClick={onReset}
            disabled={disabled || saving}
          >
            <RotateCcw size={17} />
          </button>
          <button className="button button-secondary" onClick={onCancel} disabled={saving}>
            Anuluj
          </button>
          <button className="button button-primary" onClick={onSave} disabled={disabled || saving}>
            <Check size={16} /> {saving ? "Zapisywanie…" : "Zapisz układ"}
          </button>
        </>
      ) : (
        <button
          className="button button-primary layout-edit-trigger"
          aria-label="Edytuj układ"
          title="Edytuj układ"
          onClick={onEdit}
          disabled={disabled}
        >
          <Grip size={24} aria-hidden="true" />
        </button>
      )}
    </div>
  );
}
