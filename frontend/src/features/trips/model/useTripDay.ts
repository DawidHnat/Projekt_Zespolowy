import { useEffect, useState } from "react";
import { previousDay, validTripDay, warsawDay } from "./trip-day";

// Relative choices follow Polish midnight; a custom date remains fixed.
export function useTripDay() {
  const [today, setToday] = useState(warsawDay);
  const [choice, setChoice] = useState("today");
  useEffect(() => {
    const update = () => setToday(warsawDay());
    const timer = setInterval(update, 60000);
    document.addEventListener("visibilitychange", update);
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", update);
    };
  }, []);
  const yesterday = previousDay(today);
  return {
    today,
    value: choice === "today" ? today : choice === "yesterday" ? yesterday : choice,
    select: (day: string) => {
      if (!validTripDay(day) || day > today) return;
      setChoice(day === today ? "today" : day === yesterday ? "yesterday" : day);
    },
  };
}
