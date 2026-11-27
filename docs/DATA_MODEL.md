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
| AccountPreference | `(User, module)`, wersja, JSON, czas zmiany | układ i widoki danego użytkownika (SCRUM-91) |
| SyncState | klucz konta źródła, próba/sukces, bezpieczny kod błędu | koordynacja odpytywania i stan pamięci podręcznej |

UID dostawcy pozostaje wewnętrzny; API pokazuje UUID aplikacji. Zmiana nazwy,
numeru lub rejestracji nie tworzy nowego pojazdu. Usunięcie pojazdu ze źródła
dezaktywuje rekord po kompletnym odczycie, bez usuwania historii i ręcznych pól.
Nie importujemy nazw, loginów, kontaktów ani innych pól kierowców ze źródła.
User oznacza osobę korzystającą z aplikacji, Driver — ręcznie opisany wpis floty.

## Kartoteka kierowców i przypisania — SCRUM-52

- Kierowca tworzy i edytuje wyłącznie operator w kartotece Fleet-Flow.
  Synchronizacja WEBFLEET nie tworzy, nie nadpisuje i nie dezaktywuje
  `Driver` ani ręcznych przypisań.
- Jeden kierowca może być przypisany do wielu pojazdów, a jeden pojazd może
  mieć wielu bieżących kierowców. Relacje są osobnymi rekordami
  `DriverAssignment`; nie wybiera się ani nie utrzymuje globalnego kierowcy
  głównego.
- `DriverAssignment` ma pola kontraktu `started_at` i `ended_at` (znacznik czasu
  UTC) oraz `active`. Bieżące przypisanie ma `active=true` i `ended_at=null`;
  zakończenie ustawia `ended_at` na czas zamknięcia. Okres jest półotwarty
  `[started_at, ended_at)`. Przypisania przeniesione ze starego wskaźnika mają
  `started_at=null` (nieznany początek, `start_known=false`), bez zgadywania historii.
- Para kierowca–pojazd może mieć tylko jedno aktywne przypisanie (unikalny
  indeks częściowy); ponowne przypisanie po zakończeniu tworzy nowy rekord.
  Zamknięcie i dezaktywacja blokują wiersze (`SELECT … FOR UPDATE`), więc
  równoczesna zmiana kończy się konfliktem 409 zamiast podwójnego zamknięcia.
- Zmiana bieżącego przypisania nie zmienia kierowcy zapisanego przy dawnych
  przejazdach ani nie usuwa historii relacji. Kierowca przejazdu w ewidencji
  jest utrwalany osobno, w adnotacji przejazdu (SCRUM-70), a nie wyliczany
  z bieżących przypisań.
- Wyłączenie kierowcy zamyka jego bieżące przypisania. Zachowuje UUID rekordu,
  dane ręczne i dane historyczne; ponowna aktywacja nie przywraca relacji
  automatycznie.
- Formularz i API nie zbierają numerów PESEL ani dokumentów. Wymagane jest
  imię i nazwisko/nazwa oraz wewnętrzne pole `identifier`, unikalne w koncie,
  ale edytowalne (`DriverPatch`). Historię i relacje wiąże wyłącznie stały
  UUID rekordu, nigdy `identifier`. Opcjonalny kontakt i kategorie prawa jazdy
  podlegają walidacji po wpisaniu.
- Kontrola zgodności kategorii kierowcy z wymaganiami pojazdu nie jest
  wykonywana automatycznie w tym przyroście. Brak danych oznacza
  `Do sprawdzenia`, a nie zgodność; osobną blokadę opisuje SCRUM-70.
- Import historii przejazdów nie wybiera kierowcy z bieżących przypisań. Gdy
  pojazd ma kilku kierowców, kierowcę przejazdu wskazuje operator w ewidencji.
- Testy akceptacyjne: [API i model](../backend/tests/test_manual_drivers.py),
  [PostgreSQL](../backend/tests/test_manual_drivers_postgres.py),
  [przeglądarka](../frontend/e2e/drivers.spec.ts).

## Jednostki, czas i jakość

- GPS: stopnie WGS84; GeoJSON ma kolejność `[longitude, latitude]`. Para musi być
  kompletna, skończona i w zakresie. Jakość `A` pozwala pokazać pozycję; inne
  jakości nie są traktowane jako aktualny punkt. `(0, 0)` nie jest brakiem danych.
- Licznik: km, maksymalnie jeden znak dziesiętny; snapshot WEBFLEET ma jednostkę
  100 m. Dystans przejazdu: km z konwersji metrów; czas trwania: sekundy.
- Prędkość: `speed_kmh` w km/h (0–300) lub `null`. Jednostkę snapshotu
  potwierdzono [kontrolnym porównaniem tego samego zdarzenia](qa/SCRUM-14-speed-unit.md)
  18.11.2026; wartość źródłowa nie wymaga przeliczenia. Brak, stary/przyszły
  pomiar, błąd źródła lub niepotwierdzony GPS dają `null`; zero pozostaje zerem.
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
`total` po filtrach. Lista Pojazdów obsługuje sortowanie przed paginacją:
`name-asc`, `name-desc`, `status`, `odometer-asc` i `odometer-desc`, ze stabilnym
rozstrzygnięciem po nazwie/UUID. `q` szuka
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

Preferencje konta mają osobne moduły `dashboard` i `vehicles` pod
`/api/v1/preferences/{module}`. PUT wymaga odczytanej wersji i atomowo odrzuca
przestarzały zapis kodem 409. Migracja istniejącego stanu przeglądarki wymaga
jawnego wyboru i działa tylko wtedy, gdy konto nie ma jeszcze preferencji.

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

SCRUM-32 dodaje opcjonalne nazwy/rejestracje pojazdów do stron list alertów
i reguł (JOIN bez N+1). Nie zmienia to źródłowego dystansu, dnia ani progu
zachowanego alertu. Odczyt pozostaje relacją AlertReceipt per użytkownik.

## Ręczni kierowcy — SCRUM-52

Driver ma osobne imię/nazwisko, identyfikator, opcjonalny kontakt, aktywność
oraz wersję. DriverCategory przechowuje ID wersjonowanego słownika (bez oceny
uprawnień). DriverAssignment jest historią wiele:wiele z aktywnością, czasami
początku/końca i recorded_at; nieznana stara data pozostaje null. Nowa relacja
zaczyna się w czasie zapisu, zamknięcie zachowuje wiersz. Profile i relacje
nie są danymi WEBFLEET. Vehicle.driver_id jest projekcją zgodności dla
jednego przypisania; przy wielu API zwraca driver=null, liczbę i podgląd osób.
[API, migracja starych rekordów, ograniczenia i rollback](qa/SCRUM-52.md).
