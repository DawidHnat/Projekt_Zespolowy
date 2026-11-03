# Model danych i kontrakt API — SCRUM-36

Status: projekt do przeglądu zespołu. Przykłady w `contracts/api-design.json`
są syntetyczne. Pole `delivery` rozróżnia pierwszy przyrost od dalszego MVP;
opis operacji nie oznacza jej implementacji.

## Własność i relacje

| Encja | Identyfikator i relacje | Własność danych |
|---|---|---|
| Vehicle | UUID aplikacji; unikalne `(source_account, external_uid)` | WEBFLEET: nazwa, numer, rejestracja, typ, aktywność |
| Measurement | jedna ostatnia próbka na Vehicle; czas pozycji i czas odbioru | WEBFLEET: GPS, zapłon, postój, licznik; brakujące wartości są `null` |
| Driver | UUID; imię/nazwa, aktywność | **Wyłącznie ręczny wpis w Fleet-Flow**, bez raportów kierowców WEBFLEET |
| DriverAssignment | Vehicle → Driver, przedział `[valid_from, valid_to)` | ręczne przypisanie; na początek aktualne przypisanie na Vehicle |
| Trip | UUID; Vehicle + unikalny identyfikator przejazdu źródła | WEBFLEET: czas, dystans, punkty trasy; import historii w dalszym zadaniu |
| TripAnnotation | jeden rekord na Trip, autor User, wersja | ręczny cel/opis; synchronizacja nie nadpisuje |
| Rule | UUID, typ, próg, aktywność, opcjonalny Vehicle | użytkownik; tylko obsługiwane typy reguł |
| DailyDistance | Vehicle + polska data pomiaru; dystans i granice obserwacji | dolna granica dystansu z kolejnych pomiarów, nie pełna historia dnia (SCRUM-31) |
| Alert | UUID, Rule, Vehicle, czas zdarzenia, klucz deduplikacji | wynik reguły; odczyt osobno per User w AlertReceipt |
| User / Session | UUID / hash losowego tokenu sesji, termin ważności | lokalne konta aplikacji, niezależne od Driver i WEBFLEET |
| SyncState | klucz konta źródła, próba/sukces, bezpieczny kod błędu | koordynacja odpytywania i stan pamięci podręcznej |

UID dostawcy pozostaje wewnętrzny; API pokazuje UUID aplikacji. Zmiana nazwy,
numeru lub rejestracji nie tworzy nowego pojazdu. Usunięcie pojazdu ze źródła
dezaktywuje rekord po kompletnym odczycie, bez usuwania historii i ręcznych pól.
Nie importujemy nazw, loginów, kontaktów ani innych pól kierowców ze źródła.
User oznacza osobę korzystającą z aplikacji, Driver — ręcznie opisany wpis floty.

## Jednostki, czas i jakość

- GPS: stopnie WGS84; GeoJSON ma kolejność `[longitude, latitude]`. Para musi być
  kompletna, skończona i w zakresie. Jakość `A` pozwala pokazać pozycję; inne
  jakości nie są traktowane jako aktualny punkt. `(0, 0)` nie jest brakiem danych.
- Licznik: km, maksymalnie jeden znak dziesiętny; snapshot WEBFLEET ma jednostkę
  100 m. Dystans przejazdu: km z konwersji metrów; czas trwania: sekundy.
- Prędkość: `speed_kmh` lub `null`. Jednostka pola snapshotu nie została
  potwierdzona w SCRUM-14, dlatego pierwszy przyrost zwraca `null`.
  Jednostki raportu tras nie przenosimy automatycznie na snapshot.
- Daty: ISO 8601 z UTC (`Z` lub `+00:00`), świadome strefy w bazie. Przeglądarka
  prezentuje `Europe/Warsaw`. Przedziały raportów są półotwarte `[from, to)`.
  Formularz lokalnych dat przelicza obie granice osobno, również przy zmianie DST.
- `position_at` to czas pomiaru pozycji; `received_at` to czas pobrania.
  Odbiór starego punktu nie czyni go nowym. Próbka starsza niż 15 min lub bez
  czasu jest nieaktualna. Brak pomiaru daje status `unknown`; stary — `offline`.
  Świeży `standstill=false` daje `moving`, `standstill=true` — `stopped`.
  Zapłon i jakość GPS są osobnymi polami, nie zastępują statusu ruchu.
- Brak wartości to `null`, nie zero, pusta data ani wymyślony punkt. Po awarii
  źródła ostatnie dane pozostają dostępne z `source.status=degraded` oraz czasem
  ostatniego sukcesu. Zimny cache daje 503 `SOURCE_UNAVAILABLE`; poprawna pusta
  flota daje 200 z pustą listą.

## Zasady HTTP

Prefiks `/api/v1`. Paginacja: `page` od 1, `page_size` 1–100, domyślnie 25;
`total` po filtrach. Sortowanie listy po nazwie i UUID jest stabilne. `q` szuka
w nazwie, rejestracji i numerze, maksymalnie 100 znaków; `status` jest enumem.
Mapa pobiera te same filtry, wszystkie pasujące pozycje (bez paginacji listy).
Źródło nie jest odpytywane na żądanie przeglądarki. Wspólny worker synchronizuje
nie częściej niż raz na 60 s; blokada w PostgreSQL obejmuje wszystkie procesy.

