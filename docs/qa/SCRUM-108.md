# SCRUM-108 — automatyczna kontrola React–FastAPI

Jedynym źródłem pozostaje `contracts/api-design.json` wskazany w SCRUM-36.
Dodano do **tego samego pliku** definicje JSON Schema 2020-12 i referencje
odpowiedzi operacji. Nie utworzono konkurencyjnego OpenAPI ani drugiej specyfikacji.
Status kontraktu pozostaje proposed-for-review, a schematów draft-for-SCRUM-36-review;
finalny odbiór wymaga zatwierdzenia SCRUM-36. Harness może zostać oceniony wcześniej.

`implementation_status` odróżnia17 działających operacji auth/fleet/trips/analytics
od4 przyszłych (drivers i analytics/summary). Kod/testy nie wymuszają implementacji
pustych modułów. Działające trips oznaczają zapisane przejazdy i adnotacje, nie
uruchomiony import historii. Root delivery/implementation_note zachowują ten zakres.

## Kierunek i kontrola

1. Zespół uzgadnia zmianę w jednym kontrakcie: $defs, status operacji i przykłady.
2. `python3 tools/generate_api_types.py` generuje TypeScript w
   `frontend/src/shared/api/generated/contracts.ts`. Ręcznie nie edytuj wyniku.
3. AuthProvider, DTO floty i adnotacji korzystają z tych typów. Opcjonalne pola
   prezentacyjne make/model/address pozostają jawnym rozszerzeniem UI do dalszego
   przyrostu; nie są deklaracją pola istniejącego backendu.
4. Backend `tests/test_contracts.py` waliduje rzeczywiste syntetyczne odpowiedzi
   wszystkich17 operacji i przykłady przy użyciu tych samych definicji.
5. Frontend CI wykonuje generator --check i typecheck/build, backend CI wykonuje
   pytest kontraktu. Oba joby są obowiązkowymi zależnościami Required CI.

Schemat sprawdza wymagane/null/optional, liczby/booleany/enumy/UUID, UTC daty,
GPS w zakresie i kolejność GeoJSON, paginację, jednostki km/s i kody błędów.
Testy realnego API obejmują401/403 (rola i Origin)/404/409/422/503 oraz reset400;
sprawdzają m.in. (0,0), brak GPS, przebieg1234.5km, dystans12.5km/czas600s,
autorstwo i wersję adnotacji oraz read/null receipt. Speed pozostaje null zgodnie
z niepotwierdzonymi jednostkami snapshotu SCRUM-14. Sam schema typów nie dowodzi
całej logiki domenowej — pozostają istniejące testy sync/trips/alertów i QA.

Zdalne pobieranie schematów jest wyłączone. Żadnego WEBFLEET/SMTP; test blokuje
funkcję SMTP i sprawdza brak prób. SQLite aplikacji jest efemeryczny, a pełny zestaw
korzysta wyłącznie z osobnego PostgreSQL testowego do testów integracyjnych.
Kontrakt trafia też do obrazu i archiwum wdrożenia, aby zachować spójność plików.

## Zgodne rozszerzenia i migracja

Dodatkowe opcjonalne pola odpowiedzi są dozwolone. Test potwierdza przyjęcie
optional_future_field. Zmiana nazwy, typu lub usunięcie wymaganego pola blokują,
podobnie jak niepoprawny UUID, data bez UTC, tekst zamiast liczby/boolean i GPS
poza zakresem. Dodanie opcjonalnego pola do samej specyfikacji wymaga regeneracji
typów w tym samym PR; celowy check świeżości nie jest zakazem zgodnego rozszerzenia.

Dla breaking change uzgodnij migrację w SCRUM-36: dodaj nowe pole/operację wraz
z okresem kompatybilności albo nową wersję API; najpierw dostarcz kompatybilny
backend i konsumentów, dopiero potem usuń stare pole po odbiorze użytkowników.
Nie „naprawiaj” czerwonego testu kasowaniem required albo pomijaniem walidacji.
Przestawienie proposed→implemented wymaga przypadków realnego API i regeneracji;
zbiór pokrytych operacji jest sprawdzany, więc nowy endpoint nie zostaje bez testu.

## Wyniki i odbiór

Weryfikacja developerska 28.10.2026:20 testów kontraktu PASS, pełny backend144
pytest PASS z PostgreSQL i migracjami, Ruff/format PASS, frontend47 npm test i build
PASS, generator --check PASS. Ten sam pełny zestaw144 pytest przeszedł również
wewnątrz jednorazowego obrazu Python3.13 Alpine z osobną bazą. Przeglądarkowy smoke
login/flota/mapa/adnotacja/logout przeszedł2/2 na desktop/mobile. pip-audit po
nowej zależności: zero znanych podatności. Obraz zawiera jeden kontrakt i importuje
aplikację. Kontrolny niescalany przykład jest zapisywany przy SHA PR.

Niezależny QA zapisuje wersję0.1, schema_status, SHA, środowisko i wynik.
Finalny odbiór pozostaje zablokowany zatwierdzeniem SCRUM-36 oraz review/QA;
żadnego domniemanego akceptowania specyfikacji przez samo zielone CI.
