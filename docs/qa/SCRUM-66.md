# SCRUM-66 — wspólny wybór dat

Zakres: `DatePicker`, jego styl zgodny z motywem i zastąpienie natywnego pola
w `TripDayPicker`. Bez zmian backendu, synchronizacji i danych floty.

## Sprawdzenie automatyczne

W `frontend/`: `npm test` i `npm run build`.
`tests/calendar-date.test.mjs` sprawdza rzeczywiste dni, rok przestępny,
granice zmiany czasu, lata poniżej 100, format polski, brak daty i włączające
ograniczenia. Dodatkowe uruchomienia tego pliku w `TZ=Pacific/Honolulu`
i `TZ=Asia/Tokyo` sprawdzają daty po obu stronach UTC.

## Odbiór przeglądarkowy autora — 27.10.2026

Sprawdzono w działającym localhost, w przeglądarce w aplikacji:

- Wybór dnia i przyciski Dzisiaj/Wczoraj: pole i opis dnia są zgodne.
- Wpisanie 31.02.2026 oraz daty po dozwolonym maksimum: błąd walidacji,
  bez przesunięcia dnia ani zmiany kontrolowanej daty. Poprawienie daty
  usuwa błąd. Osobno sprawdzono Enter, Tab i kliknięcie poza polem.
- Polski język, poniedziałek na początku tygodnia, dni po dzisiaj niedostępne.
- Jasne szkło z niebieskim akcentem oraz ciemne szkło z fioletowym akcentem:
  kolory powierzchni i zaznaczenia pochodzą z aktualnego motywu.
- Przy szerokości 390 px kalendarz ma 320 px; przy szerokości 320 px mieści
  się między x=8 a x=312. Tymczasowe zmiany viewportu wycofano po odbiorze.
- Strzałka w dół ustawia fokus na dniu. Escape zamyka kalendarz i wraca
  do pola. W Podróżach pojazdu wybranie dnia działa, a Escape pozostawia
  nadrzędny dialog otwarty. Kalendarz nie jest schowany pod dialogiem.

To sprawdzenie autora, nie niezależny odbiór QA. Osoba przeglądająca PR
powinna powtórzyć wybór daty na swoim urządzeniu. Fallback bez Popover API
jest w kodzie, lecz nie był przedmiotem odbioru na starszej przeglądarce.
Nie dodano rekordów demonstracyjnych ani nie zmieniono danych klienta.

## Źródła biblioteki

- [Opcje Flatpickr](https://flatpickr.js.org/options/)
- [Lokalizacja](https://flatpickr.js.org/localization/)
- [Stylowanie](https://flatpickr.js.org/themes/)
