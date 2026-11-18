# Definition of Done — Fleet-Flow

Od 18.11.2026 (decyzja PO, SCRUM-151) zadanie implementacyjne jest **Gotowe**,
gdy cały jego zakres został sprawdzony, zatwierdzony i scalony do `main`.
QA konkretnej zmiany odbywa się przed merge. Regresja modułu i odbiór wydania
mają osobne zadania oraz wyniki; nie wymagają ponownego ręcznego potwierdzania
tego samego PR tylko do zmiany jego statusu.

## Ukończenie zadania implementacyjnego

| Warunek | Jedno sprawdzenie / dowód | Kto i kiedy sprawdza |
| --- | --- | --- |
| Cały zakres zadania jest spełniony i sprawdzony przed merge. | Kryteria, wynik, osoba, SHA i środowisko w PR lub podlinkowanym zgłoszeniu; uzasadnione N/A dla zmiany bez zachowania aplikacji. | **człowiek** — Marcel Głowacki (QA) lub inna osoba niż autor sprawdza konkretną zmianę; reviewer potwierdza zakres i wyniki przed Approved. |
| Zmiana trafiła do `main` przez PR z zatwierdzeniem innego developera. | PR ma co najmniej jedno aktualne **Approved** i stan **Merged**. | **reguła ochrony** — istniejąca ochrona `main`: PR i approval innego developera; reviewer (Dawid Hnat lub Jakub Nazarewicz) sprawdza ostatnią zmianę. Właściciel potwierdza egzekwowanie reguły. |
| Obowiązkowe CI przeszło dla ostatniej wersji PR. | Wszystkie wymagane kontrole w sekcji Checks są zielone; zatwierdzenie starszego commita nie wystarcza. | **reguła ochrony** — `main`, wymagany `Required CI`; **pipeline** — `Required CI` odrzuca failure/skipped zależności. Planowane dodatkowe wymagane checki: `Backend (3.13)` i `Lint`; ich aktywację potwierdza odczyt API, nie ten dokument. |
| Zmieniony frontend przechodzi testy i budowę. | `npm --prefix frontend test && npm --prefix frontend run build` kończy się kodem `0`. | **pipeline** — `Frontend build`, przy każdym PR i pushu do main: npm test, typecheck i build. |
| Zmieniony backend przechodzi kontrole kodu i testy bez żywych integracji. | W aktywnym środowisku Pythona: `cd backend && ruff check . && ruff format --check . && pytest` kończy się kodem `0`; CI dostarcza osobną bazę testową. | **pipeline** — `Backend (3.12)`, `Backend (3.13)` i `Lint`: pytest z izolowaną bazą, Ruff check i format --check; bez żywego WEBFLEET/SMTP. |
| Zmieniony widok działa na komputerze i telefonie. | Wynik sprawdzenia w przeglądarce jest zapisany w PR, razem z obsługą pustego stanu, błędu i klawiatury, jeśli dotyczą zmiany. | **pipeline** — `Critical browser flows`, regresja desktop/mobile; **człowiek** — QA sprawdza zakres zmienionego widoku przed merge, w tym mapę, jeśli dotyczy. |
| Repozytorium nie zawiera sekretów ani danych klientów. | Przegląd zakładki Files changed potwierdza brak prywatnych kluczy, haseł, rzeczywistych `.env` i danych floty; sekrety wdrożenia pozostają w GitHub Actions. | **człowiek** — niezależny reviewer (Dawid Hnat lub Jakub Nazarewicz) przed approval sprawdza Files changed; developer sprawdza zakres przed push. Nie jest to deklaracja automatycznego skanera sekretów. |
| Dokumentacja odpowiada dostarczonej zmianie. | Zmienione instrukcje, zakres funkcji i kontrakty są aktualne. | **człowiek** — autor aktualizuje dokumentację, reviewer sprawdza ją razem z PR. |
| Zmiana schematu lub wdrożenia ma sprawdzone odtworzenie. | W PR/Jirze jest wynik próby przywrócenia kopii albo powrotu do wcześniejszego wydania, odpowiednio do zmiany. | **człowiek** — Dawid Hnat przed wdrożeniem zmian schematu/infrastruktury zapisuje próbę restore/rollback; Marcel w odbiorze sprawdza dowód i ograniczenia. |

## Ochrona gałęzi

Właściciel repozytorium wymusza PR, co najmniej jedno zatwierdzenie i zielone
CI również dla administratorów. Bezpośredni push do `main`, force push,
usuwanie gałęzi i pominięcie wymaganych kontroli są zabronione. W prywatnym
repozytorium wymaga to planu obsługującego ochronę gałęzi u jego właściciela.

## Odbiór i status zadania

