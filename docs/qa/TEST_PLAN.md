# Fleet-Flow — plan QA MVP

**Jira:** SCRUM-37  
**Odpowiedzialny:** Marcel Głowacki  
**Wersja:** 1.0 (projekt do niezależnego review)  
**Stan:** dokumentacja przygotowana, **żadnego testu nie wykonano ani nie oznaczono PASS**  
**Źródła wymagań:** SCRUM-37, SCRUM-5, SCRUM-6, SCRUM-7, SCRUM-16, SCRUM-15, SCRUM-38 oraz wydzielone SCRUM-62 i SCRUM-61; dokumentacja `docs/DATA_MODEL.md`, `docs/MVP_BACKLOG.md`, `docs/WEBFLEET_INTEGRATION.md`, `DEFINITION_OF_DONE.md` i implementacja `main`.

## 1. Cel, rezultat i granice zadania

Celem SCRUM-37 jest **przygotowanie** powtarzalnych scenariuszy QA, macierzy śledzenia kryteriów oraz małego, opisanego zbioru danych syntetycznych z **ręcznie obliczonymi oczekiwanymi wynikami**. Wyniki wykonania są rozliczane później w zadaniach odbiorowych; samo istnienie planu, zielone CI ani scalony PR nie potwierdzają PASS. Plan nie obejmuje automatycznej implementacji testów ani wykonywania żądań do żywego WEBFLEET/SMTP.

Artefakty:

- `docs/qa/TEST_PLAN.md` — zakres, zasady, środowiska, raportowanie, ryzyka i DoD.
- `docs/qa/TEST_CASES.md` — macierz scenariuszy z kryteriami, warunkami, krokami, oczekiwanymi wynikami i miejscem zapisu przyszłych rezultatów.
- `docs/qa/TEST_DATA.json` — syntetyczne dane, przypadki brzegowe i oczekiwane wartości. **To czytelna specyfikacja fixture'ów**, nie plik zgodny 1:1 z dowolnym endpointem ani gotowy seed SQL; adaptery dla testów mogą wymagać odwzorowania pól.

## 2. Kolejność opracowania i powiązania

| Etap | Powiązane zgłoszenia | Zakres |
|---|---|---|
| Sprint 1, najpierw | SCRUM-40 / 38 / 45 / 46 | Szablon, style, układ, zapamiętywanie, klawiatura, telefon, Safari |
| Sprint 1 | SCRUM-23 / 5 / 19–22 / 51 | Lista i mapa, statusy, aktualność, filtry, podgląd, błąd API, cache |
| Sprint 1 | SCRUM-56 / 16 / 44 | Sesja, logowanie, Origin, role, reset z atrapą SMTP |
| Sprint 1 | SCRUM-15 | Idempotencja i odporność synchronizacji |
| Sprint 2 (plan) | SCRUM-6 / 24 / 25 / 28 | Historia i daty, granice okresów, DST, brak danych |
| Sprint 2 (plan) | SCRUM-62 / 26 / 27 / 28 | Adnotacje, ich trwałość, agregacja okresu |
| Sprint 2 (plan) | SCRUM-42 / 52–54 / 63 | Ręczna kartoteka kierowców i przypisania |
| Sprint 3 (plan) | SCRUM-61 / 29 / 30 | Agregacje i porównania |
| Sprint 3 (plan) | SCRUM-7 / 31–33 | Reguły dystansu i alerty |
| Końcowy | SCRUM-17 | Regresja trzech funkcji MVP i demonstracja |

Przyjęta kolejność służy organizacji QA; nie zmienia planu Jiry. SCRUM-57–60 (dokumenty i skany), SCRUM-50 (CSV) i inne rozszerzenia pozostają w dalszym backlogu i nie blokują SCRUM-37. SCRUM-28 dotyka ręcznej kartoteki pojazdu, jednak pełne testy dokumentów należą do SCRUM-60.

## 3. Metody i poziomy testów

