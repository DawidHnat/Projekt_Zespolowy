# SCRUM-66 — wspólny wybór dat

Zakres: `DatePicker`, jego styl zgodny z motywem i zastąpienie natywnego pola
w `TripDayPicker`. Bez zmian backendu, synchronizacji i danych floty.

## Sprawdzenie automatyczne

W `frontend/`: `npm test` i `npm run build`.
`tests/calendar-date.test.mjs` sprawdza rzeczywiste dni, rok przestępny,
granice zmiany czasu, lata poniżej 100, format polski i brak daty.
Dodatkowe uruchomienia tego pliku w `TZ=Pacific/Honolulu`
i `TZ=Asia/Tokyo` sprawdzają daty po obu stronach UTC.

## Odbiór przeglądarkowy autora — 27.10.2026

Sprawdzono w działającym localhost, w przeglądarce w aplikacji:

- Wybór dnia i przyciski Dzisiaj/Wczoraj: pole i opis dnia są zgodne.
- Widoczne pole jest przyciskiem. Klawisze tekstowe i Backspace nie
  zmieniają daty, a dwuklik nie zaznacza tekstu (`selectionLength=0`).
  Nie ma widocznego edytowalnego pola tekstowego; ukryte pole techniczne
  i rok kalendarza są tylko do odczytu. Wybór przyszłego, wyłączonego dnia
  nie zmienia daty. Obowiązuje wybór wyłącznie z kalendarza lub skrótów.
- Polski język, poniedziałek na początku tygodnia, dni po dzisiaj niedostępne.
- Jasne szkło z niebieskim akcentem oraz ciemne szkło z fioletowym akcentem:
  kolory powierzchni i zaznaczenia pochodzą z aktualnego motywu.
- Kompaktowy widok komputera ma 280 × 282 px. Przy szerokości viewportu
  320 px mieści się między x=32 a x=312. Tymczasowe zmiany viewportu
  wycofano po odbiorze. Reguła CSS dla wskaźnika dotykowego powiększa dni
  i szerokość do 320 px; wymaga osobnego odbioru na urządzeniu dotykowym.
- Przycisk z aktywnym `:focus-visible` nie ma dodatkowego czarnego obrysu tekstu;
  fokus pozostaje widoczny na całej otoczce. Nagłówek mieści miesiąc, rok
  i obie strzałki, w tym nieaktywną strzałkę przyszłego miesiąca. Po zmianie
  siatki wybór 26 października nadal ustawia Wczoraj i wartość pola.
- Enter otwiera kalendarz, strzałka w dół ustawia fokus na dniu. Escape
  zamyka kalendarz i wraca do przycisku. W Podróżach pojazdu ten sam przycisk
  nie pozwala edytować ani zaznaczać daty. Wybór dnia działa, a Escape pozostawia
  nadrzędny dialog otwarty. Kalendarz nie jest schowany pod dialogiem.

To sprawdzenie autora, nie niezależny odbiór QA. Osoba przeglądająca PR
powinna powtórzyć wybór daty na swoim urządzeniu. Fallback bez Popover API
jest w kodzie, lecz nie był przedmiotem odbioru na starszej przeglądarce.
Nie dodano rekordów demonstracyjnych ani nie zmieniono danych klienta.

## Źródła biblioteki

- [Opcje Flatpickr](https://flatpickr.js.org/options/)
- [Lokalizacja](https://flatpickr.js.org/localization/)
- [Stylowanie](https://flatpickr.js.org/themes/)
