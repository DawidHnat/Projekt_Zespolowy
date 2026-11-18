import { useState } from "react";
import { createRoot } from "react-dom/client";
import { DatePicker } from "../../src/shared/components/DatePicker";

function Fixture() {
  const [value, setValue] = useState("2026-10-17");
  const [disabled, setDisabled] = useState(false);
  const [changes, setChanges] = useState<string[]>([]);

  const change = (day: string) => {
    setChanges(previous => [...previous, day]);
    setValue(day);
  };

  return (
    <main>
      <DatePicker
        id="qa-date"
        label="Data testowa"
        value={value}
        onChange={change}
        minDate="2026-10-15"
        maxDate="2026-10-20"
        disabled={disabled}
      />
      <output data-testid="value">{value}</output>
      <output data-testid="changes">{changes.join(",")}</output>
      <button type="button" onClick={() => setValue("2026-10-19")}>
        Ustaw z zewnątrz
      </button>
      <button type="button" onClick={() => setDisabled(v => !v)}>
        Przełącz blokadę
      </button>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<Fixture />);
