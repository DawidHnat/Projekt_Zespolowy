import { useEffect, useId, useRef, useState } from "react";
import flatpickr from "flatpickr";
import { Polish } from "flatpickr/dist/l10n/pl.js";
import type { Instance } from "flatpickr/dist/types/instance";
import { CalendarDays, X } from "lucide-react";
import { calendarDate, calendarInputError, calendarInputValue, calendarValue, displayCalendarDate } from "./calendar-date";
import "flatpickr/dist/flatpickr.css";
import "./date-picker.css";

type Props = {
  value: string;
  onChange: (value: string) => void;
  label: string;
  id?: string;
  minDate?: string;
  maxDate?: string;
  disabled?: boolean;
  required?: boolean;
  allowClear?: boolean;
};

export function DatePicker(props: Props) {
  const { value, label, minDate, maxDate, disabled = false, required = false, allowClear = false } = props;
  const generatedId = useId();
  const id = props.id ?? generatedId;
  const calendarId = `${id}-calendar`;
  const root = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const picker = useRef<Instance | null>(null);
  const latest = useRef(props);
  latest.current = props;
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const field = input.current!;
    const host = root.current!;
    // Validate before Flatpickr parses typed dates: it otherwise normalizes 31.02.
    const commitInput = () => {
      const error = calendarInputError(field.value, latest.current);
      field.setCustomValidity(error);
      field.setAttribute("aria-invalid", String(Boolean(error)));
      if (error) return false;
      const value = calendarInputValue(field.value)!;
      const current = picker.current?.selectedDates[0];
      if (value !== (current ? calendarValue(current) : "")) {
        picker.current?.setDate(calendarDate(value) ?? [], true);
      }
      return true;
    };
    const blur = (event: FocusEvent) => {
      if (event.relatedTarget instanceof Node && picker.current?.calendarContainer.contains(event.relatedTarget)) return;
      // Own typed input commits; Flatpickr's outside-click parsing can otherwise
      // normalize invalid dates or update its DOM without notifying React.
      event.stopImmediatePropagation();
      commitInput();
      picker.current?.close();
    };
    const clearError = () => {
      field.setCustomValidity("");
      field.removeAttribute("aria-invalid");
    };
    const keydown = (event: KeyboardEvent) => {
      const instance = picker.current;
      if (event.key === "Escape" && instance?.isOpen) {
        event.preventDefault();
        event.stopImmediatePropagation();
        field.focus();
        instance.close();
      } else if (event.key === "ArrowDown" && event.target === field && instance) {
        event.preventDefault();
        instance.open();
        (instance.selectedDateElem ?? instance.todayDateElem ??
          instance.calendarContainer.querySelector<HTMLElement>(".flatpickr-day:not(.flatpickr-disabled):not(.hidden)"))?.focus();
      } else if (event.key === "Enter" && event.target === field) {
        event.preventDefault();
        event.stopImmediatePropagation();
        if (commitInput()) instance?.close();
        else field.reportValidity();
      }
    };
    const outside = (event: Event) => {
      if (picker.current?.isOpen && event.target instanceof Node && !host.contains(event.target)) {
        commitInput();
        picker.current.close();
      }
    };
    field.addEventListener("blur", blur);
    field.addEventListener("input", clearError);
    host.addEventListener("keydown", keydown, true);
    document.addEventListener("mousedown", outside, true);
    document.addEventListener("touchstart", outside, true);
    document.addEventListener("focus", outside, true);

    const floating = typeof HTMLElement.prototype.showPopover === "function";
    const position = (instance: Instance) => {
      if (!floating || !instance.isOpen) return;
      const rect = field.parentElement!.getBoundingClientRect();
      const calendar = instance.calendarContainer;
      const width = calendar.offsetWidth;
      const height = calendar.offsetHeight;
      const gap = 8;
      const top = rect.bottom + gap + height <= window.innerHeight - gap
        ? rect.bottom + gap
        : Math.max(gap, rect.top - height - gap);
      calendar.style.left = `${Math.max(gap, Math.min(rect.left, window.innerWidth - width - gap))}px`;
      calendar.style.top = `${top}px`;
    };
    const instance = flatpickr(field, {
      locale: Polish,
      dateFormat: "d.m.Y",
      ariaDateFormat: "j F Y",
      defaultDate: calendarDate(latest.current.value),
      minDate: minDate ? calendarDate(minDate) : undefined,
      maxDate: maxDate ? calendarDate(maxDate) : undefined,
      allowInput: true,
      animate: false,
      disableMobile: true,
      appendTo: host,
      ignoredFocusElements: [host],
      position,
      onReady: (_, __, ready) => {
        const calendar = ready.calendarContainer;
        calendar.id = calendarId;
        calendar.classList.add("ff-calendar");
        calendar.setAttribute("role", "dialog");
        calendar.setAttribute("aria-label", `Wybierz datę: ${latest.current.label}`);
        if (floating) calendar.setAttribute("popover", "manual");
        else calendar.classList.add("ff-calendar-inline");
        ready.prevMonthNav.setAttribute("aria-label", "Poprzedni miesiąc");
        ready.nextMonthNav.setAttribute("aria-label", "Następny miesiąc");
      },
      onChange: (dates) => {
        if (!dates.length && latest.current.required) return;
        clearError();
        latest.current.onChange(dates.length ? calendarValue(dates[0]) : "");
      },
      onOpen: (_, __, current) => {
        if (latest.current.disabled) { current.close(); return; }
        if (floating) current.calendarContainer.showPopover();
        position(current);
        setOpen(true);
      },
      onClose: (_, __, current) => {
        if (floating && current.calendarContainer.matches(":popover-open")) current.calendarContainer.hidePopover();
        setOpen(false);
      },
    });
    picker.current = instance;
    const reposition = () => position(instance);
    window.addEventListener("resize", reposition);
    document.addEventListener("scroll", reposition, true);
    return () => {
      window.removeEventListener("resize", reposition);
      document.removeEventListener("scroll", reposition, true);
      field.removeEventListener("blur", blur);
      field.removeEventListener("input", clearError);
      host.removeEventListener("keydown", keydown, true);
      document.removeEventListener("mousedown", outside, true);
      document.removeEventListener("touchstart", outside, true);
      document.removeEventListener("focus", outside, true);
      instance.destroy();
      picker.current = null;
    };
    // Instantiate once; the following effect synchronizes controlled props.
  }, [calendarId]);

  useEffect(() => {
    const instance = picker.current;
    if (!instance) return;
    instance.set({ minDate: minDate ? calendarDate(minDate) : undefined, maxDate: maxDate ? calendarDate(maxDate) : undefined });
    instance.setDate(calendarDate(value) ?? [], false);
    input.current?.setCustomValidity("");
    input.current?.removeAttribute("aria-invalid");
    if (disabled) instance.close();
  }, [value, minDate, maxDate, disabled]);

  return (
    <div className="date-picker" ref={root}>
      <div className="date-picker-field" data-disabled={disabled || undefined}>
        <CalendarDays size={16} aria-hidden="true" />
        <input
          ref={input}
          id={id}
          type="text"
          defaultValue={displayCalendarDate(value)}
          aria-label={label}
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-controls={calendarId}
          placeholder="DD.MM.RRRR"
          autoComplete="off"
          disabled={disabled}
          required={required}
        />
        {allowClear && !required && value && (
          <button type="button" className="date-picker-clear" disabled={disabled}
            aria-label={`Wyczyść datę: ${label}`} onClick={() => picker.current?.clear()}>
            <X size={14} aria-hidden="true" />
          </button>
        )}
      </div>
    </div>
  );
}