Developer dołącza PR i wyniki sprawdzeń. Drugi developer wykonuje review,
a QA sprawdza kryteria konkretnej zmiany przed merge. Scalenie kompletnego PR
do `main` po aktualnym Approved i zielonym wymaganym CI kończy zadanie.
Reguła Jira **SCRUM: merge PR do main → Gotowe** odwzorowuje tę decyzję dla
klucza w gałęzi. Jej stan połączenia i testu jest w
[SCRUM-151](https://fleet-flow.atlassian.net/browse/SCRUM-151).

Automatyzacja dotyczy zadań i podzadań, z pominięciem Story i epików.
Nie zamyka innych zgłoszeń tylko dlatego, że są wspomniane w opisie PR.
Przed merge częściowego przyrostu wydzielamy jego własne zadanie i klucz.
Dużą Story zamykamy po spełnieniu jej pełnego zakresu; epik po zakresie epiku.
Merge do gałęzi zależności wymaga jeszcze dostarczenia do `main`.

Zadania bez kodu, w tym QA, zamykamy po dostarczeniu wyniku zgodnego z ich
kryteriami. Regresja całego modułu ma osobny status i nie powoduje ponownego
oczekiwania implementacji na ten sam odbiór. Błąd wykryty później otrzymuje
własne zgłoszenie, priorytet i PR poprawki; jego naprawa kończy się po retestach.

## Osobne QA i odbiór wydania

**Testowanie** służy zadaniom QA, np. SCRUM-23 (flota), SCRUM-56 (logowanie),
SCRUM-63 (historia/ewidencja) i SCRUM-17 (regresja MVP). Wynik zawiera zakres,
scenariusze, PASS/FAIL/BLOCKED, SHA i środowisko. Osoba wykonująca QA nie jest
autorem sprawdzanej zmiany. Korzystamy z istniejącego zadania, jeśli obejmuje
potrzebny zakres, i dopisujemy znalezione błędy oraz retesty.

Wdrożenie i regresja pozostają częścią odbioru modułu/wydania. Ich wynik
nie jest automatycznie potwierdzany przez status Gotowe zadania kodu.

| Warunek wydania | Dowód i odpowiedzialność |
| --- | --- |
| Aplikacja działa przez HTTPS na wspólnym serwerze. | QA sprawdza uzgodnione scenariusze modułu na uprawnionym koncie i zapisuje wynik; PO prezentuje zakres na Review. |
| Serwer udostępnia właściwy commit main. | `Post-deploy smoke` sprawdza SHA przebiegu w HTTP i HTTPS; PO przed oddaniem porównuje wdrożenie z aktualnym `origin/main`. |
| Backend i baza są gotowe. | `Post-deploy smoke` wymaga HTTP 200 z HTTPS `/api/health/ready`. |
| Regresja modułu ma jawny wynik i błędy. | QA zapisuje wynik w osobnym zadaniu; brakujący scenariusz pozostaje otwarty lub BLOCKED. |
| Awaria deployment/smoke ma obsługę. | Właściciel wdrożenia prowadzi zadanie naprawcze lub rollback i ponownie sprawdza wynik. |

Wymagania oddania kursowego, protokoły Review i wcześniejsze wyniki zachowują
własne kryteria. Zmiana statusów nie dopisuje historycznych PASS ani nie
potwierdza zaległych odbiorów.

## Bramy jakości Sprintu 2

Stan 18.11.2026: `Lint` i `Post-deploy smoke` są na main po PR #76
(SCRUM-127). Run `44176327656` dla `132fefc` potwierdza sukces testów,
lintu, wdrożenia i smoke; nie potwierdza pełnego odbioru Story przez człowieka.
Zachowujemy nazwy wszystkich dotychczasowych jobów. `Post-deploy smoke`
nie jest wymaganym checkiem PR: dla PR deployment i smoke są pomijane.
Ochrona nadal wymaga tylko `Required CI`. Właściciel dodaje osobno wymagane
`Backend (3.13)` i `Lint` w SCRUM-140, zachowując dotychczasowe zabezpieczenia.
[Bieżące dowody i braki oddania](docs/COURSE_READINESS.md).

## SCRUM-101 — bezpieczeństwo przyrostu (ASVS 5.0.0)

Dla zmian w obszarze auth, sesji, uprawnień i danych reviewer i QA wskazują
konkretne wymagania OWASP ASVS **v5.0.0** (identyfikatory `v5.0.0-X.Y.Z`),
wersję/commit testu, środowisko oraz wynik PASS/FAIL/BLOCKED lub umotywowane N/A.
Macierz i aktualne luki: [SCRUM-101](docs/security/SCRUM-101-ASVS-5.0.0-L2.md).
Nie oznaczamy pełnej zgodności ASVS L2 na podstawie wybranych kontroli.
Przed merge: zamknięte błędy krytyczne i wysokie dotyczące zmiany lub jawna
decyzja PO dotycząca ryzyka; niezależny code review/QA; regresja zmienianych
kontroli oraz testy migracji i odtworzenia, gdy dotyczą zmiany. Przekrojowa
regresja bezpieczeństwa ma osobne zadanie QA. Dowody nie mogą zawierać
sekretów ani danych klientów.
