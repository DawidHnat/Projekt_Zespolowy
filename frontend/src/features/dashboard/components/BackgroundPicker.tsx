import { useId, useRef } from "react";
import { Check, ImagePlus, Upload, Trash2 } from "lucide-react";
import {
  BACKGROUND_PRESETS, presetBackground,
  type BackgroundKind, type BackgroundPreferences,
} from "../model/background-model";
import type { BackgroundImageController } from "../model/useBackgroundImage";

type Props = {
  value: BackgroundPreferences;
  onChange: (value: BackgroundPreferences) => void;
  media: BackgroundImageController;
};
export function BackgroundPicker({ value, onChange, media }: Props) {
  const fileInput = useRef<HTMLInputElement>(null);
  const veilId = useId();
  const blurId = useId();
  const hasCustom = Boolean(media.url && media.image?.id === value.customId);
  const selectKind = (kind: BackgroundKind) => onChange({
    ...value, kind,
    customId: kind === "custom" ? media.image?.id ?? value.customId : value.customId,
  });
  const upload = async (file: File) => {
    const id = await media.upload(file);
    if (id) onChange({ ...value, kind: "custom", customId: id });
  };
  const remove = async () => {
    if (await media.remove()) onChange({ ...value, customId: null });
  };
  return (
    <fieldset className="background-settings">
      <legend>Tło przestrzeni</legend>
      <p>Dopasuj otoczenie kafelków. Tło działa w obu stylach.</p>
      <div className="background-modes" role="group" aria-label="Źródło tła">
        {([
          ["default", "Domyślne"], ["preset", "Galeria"], ["custom", "Własne"],
        ] as const).map(([kind, name]) => (
          <button key={kind} aria-pressed={value.kind === kind} disabled={media.busy}
            onClick={() => selectKind(kind)}>{name}</button>
        ))}
      </div>
      {value.kind === "preset" && (
        <div className="background-gallery" role="group" aria-label="Galeria teł">
          {BACKGROUND_PRESETS.map(preset => (
            <button key={preset.id} className="background-option"
              aria-label={`Tło: ${preset.name}`} aria-pressed={value.preset === preset.id}
              onClick={() => onChange({ ...value, preset: preset.id })}>
              <span className="background-thumbnail" style={{ backgroundImage: presetBackground(preset.id, import.meta.env.BASE_URL) }}>
                {value.preset === preset.id && <span className="background-selected"><Check size={13} /></span>}
              </span>
              <span className="background-caption"><strong>{preset.name}</strong><small>{preset.description}</small></span>
            </button>
          ))}
        </div>
      )}
      {value.kind === "custom" && (
        <div className="background-upload" aria-busy={media.busy}>
          {hasCustom ? (
            <div className="background-custom-preview">
              <img src={media.url} alt="Podgląd własnego tła" />
              <span>{media.image?.name}</span>
            </div>
          ) : (
            <div className="background-upload-placeholder">
              <ImagePlus size={26} aria-hidden="true" />
              <strong>Twoje zdjęcie, Twój widok</strong>
              <span>JPG, PNG lub WebP · do 10 MB</span>
            </div>
          )}
          <input ref={fileInput} type="file" hidden accept="image/jpeg,image/png,image/webp"
            aria-label="Plik własnego tła" onChange={event => {
              const file = event.currentTarget.files?.[0];
              event.currentTarget.value = "";
              if (file) void upload(file);
            }} />
          <div className="background-upload-actions">
            <button className="button button-secondary" disabled={media.busy || media.loading}
              onClick={() => fileInput.current?.click()}>
              <Upload size={15} />{media.busy ? "Przygotowywanie…" : hasCustom ? "Zmień zdjęcie" : "Wybierz zdjęcie"}
            </button>
            {hasCustom && <button className="icon-button" aria-label="Usuń własne zdjęcie" disabled={media.busy}
              onClick={() => void remove()}><Trash2 size={16} /></button>}
          </div>
          <p className="background-note" role="status">
            {media.busy ? "Przygotowuję i zapisuję zdjęcie…"
              : media.loading ? "Wczytuję zapisane zdjęcie…"
              : hasCustom && !media.persistent ? "Zdjęcie działa w tej sesji. Przeglądarka nie pozwoliła go zapisać."
              : value.customId && !hasCustom ? "Poprzednie zdjęcie nie jest dostępne. Dodaj je ponownie."
              : "Zdjęcie pozostaje w tej przeglądarce. Nie wysyłamy go na serwer."}
          </p>
          {media.error && <p className="background-error" role="alert">{media.error}</p>}
        </div>
      )}
      {(value.kind === "preset" || hasCustom) && (
        <div className="background-adjustments">
          <label htmlFor={veilId}>Wyciszenie tła<output aria-hidden="true">{value.veil}%</output></label>
          <input id={veilId} type="range" min="0" max="70" step="1" value={value.veil}
            aria-valuetext={`${value.veil} procent`} disabled={media.busy}
            onChange={event => onChange({ ...value, veil: Number(event.currentTarget.value) })} />
          <label htmlFor={blurId}>Rozmycie<output aria-hidden="true">{value.blur} px</output></label>
          <input id={blurId} type="range" min="0" max="16" step="1" value={value.blur}
            aria-valuetext={`${value.blur} pikseli`} disabled={media.busy}
            onChange={event => onChange({ ...value, blur: Number(event.currentTarget.value) })} />
          <p className="background-note">Osłona dopasowuje się do motywu. Zdjęcie wypełnia ekran bez rozciągania.</p>
        </div>
      )}
    </fieldset>
  );
}
