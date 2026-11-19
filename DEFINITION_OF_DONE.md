# Definition of Done — Fleet-Flow

Przyrost jest ukończony dopiero po spełnieniu wszystkich poniższych warunków.
Zielone CI i scalenie części zadania nie zastępują odbioru całej historyjki.

| Warunek | Jedno sprawdzenie / dowód | Kto i kiedy sprawdza |
| --- | --- | --- |
| Kryteria akceptacji historyjki są spełnione, a QA zapisało wynik odbioru. | Lista kryteriów i wynik QA w zgłoszeniu Jira. | **człowiek** — Marcel Głowacki (QA) odbiera wszystkie kryteria na SHA wydania; Jakub Czaja (PO) potwierdza zakres przed Done. |
| Zmiana trafiła do `main` przez PR z zatwierdzeniem innego developera. | PR ma co najmniej jedno aktualne **Approved** i stan **Merged**. | **reguła ochrony** — istniejąca ochrona `main`: PR i approval innego developera; reviewer (Dawid Hnat lub Jakub Nazarewicz) sprawdza ostatnią zmianę. Właściciel potwierdza egzekwowanie reguły. |
| Obowiązkowe CI przeszło dla ostatniej wersji PR. | Wszystkie wymagane kontrole w sekcji Checks są zielone; zatwierdzenie starszego commita nie wystarcza. | **reguła ochrony** — `main`, wymagane `Required CI`, `Backend (3.13)` i `Lint`; **pipeline** — `Required CI` odrzuca failure/skipped zależności. Odczyt API 19.11.2026 potwierdził wszystkie trzy konteksty; dowód SCRUM-140/10320 i docs/COURSE_READINESS.md. |
| Frontend przechodzi testy i budowę. | `npm --prefix frontend test && npm --prefix frontend run build` kończy się kodem `0`. | **pipeline** — `Frontend build`, przy każdym PR i pushu do main: npm test, typecheck i build. |
| Backend przechodzi kontrole kodu i testy bez żywych integracji. | W aktywnym środowisku Pythona: `cd backend && ruff check . && ruff format --check . && pytest` kończy się kodem `0`; CI dostarcza osobną bazę testową. | **pipeline** — `Backend (3.12)`, `Backend (3.13)` i `Lint`: pytest z izolowaną bazą, Ruff check i format --check; bez żywego WEBFLEET/SMTP. |
| Aplikacja działa na wspólnym serwerze deweloperskim. | Widok aplikacji otwiera się pod udokumentowanym adresem serwera; logowanie i dane floty są dostępne przez HTTPS. | **człowiek** — Marcel Głowacki po wdrożeniu sprawdza scenariusz Story przez HTTPS na uprawnionym koncie; Jakub Czaja pokazuje go na Review. |
| Strona serwera wskazuje dokładnie ostatni wdrożony commit `main`. | `git fetch origin && curl -fsS http://57.129.179.53/ \| grep -F "$(git rev-parse --short=7 origin/main)"` znajduje skrót; aktualność potwierdzamy po zakończeniu wdrożenia. | **pipeline** — `Post-deploy smoke`, po udanym deployment: HTTP i HTTPS muszą zawierać SHA tego przebiegu (GITHUB_SHA). **człowiek** — Jakub Czaja po git fetch porównuje także aktualne origin/main do oddania. |
| Wdrożenie ma działający backend i bazę. | Kontrola `/api/health/ready` przez docelowy HTTPS zwraca HTTP `200`. | **pipeline** — `Post-deploy smoke`, po deployment wymaga HTTP 200 z HTTPS /api/health/ready; stan bazy jest częścią readiness. |
| Zmieniony widok działa na komputerze i telefonie. | Wynik sprawdzenia w przeglądarce jest zapisany w PR, razem z obsługą pustego stanu, błędu i klawiatury, jeśli dotyczą zmiany. | **pipeline** — `Critical browser flows`, regresja desktop/mobile; **człowiek** — Marcel Głowacki w odbiorze konkretnej Story sprawdza pełen zakres UI, w tym rzeczywistą mapę, jeśli dotyczy. |
| Repozytorium nie zawiera sekretów ani danych klientów. | Przegląd zakładki Files changed potwierdza brak prywatnych kluczy, haseł, rzeczywistych `.env` i danych floty; sekrety wdrożenia pozostają w GitHub Actions. | **człowiek** — niezależny reviewer (Dawid Hnat lub Jakub Nazarewicz) przed approval sprawdza Files changed; developer sprawdza zakres przed push. Nie jest to deklaracja automatycznego skanera sekretów. |
| Dokumentacja odpowiada dostarczonej wersji. | README zawiera aktualne uruchomienie, adres środowiska, zakres funkcji i link do prototypu dla historyjek sprintu. | **człowiek** — Jakub Czaja przed Review porównuje README i instrukcje ze scalonym przyrostem oraz uzupełnia protokół. |
| Zmiana schematu lub wdrożenia ma sprawdzone odtworzenie. | W PR/Jirze jest wynik próby przywrócenia kopii albo powrotu do wcześniejszego wydania, odpowiednio do zmiany. | **człowiek** — Dawid Hnat przed wdrożeniem zmian schematu/infrastruktury zapisuje próbę restore/rollback; Marcel w odbiorze sprawdza dowód i ograniczenia. |

