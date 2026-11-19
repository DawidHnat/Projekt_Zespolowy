# SCRUM-21 — Procedura niezależnego odbioru QA: Mapa na żywo (Mapbox)

**Klucz zadania:** [SCRUM-21](https://fleet-flow.atlassian.net/browse/SCRUM-21) — Wizualizacja floty na mapie (Live Map)  
**Autor specyfikacji procedury:** Jakub Nazarewicz (`jnazarewiczs`) — Developer  
**Dedykowany tester QA:** Marcel Głowacki (`mglowacki0`)  
**Zakres:** Wyłącznie kryteria SCRUM-21 (sama mapa na żywo, markery DOM, nakładanie pozycji, brak GPS, stany pusty/błąd, obsługa metadanych). Nie mylić z szerszym zakresem SCRUM-23 (pełna agregacja historii i telemetrii).  
**Zasada bezpieczeństwa:** Żadnych danych klientów, haseł ani żywego API WEBFLEET. Procedura operuje w 100% na danych syntetycznych w izolacji.

---

## 1. Środowisko i przygotowanie testów

### 1.1. Wymagania wstępne
- Przeglądarka: Chromium / Google Chrome lub Microsoft Edge (zgodnie z [docs/qa/browser-scope-20261119.md](browser-scope-20261119.md); Safari jest wyłączone z obowiązkowego zakresu QA).
- Rozdzielczości testowe:
  - **Desktop:** 1440 × 1000 px (widok z pulpitem / mapą obok listy)
  - **Mobile:** 390 × 844 px (widok wąski, panel mapy dostosowany do ekranu dotykowego)
- Motyw: Jasny oraz Ciemny.

### 1.2. Uruchomienie lokalnego środowiska z danymi syntetycznymi
```bash
# W terminalu 1 (backend w trybie testowym bez synchronizacji z zewnątrz):
cd backend
source ../.venv/bin/activate
SYNC_ENABLED=false uvicorn app.main:app --port 8000

# W terminalu 2 (frontend):
cd frontend
npm run dev
```
Alternatywnie w testach Playwright można wykorzystać mockowanie żądań sieciowych (`page.route('/api/v1/vehicles*', ...)`).

---

## 2. Scenariusze testowe do weryfikacji przez QA

### Scenariusz 1: Dwa pojazdy o identycznych współrzędnych (Marker Overlap)

**Cel:** Weryfikacja, że pojazdy parkujące w tym samym miejscu nie znikają pod pojedynczym markerem, a użytkownik ma możliwość wyboru każdego z nich.

1. **Dane wejściowe (syntetyczne):**
   - Pojazd A: ID `veh-alpha`, rejestracja `KR-001AA`, status `stopped`, współrzędne: `[19.9449, 50.0647]` (Kraków).
   - Pojazd B: ID `veh-bravo`, rejestracja `KR-002BB`, status `stopped`, współrzędne: `[19.9449, 50.0647]` (identyczne współrzędne).
2. **Kroki:**
   - Otwórz widok mapy floty.
   - Zlokalizuj marker w punkcie `[19.9449, 50.0647]`.
   - Kliknij w marker myszą (lub dotknij na ekranie mobilnym).
3. **Oczekiwany rezultat:**
   - Aplikacja wykrywa kolizję trafienia (`vehiclesAtPoint` w promieniu kolizji 18 px).
   - Wyświetla się panel boczny / okno wyboru `aside.map-overlap` z nagłówkiem **„Wybierz pojazd”**.
   - Na liście widoczne są oba pojazdy (`KR-001AA` oraz `KR-002BB`) wraz ze statusami.
   - Kliknięcie w jeden z pojazdów zamyka listę kolizji, zaznacza wybrany pojazd i otwiera jego kartę podglądu (`VehicleMapPreview`).
   - Przycisk zamknięcia („Zamknij” / `x`) zamyka panel bez zmiany zaznaczenia.

---

### Scenariusz 2: Pojazd bez pozycji GPS (Brak współrzędnych)

**Cel:** Pojazdy bez sygnału GPS nie mogą psuć widoku mapy, nie mogą powodować błędów JavaScript i muszą być czytelnie oznaczone.

1. **Dane wejściowe:**
   - Pojazd C: ID `veh-nogps`, rejestracja `WA-999XX`, współrzędne `null` lub brak obiektu `geometry`.
   - Pojazd D: ID `veh-valid`, rejestracja `WA-111OK`, współrzędne `[21.0122, 52.2297]` (Warszawa).
2. **Kroki:**
   - Wczytaj flotę zawierającą oba pojazdy.
   - Sprawdź listę pojazdów obok mapy.
   - Sprawdź zachowanie przycisku **„Cała flota”** (`fitBounds`).
   - Kliknij na liście pojazd `veh-nogps`.
3. **Oczekiwany rezultat:**
   - Na liście pojazd `veh-nogps` posiada widoczny status / adnotację **„Brak pozycji”** (lub brak współrzędnych).
   - Funkcja `validFeatures` wyklucza `veh-nogps` z geometrii mapy (brak markera w `[0,0]` czy na środku oceanu).
   - Przycisk „Cała flota” dopasowuje widok wyłącznie do pojazdu `veh-valid` (`boundsForFeatures` nie rzuca wyjątku).
   - Kliknięcie pojazdu bez GPS na liście nie powoduje błędu w konsoli przeglądarki (`TypeError / Unhandled Promise Rejection`).

---

### Scenariusz 3: Pełne, puste oraz przestarzałe pola metadanych (SCRUM-51 / SCRUM-22)

**Cel:** Weryfikacja prezentacji metadanych w karcie podglądu (`VehicleMapPreview`) oraz w pełnym oknie szczegółów (`VehicleDetailsDialog`).

1. **Kroki dla pojazdu z pełnymi danymi:**
   - Wybierz pojazd z kompletem danych (marka: `Skoda`, model: `Octavia`, rocznik: `2023`, VIN: `TMB...`, prędkość: `68 km/h`, adres: `Al. Jerozolimskie 1, Warszawa`, czas: sprzed 2 minut).
   - **Oczekiwany rezultat:** Karta podglądu i okno szczegółów poprawnie wyświetlają markę, model, rok, VIN, prędkość sformatowaną jako `68 km/h` (zgodnie z `fix(SCRUM-22)` i SCRUM-14), sformatowany adres oraz czas relatywny.
2. **Kroki dla pojazdu z polami pustymi (`null`):**
   - Wybierz pojazd bez rocznika (`production_year: null`), bez VIN (`vin: null`), bez adresu (`address: null`).
   - **Oczekiwany rezultat:** W miejscach brakujących pól widoczny jest neutralny symbol (np. `—` lub puste pole); brak tekstów `"null"`, `"undefined"` czy błędów parsowania.
3. **Kroki dla danych przestarzałych (Stale Data, pomiar > 900 s temu):**
   - Wybierz pojazd z pozycją sprzed 3 godzin.
   - **Oczekiwany rezultat:** Wyświetla się etykieta **„Ostatni znany stan”** oraz relatywny wiek pomiaru (np. „Pozycja sprzed 3 godz.”). Zgodnie z zasadą bezpieczeństwa prędkość z nieaktualnego pomiaru nie jest prezentowana jako aktualna prędkość w ruchu.

---

### Scenariusz 4: Pusta flota (Zero pojazdów) oraz wyczyszczenie filtrów

**Cel:** Weryfikacja stanu zerowego mapy.

1. **Kroki przy pustej bazie:**
   - Skonfiguruj odpowiedź API: `{ "total": 0, "features": [] }`.
   - Otwórz mapę.
   - **Oczekiwany rezultat:**
     - Mapa centruje się na domyślnym widoku (Polska, współrzędne `[19, 52]`, zoom 5).
     - Wyświetla się komunikat `mapEmptyState`: **„Flota jest pusta”**.
     - Wskaźnik notatki mapy informuje: `0 pozycji · 0 pojazdów`.
2. **Kroki przy pustym wyniku wyszukiwania / filtra:**
   - Wpisz w filtrze wyszukiwania frazę, która nie pasuje do żadnego auta (np. `xyz999`).
   - **Oczekiwany rezultat:**
     - Wyświetla się przycisk **„Wyczyść filtry”**.
     - Kliknięcie przycisku czyści pole wyszukiwania i przywraca widok wszystkich dostępnych pojazdów.

---

### Scenariusz 5: Awaria API lub błąd sieci (API Failure / Offline)

**Cel:** Weryfikacja odporności mapy na brak odpowiedzi backendu i zachowanie danych podręcznych.

1. **Kroki przy początkowej awarii (Cold start z błędem 500):**
   - Zablokuj endpoint `/api/v1/vehicles` (HTTP 500 lub zablokowane żądanie w Network DevTools).
   - Załaduj stronę.
   - **Oczekiwany rezultat:**
     - Widoczny czytelny komunikat stanu błędu: **„Dane floty niedostępne”**.
     - Dostępny jest przycisk **„Spróbuj ponownie”** (`action: "retry"`).
     - Aplikacja nie wpada w pętlę ciągłych zapytań (throttling/backoff).
2. **Kroki przy chwilowej awarii w trakcie pracy (Cache retention):**
   - Załaduj poprawnie pojazdy na mapę.
   - Włącz tryb Offline lub zwróć błąd HTTP 500 przy kolejnym cyklu odpytywania (co 10 s).
   - **Oczekiwany rezultat:**
     - Wcześniej załadowane markery **pozostają na mapie** (zgodnie z testem `map distinguishes an unavailable source from missing GPS and preserves cached positions` w `frontend/tests/map.test.mjs`).
     - Pojawia się dyskretny pasek/ostrzeżenie o braku łączności, ale flota nie znika z ekranu.

---

## 3. Matryca weryfikacji QA dla Marcela Głowackiego

| Nr | Scenariusz | Warunek sukcesu | Wynik Marcela | Status |
| :-: | :--- | :--- | :-: | :-: |
| 1 | Kolizja pozycji (Overlap) | Wykrycie kolizji, panel `aside.map-overlap`, lista wyboru auta | Do uzupełnienia | Oczekuje |
| 2 | Brak sygnału GPS | Oznaczenie na liście, wykluczenie z `fitBounds`, brak błędów JS | Do uzupełnienia | Oczekuje |
| 3 | Metadane i jednostka km/h | Poprawne km/h, brak `"undefined"`, etykieta „Ostatni znany stan” | Do uzupełnienia | Oczekuje |
| 4 | Pusta flota / Filtry | Komunikat „Flota jest pusta”, działający przycisk „Wyczyść filtry” | Do uzupełnienia | Oczekuje |
| 5 | Awaria API / Offline | Komunikat błędu, przycisk retry, zachowanie markerów z pamięci | Do uzupełnienia | Oczekuje |
| 6 | Dostępność / Mobile | Działanie na 390 × 844 px, obsługa klawiaturą markerów | Do uzupełnienia | Oczekuje |

*Podpis testera QA:* Marcel Głowacki (`mglowacki0`)  
*Data weryfikacji:* `[RRRR-MM-DD]`  
*Środowisko:* Chromium / Windows / Linux (bez Safari)  
*Końcowy werdykt:* `PASS / FAIL / BLOCKED`