Sesja jest losowym tokenem w HttpOnly cookie, SameSite=Strict; Secure w HTTPS.
Nie przechowujemy hasła ani tokenu w localStorage. Wszystkie dane floty wymagają
sesji. Operacje zapisujące sprawdzają Origin i rolę (`admin`, `editor`, `viewer`).
Brak publicznej rejestracji. Błędy: `{ "error": { "code": "...", "message":
"..." } }`, bez treści odpowiedzi dostawcy, SQL, sekretów czy stack trace.
400/422 — walidacja, 401 — brak sesji, 403 — rola/Origin, 404 — brak rekordu,
409 — konflikt wersji, 429 — limit, 503 — niedostępna zależność.

SCRUM-26 dodaje tabelę `trips`, odczyt zapisanych przejazdów oraz osobną tabelę
`trip_annotations` na cel i opis. Brak notatki ma w API wersję 1; pierwszy zapis
tworzy wersję 2. Każdy zapis wymaga bieżącej wersji, roli admin/editor i poprawnego
Origin. Blokada rekordu Trip w PostgreSQL obejmuje również pierwszy zapis;
drugi edytor otrzymuje 409 zamiast cichego nadpisania. Notatka ma autora i czas
ostatniej zmiany; nie jest pełnym dziennikiem wcześniejszych wersji.

GET `/trips` wymaga pojazdu i zakresu ze strefą czasu (maks. 93 dni), zwraca
przejazdy przecinające `[from, to)`, od najnowszego początku, z UUID jako drugim
kluczem sortowania. Przy braku końca przejazd traktujemy jako punkt początku;
dystans i czas końca mogą być `null`. Geometria pozostaje `null`.
Cel ma maks. 200 znaków w jednym wierszu, opis 2000; tekst jest przycinany,
pusty wpis lub `null` usuwa wartość. PATCH zmienia tylko podane pola, nie dane
źródłowe. Odczyt wymaga sesji i pojazdu z bieżącego konta źródła.

Import historii WEBFLEET pozostaje w SCRUM-24: importer ma aktualizować Trip
według `(vehicle_id, external_uid)`, zachowując UUID oraz TripAnnotation.
Nie może usuwać i odtwarzać przejazdów przy ponownej synchronizacji. Nie ma
publicznego endpointu tworzącego przejazdy ani danych demo w aplikacji.
AlertReceipt przechowuje stan odczytu osobno od Alert. Analityka jawnie podaje
pokrycie okresu i nie liczy brakujących danych jako zera. API zestawień pozostaje
przyszłym zadaniem.

SCRUM-31 implementuje `daily_distance_threshold`, zgodnie z dziennym dystansem
ze Story SCRUM-7. Zastępuje wcześniejszą propozycję `odometer_threshold`, która
dotyczyła wartości licznika. Obserwowany dystans sumuje różnice licznika z
kolejnych pomiarów w tym samym dniu `Europe/Warsaw`, z odstępem do 15 minut.
Pierwszy odczyt, brak danych, cofnięcie licznika, większa luka i odcinek przez
północ nie dopisują zgadywanego dystansu. Pokrycie pozostaje `partial`; pełne
obliczenia z historii przejazdów należą do SCRUM-24/29. To nie jest dzienna
wartość absolutnego licznika ani twierdzenie o pełnym pokryciu dnia.

Reguły obsługują GET/POST/PATCH, dodatni próg 0,1 km, jeden aktywny pojazd lub
całą flotę. Wyłączenie nie usuwa historii. Alert powstaje po przekroczeniu progu
(równość nie wystarcza), tylko ze świeżej obserwacji; ma niezmienny snapshot
dystansu i progu oraz UNIQUE `(rule_id, vehicle_id, event_day)`. Lista alertów
jawnie zwraca polską datę zdarzenia i czas UTC, paginację oraz odczyt aktualnego
użytkownika. Ponowny zapis odczytu jest idempotentny. API rozróżnia reguły
według bieżącego konta źródła; admin/editor edytują, viewer czyta i oznacza
własny odczyt. Pozostałe moduły tego projektu modelu zachowują swój status.

Reset hasła jest osobnym przyrostem po potwierdzeniu SMTP: jednorazowy token
przechowywany jako hash, krótki termin ważności, neutralne odpowiedzi, limit
wysyłki i unieważnienie sesji. Obecna diagnostyka SMTP nie wysyła wiadomości.

## Automatyczna weryfikacja — SCRUM-108

`contracts/api-design.json` pozostaje jedynym źródłem. Jego `$defs` i referencje
odpowiedzi generują typy frontendu oraz walidują realne syntetyczne odpowiedzi API.
`implementation_status` oddziela działające operacje od przyszłych propozycji.
Generator `tools/generate_api_types.py --check` i pytest kontraktu są częścią
Required CI. Status proposed-for-review i wymagany odbiór SCRUM-36 pozostają
w mocy; procedurę aktualizacji/migracji opisuje `docs/qa/SCRUM-108.md`.