- Funkcjonalne i negatywne: zgodność odpowiedzi UI/API z kryteriami, błędne zakresy, brakujące wartości, rozłączne filtry.
- Integracyjne: React ↔ FastAPI ↔ PostgreSQL; stub/mock źródła WEBFLEET, ewentualnie izolowana baza testowa.
- Bezpieczeństwa: brak sesji, wygasanie, role `admin`/`editor`/`viewer`, kontrola Origin, brak ujawniania danych i sekretów.
- Graniczne: półotwarte zakresy dat, DST `Europe/Warsaw`, próg dystansu (`>`), dokładność/niepełność odczytów, paginacja.
- Dostępności i użyteczności: Tab, Enter, Escape, fokus, etykiety, kontrast, reduced motion, mały ekran, Safari.
- Odporności i regresyjne: timeout, 503, stan degraded, odnowienie danych, powtórne synchronizacje bez duplikacji.

## 4. Warunki środowiska i dowodów

Przygotowanie planu nie wymaga instalacji. Późniejszy odbiór lokalny: Windows, Node.js wg `frontend/.nvmrc` (README wskazuje 22.18.0), npm, Python 3.12/3.13, PostgreSQL w Docker Desktop zgodnie z repozytorium; frontend uruchamiany przez Vite, API FastAPI. Weryfikacja: `npm test`, `npm run typecheck`, `npm run build`; backend: `ruff check .`, `ruff format --check .`, `pytest`; są to polecenia **na przyszłość**, nie wyniki obecnego zadania. Safari wymaga macOS/iOS; emulacja widoku mobilnego nie jest równoważna rzeczywistemu Safari. Kontrola `Secure` cookie wymaga działającego HTTPS; test lokalny HTTP nie zastępuje jej.

W każdym raporcie z wykonania zapisz: ID, Jira/AC, środowisko i URL (bez sekretów), datę z TZ, przeglądarkę/urządzenie, SHA sprawdzonej wersji, dane, kroki, oczekiwany oraz rzeczywisty rezultat, **PASS/FAIL/BLOCKED**, dowód (zanonimizowany zrzut/log) i link do błędu. Wszystkie przypadki w tej macierzy są **NOT RUN**. Jeśli brak funkcji, praw dostępu, WebGL, Safari czy środowiska — raportuj BLOCKED z powodem, nie PASS.

## 5. Kontrakt danych i reguły oczekiwań

1. `Vehicle` identyfikuje stabilne `external_uid` w danym `source_account`, ale API zwraca własny UUID. Zmiana nazwy/rejestracji nie tworzy nowego pojazdu.
2. Brak to `null`, **nie** `0`; GPS `(0,0)` jest prawidłowy. Para GPS musi być skończona, mieścić się w zakresie szer. ±90°, dł. ±180°, a jakość `A` pozwala pokazać aktualną pozycję. Jakości `V/L/0` nie wolno udawać świeżego fixa. Nie tworzymy fikcyjnych współrzędnych.
3. `position_at` = czas pomiaru, `received_at` = odbiór. Dla czasu referencyjnego 2026-10-26T12:00:00Z i progu 900 s pozycja starsza od 15 min jest nieaktualna; brak pomiaru to `unknown`, stary to `offline`, świeży `standing_still=false` → `moving`, `true` → `stopped`.
4. Mapa i lista mają wspólne `q` i `status`; lista ma `page` i `page_size`, mapa zwraca **wszystkie** pasujące punkty GPS bez paginacji. Marker na pojazd, **bez klastrów**. Gdy GPS nie ma, pojazd zostaje na liście.
5. Źródłowy snapshot prędkości nie ma potwierdzonej jednostki, więc obecny kontrakt zwraca `speed_kmh=null`. Nie generujemy fikcyjnej prędkości. Przebieg `odometer_km` w km, dystans przejazdów w km; brak wartości jest jawny.
6. Wartości dat używają UTC (ISO 8601), prezentacji w Europe/Warsaw oraz półotwartego przedziału `[from,to)`. Każda granica daty lokalnej wymaga osobnej konwersji przy DST; nie wolno zakładać 24 h dla każdego dnia.
7. `DailyDistance` to **obserwowana dolna granica dystansu**, z dodatnich różnic licznika pomiędzy kolejnymi pomiarami: oba pomiary z tego samego dnia Europe/Warsaw, rosnący czas, odstęp **≤900 sekund**, bez braków i cofania licznika. Nie sumujemy absolutnego licznika i nie imputujemy przerw. Pokrycie: `partial`.
8. Reguła `daily_distance_threshold` ma dodatni próg w km z dokładnością 0,1. Alert dopiero po **ściśle większej** wartości i świeżych obserwacjach; klucz unikatowy `(rule_id, vehicle_id, event_day)` usuwa duplikaty. Wyłączenie reguły nie usuwa historii. Stan przeczytania przechowywany osobno na użytkownika.
9. Błąd zimnego cache: HTTP 503, `SOURCE_UNAVAILABLE`. Poprawnie pusta flota: 200 i `items=[]`. Awaria z zapisanym cache: ostatni poprawny wynik ze statusem `degraded`, nigdy udawany bieżący odczyt.
10. Kierowców wprowadza się **ręcznie**. Synchronizacja WEBFLEET nie tworzy ich ani nie nadpisuje przypisań lub lokalnych opisów. Konflikty zmian wersji adnotacji to 409 zgodnie z proponowanym kontraktem (implementacja przyszła).

