# Definition of Done — Fleet-Flow

Przyrost jest ukończony dopiero po spełnieniu wszystkich poniższych warunków.
Zielone CI i scalenie części zadania nie zastępują odbioru całej historyjki.

| Warunek | Jedno sprawdzenie / dowód |
| --- | --- |
| Kryteria akceptacji historyjki są spełnione, a QA zapisało wynik odbioru. | Lista kryteriów i wynik QA w zgłoszeniu Jira. |
| Zmiana trafiła do `main` przez PR z zatwierdzeniem innego developera. | PR ma co najmniej jedno aktualne **Approved** i stan **Merged**. |
| Obowiązkowe CI przeszło dla ostatniej wersji PR. | Wszystkie wymagane kontrole w sekcji Checks są zielone; zatwierdzenie starszego commita nie wystarcza. |
| Frontend przechodzi testy i budowę. | `npm --prefix frontend test && npm --prefix frontend run build` kończy się kodem `0`. |
| Backend przechodzi kontrole kodu i testy bez żywych integracji. | W aktywnym środowisku Pythona: `cd backend && ruff check . && ruff format --check . && pytest` kończy się kodem `0`; CI dostarcza osobną bazę testową. |
| Aplikacja działa na wspólnym serwerze deweloperskim. | Widok aplikacji otwiera się pod udokumentowanym adresem serwera; logowanie i dane floty są dostępne przez HTTPS. |
| Strona serwera wskazuje dokładnie ostatni wdrożony commit `main`. | `git fetch origin && curl -fsS http://57.129.179.53/ \| grep -F "$(git rev-parse --short=7 origin/main)"` znajduje skrót; aktualność potwierdzamy po zakończeniu wdrożenia. |
| Wdrożenie ma działający backend i bazę. | Kontrola `/api/health/ready` przez docelowy HTTPS zwraca HTTP `200`. |
| Zmieniony widok działa na komputerze i telefonie. | Wynik sprawdzenia w przeglądarce jest zapisany w PR, razem z obsługą pustego stanu, błędu i klawiatury, jeśli dotyczą zmiany. |
| Repozytorium nie zawiera sekretów ani danych klientów. | Przegląd zakładki Files changed potwierdza brak prywatnych kluczy, haseł, rzeczywistych `.env` i danych floty; sekrety wdrożenia pozostają w GitHub Actions. |
| Dokumentacja odpowiada dostarczonej wersji. | README zawiera aktualne uruchomienie, adres środowiska, zakres funkcji i link do prototypu dla historyjek sprintu. |
| Zmiana schematu lub wdrożenia ma sprawdzone odtworzenie. | W PR/Jirze jest wynik próby przywrócenia kopii albo powrotu do wcześniejszego wydania, odpowiednio do zmiany. |

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
