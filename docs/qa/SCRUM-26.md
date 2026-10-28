# SCRUM-26 — cel i opis przejazdu

Implementacja do przeglądu i odbioru QA (Marcel). Rodzic SCRUM-62 pozostaje
otwarty: raport okresu i pełna historia mają osobne zadania.

## Zakres i dane

Migracja `0005_trip_annotations` tworzy fakty przejazdu osobno od ręcznej notatki.
Nie ma danych demo ani importera WEBFLEET w tym przyroście. Do testu używaj
wyłącznie syntetycznego przejazdu w izolowanej bazie testowej. Nie dodawaj go
do bazy zespołu. Bez danych w wybranym dniu poprawnym wynikiem jest pusty widok.

Dawid w SCRUM-24 powinien użyć modelu `app.modules.trips.models.Trip` i upsertu
po `(vehicle_id, external_uid)`. UUID istniejącego przejazdu musi pozostać stałe;
importer aktualizuje tylko fakty źródłowe. Nie usuwa `TripAnnotation` ani jej pól.
Foreign key bez cascade chroni notatkę przed przypadkowym usunięciem przejazdu.

## Scenariusze odbioru

1. Admin/editor: Pojazdy → ikona „Szczegóły” → Podróże → dzień z zapisanym
   przejazdem → wybór przejazdu. Cel i opis początkowo są puste, bez udawanego
   autora. Zapisz oba pola, zamknij szczegóły i otwórz ponownie: wartości,
   autor i czas ostatniej zmiany są zachowane. Dane czasu/dystansu są bez zmian.
2. Zmień wyłącznie opis przez PATCH z bieżącą wersją: cel zostaje. Puste pole
   lub `null` usuwa wpis. Brak obu pól, błędna wersja, ponad 200/2000 znaków
   lub niedozwolone znaki dają 422 i nie zapisują zmian. Cel jest jednowierszowy.
3. Dwa konta otwierają tę samą wersję. Pierwsze zapisuje. Drugie dostaje 409,
   zachowuje wpisany tekst i ma zablokowany zwykły zapis. „Sprawdź bieżącą
   wersję” pokazuje zdalną notatkę. Dopiero „Kontynuuj z moim tekstem” pozwala
   świadomie zapisać na podstawie nowej wersji. Kolejna zmiana innej osoby
   ponownie daje konflikt. Dotyczy także pierwszego zapisu pustej notatki.
4. Zasymuluj 503 lub brak sieci przy PATCH: błąd jest widoczny, tekst zostaje,
   można ponowić zapis. Nie pokazuj sukcesu bez potwierdzenia odpowiedzi API.
   Zmiana dnia, strony i przejazdu jest zablokowana podczas edycji. Zamknięcie
   lub inna zakładka pyta o porzucenie tekstu; odrzucenie pytania zachowuje go.
   Odświeżenie strony ostrzega o niezapisanym wpisie.
5. Viewer widzi treść i audyt, ale nie zapisuje; ręczny PATCH daje 403.
   Brak sesji daje 401, błędny Origin 403. Obcy lub nieistniejący przejazd
   daje 404. Wylogowanie/wygaśnięcie sesji usuwa prywatny widok zgodnie z
   istniejącą obsługą logowania; szkic nie jest zapisywany w localStorage.
6. Ponowne uaktualnienie faktów tego samego Trip zachowuje notatkę. Lista
   ma stabilną paginację, puste wartości nie zmieniają się w zero. Sprawdź
   przejazd przez północ oraz dni zmiany czasu Europe/Warsaw (23/25 godzin).
7. Jasny i ciemny motyw, szkło, ekran 390 px: pola i przyciski mieszczą się
   w dialogu, tekst jest czytelny. Tab/Shift+Tab, strzałki zakładek i Escape
   pozwalają obsłużyć dialog z klawiatury.

## Weryfikacja automatyczna

W `frontend/`: `npm test` i `npm run build`.
W `backend/`: `ruff check .`, `ruff format --check .`, `pytest`.
`TEST_DATABASE_URL` musi wskazywać osobną bazę PostgreSQL o nazwie zaczynającej
się od `fleet_flow_test`: test migracji wykonuje downgrade do pustego schematu.
CI sprawdza migracje i dwa równoległe zapisy z tą samą wersją na PostgreSQL 17,
zarówno przed pierwszą notatką, jak i po jej utworzeniu.

Lokalnie 26.10.2026: testy backendu na PostgreSQL 17, frontend i build przeszły.
Przeglądarka: zapis/ponowny odczyt, symulowane 503, konflikt/porównanie/ponowienie
oraz ekran 390 px sprawdzone na osobnej syntetycznej bazie, bez WEBFLEET/SMTP.
Niezależne review i odbiór QA pozostają przed zamknięciem zadania.