## Ochrona gałęzi

Właściciel repozytorium wymusza PR, co najmniej jedno zatwierdzenie i zielone
CI również dla administratorów. Bezpośredni push do `main`, force push,
usuwanie gałęzi i pominięcie wymaganych kontroli są zabronione. W prywatnym
repozytorium wymaga to planu obsługującego ochronę gałęzi u jego właściciela.

## Odbiór i status zadania

Developer dołącza PR i wyniki sprawdzeń. Drugi developer wykonuje review,
a QA sprawdza kryteria. PO potwierdza zakres. **Done** ustawiamy po odbiorze,
działającym wdrożeniu oraz zebraniu dowodów. Niespełniony warunek zapisujemy
jako otwartą pracę lub blokadę; nie oznaczamy go jako wykonanego na podstawie
samej instrukcji konfiguracji.

## Bramy jakości Sprintu 2

Odczyt 19.11.2026: `Lint` i `Post-deploy smoke` są na main, a ochrona wymaga
`Required CI`, `Backend (3.13)` i `Lint`. Rozszerzenie już wykonano w SCRUM-140
(dowód właściciela 10320); nie jest kolejną otwartą pracą. Run `44386951054`
dla `cb634da` ma wszystkie 10 jobów SUCCESS, w tym deploy/smoke.
Nie potwierdza to pełnego odbioru Story przez człowieka. `Post-deploy smoke`
nie jest wymaganym checkiem PR, bo dla PR deploy/smoke są pomijane.
[Bieżące dowody i braki oddania](docs/COURSE_READINESS.md).

## SCRUM-101 — bezpieczeństwo przyrostu (ASVS 5.0.0)

Dla zmian w obszarze auth, sesji, uprawnień i danych reviewer i QA wskazują
konkretne wymagania OWASP ASVS **v5.0.0** (identyfikatory `v5.0.0-X.Y.Z`),
wersję/commit testu, środowisko oraz wynik PASS/FAIL/BLOCKED lub umotywowane N/A.
Macierz i aktualne luki: [SCRUM-101](docs/security/SCRUM-101-ASVS-5.0.0-L2.md).
Nie oznaczamy pełnej zgodności ASVS L2 na podstawie wybranych kontroli.
Przed Done: zamknięte błędy krytyczne i wysokie lub jawna decyzja PO dotycząca
ryzyka; niezależny code review/QA; testy regresji, migracji i odtworzenia,
gdy dotyczą zmiany. Dowody nie mogą zawierać sekretów ani danych klientów.