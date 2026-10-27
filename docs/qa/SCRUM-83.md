# SCRUM-83 - krytyczne przepływy w przeglądarce

Playwright uruchamia rzeczywisty React, FastAPI, migracje i dedykowany PostgreSQL.
Przyrost zależy od PR #30 / SCRUM-26, ponieważ sprawdza trwały zapis celu i opisu
istniejącego przejazdu. Nie dodaje rekordów testowych do aplikacji ani deploymentu.

## Uruchomienie lokalne

Wymagane: Node zgodny z `.nvmrc`, Python 3.12/3.13 z
`backend/requirements-dev.txt`, PostgreSQL 17 i developerskie zależności npm.
W odizolowanym lokalnym PostgreSQL utwórz pustą bazę **fleet_flow_test_e2e**
oraz konto testowe z prawem migracji. Nie używaj bazy aplikacji.
`npm ci` i `npx playwright install chromium` przygotowują frontend/przeglądarkę.

W `frontend/`, po ustawieniu prywatnie E2E_DATABASE_URL do tej bazy:

```bash
npm run test:e2e
```

Opcjonalnie `E2E_PYTHON` wskazuje interpreter w venv. Serwery testowe używają
127.0.0.1:54173 i 127.0.0.1:58000. Zajęty port kończy test błędem - nie przejmujemy
istniejącego serwera. Backend fixture wymaga `FLEET_FLOW_E2E=true`, dokładnej nazwy
lokalnej bazy i odrzuca obecność innych użytkowników. Tego trybu nie wywołuje
produktowe wejście `app.main:create_app`. Synchronizacja jest wyłączona, token
mapy pusty, zewnętrzny ruch przeglądarki blokowany. Nie odczytujemy kont klientów.

Fixture zapisuje wyłącznie dwa syntetyczne konta, jeden pojazd z pozycją (0,0)
i jeden przejazd. Po testach usuń dedykowaną bazę lub jej jednorazowy kontener;
nie ma automatycznego czyszczenia cudzych baz. Serwery i konteksty przeglądarki
sprząta Playwright. Nie uruchamiaj równolegle dwóch zestawów na tej samej bazie.
Przed każdym przypadkiem fixture usuwa sesje i liczniki prób wyłącznie z tej
dedykowanej bazy. Osobny scenariusz potwierdza działanie prawdziwego limitera.

## Zakres i granice wyniku

Każdy scenariusz działa w Chromium na desktopie i ekranie 390 px:

- 401 bez sesji, login, lista, filtry (wynik i brak wyniku), API GeoJSON oraz
  widok mapy z jawnym fallbackiem bez tokenu; szczegóły pojazdu.
- Zapis celu/opisu przez edytora i ponowny odczyt po przeładowaniu z prawdziwej DB.
- Viewer: UI tylko do odczytu i 403 po bezpośredniej próbie PATCH.
- Awaria źródła ze starym cache: dane nadal widoczne i jawny komunikat degradacji.
- Awaria bez cache: 503 i komunikat oczekiwania, bez udawanej pustej floty.
- Unieważniona sesja i logout: powrót do logowania oraz ponowne 401 z API.
- Równoległy zapis: 409, zachowany szkic i porównanie aktualnej wersji.
- Limit 10 prób logowania: blokada kolejnej próby i komunikat w przeglądarce.

Testy nie potwierdzają renderowania mapy Mapbox/WebGL ani działania żywej integracji,
SMTP, fizycznego telefonu lub pełnego planu 57 scenariuszy. Nie zastępują
niezależnego QA z wynikiem na konkretnym SHA.

## CI

Job `Critical browser flows` działa dla każdego PR i jest częścią `Required CI`.
Baza jest osobnym serwisem z syntetycznymi danymi. Raport JUnit i screenshoty
błędu trafiają do artefaktu na 7 dni. Trace, film i nagrywanie requestów są
wyłączone. Artefakty zawierają tylko fixture; nie uruchamiaj tego zestawu przeciw
produkcyjnemu serwerowi. Brak retries ujawnia flaky test zamiast ukrywać błąd.

Odbiór: URL runu, SHA, projekty desktop/mobile, liczba PASS/FAIL, dowody regresji,
niezależny reviewer. Wyniku E2E nie przenosimy automatycznie na całą Story.