## 6. Kryteria kompletności planu (SCRUM-37)

- Każde kryterium SCRUM-5, 6 i 7 jest powiązane z co najmniej jednym scenariuszem; wydzielone SCRUM-62 i 61 mają osobne wiersze.
- Scenariusze zawierają: kroki, wejście, oczekiwany wynik, miejsce zapisu późniejszego wyniku i błędów.
- Uwzględniono pustą flotę, brak GPS, `(0,0)`, wartości `null`, filtr bez wyników, stale/degraded, timeout i awarię.
- Uwzględniono granice dat i DST, izolację pojazdów, trwałość celu/opisu mimo ponownej synchronizacji oraz utratę połączenia.
- Oczekiwane agregaty i progi policzone ręcznie; uwzględniono poniżej/równo/powyżej, brak danych, duplikaty i wyłączenie reguły.
- Uwzględniono brak sesji, wygasłą sesję i odczyt alertu po ponownym zalogowaniu.
- Dane są fikcyjne, jawnie opisane i bez sekretów/realnych lokalizacji klientów.
- Przed zakończeniem zadania: osobna gałąź, PR, niezależne review i aktualizacja stosownego zgłoszenia przez właściciela. **Nie wykonano tych działań w ramach przygotowania plików.**

## 7. Ryzyka, ograniczenia i decyzje do potwierdzenia

- W przyszłych Sprintach historia i część UI analityki mogą być niewdrożone — przypadki pozostają NOT RUN/BLOCKED, nie są zaliczone.
- Syntetyczny JSON to fixture specyfikacji; dopasowanie do fizycznej bazy i stubów/API trzeba wykonać przy faktycznym uruchamianiu testów.
- Kształt części przyszłych endpointów z `contracts/api-design.json` ma status **proposed-for-review** — przed testem implementacyjnym należy ponownie potwierdzić kontrakt.
- Żywe WEBFLEET i realna dostawa SMTP wymagają osobnego wyraźnego uzgodnienia; brak takich testów trzeba wskazać w raporcie.
- Pełny odbiór dokumentów i załączników pojazdu jest osobno w SCRUM-60; kierowcy w SCRUM-54.
- Wszystkie przypadki zostają niewykonane do czasu prac odbiorowych. Wypełnienie `TEST_PLAN` nie jest końcem SCRUM-23/40/56 ani odbiorem całego MVP.

## 8. Odniesienia

- Jira: `https://fleet-flow.atlassian.net/browse/SCRUM-37`; SCRUM-5/6/7/15/16/23/28/33/40/56/61/62.
- GitHub: `docs/DATA_MODEL.md`, `docs/MVP_BACKLOG.md`, `docs/WEBFLEET_INTEGRATION.md`, `frontend/README.md`, `backend/README.md`, `DEFINITION_OF_DONE.md`, `contracts/api-design.json`.
- Kod źródłowy: `backend/app/modules/analytics/service.py`, `backend/app/modules/analytics/router.py`, `backend/app/modules/fleet/sync.py` (stan `main` sprawdzony przy przygotowaniu dokumentów).
