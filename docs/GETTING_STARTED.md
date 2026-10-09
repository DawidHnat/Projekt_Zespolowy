# Rozpoczęcie pracy

Podstawa aplikacji jest w `main`: React + TypeScript, FastAPI, PostgreSQL,
logowanie, lista i mapa floty oraz personalizacja widoków. Puste moduły czekają
na swoje zadania implementacji. Pracę lokalną można rozpocząć niezależnie od VPS.

## Każdy członek zespołu

1. Klonuje `https://github.com/DawidHnat/Projekt_Zespolowy` na własny komputer.
   Jeśli już pracuje w repozytorium, zapisuje rozpoczęte zmiany na swojej gałęzi,
   następnie aktualizuje podstawę:

   ```bash
   git fetch origin
   git switch main
   git pull --ff-only
   ```

2. Ustawia własne `git config user.name` i `git config user.email` zgodne z kontem
   GitHub. Sprawdza je przed pierwszym commitem.
3. Przygotowuje Node.js wskazany w `frontend/.nvmrc`, Python 3.12 lub 3.13
   i lokalny Docker do PostgreSQL.
4. Uruchamia bazę, migracje, tworzy własne konto aplikacji i uruchamia API według
   [backend/README.md](../backend/README.md). Uzupełnia własny lokalny `.env`
   zgodnie z `.env.example`; istniejącego `.env` nie nadpisuje.
5. W drugim terminalu wykonuje `npm ci` i `npm run dev` w `frontend/`, według
   [frontend/README.md](../frontend/README.md). Loguje się swoim kontem aplikacji.
   Dane WEBFLEET pobiera backend; publiczny token Mapbox jest potrzebny do mapy.
6. Czyta przypisane zadanie oraz kryteria akceptacji w Jirze i tworzy gałąź
   zadania z aktualnego `main`, zgodnie z [CONTRIBUTING](../CONTRIBUTING.md).
   Zmiana trafia do osobnego PR z opisem i wynikami sprawdzeń.
7. Dostarcza Dawidowi własny publiczny klucz SSH `.pub` według
   [instrukcji VPS](../infra/vps/README.md), a po dodaniu klucza zapisuje własny
   test SSH z kodem wyjścia w [SCRUM-12](https://fleet-flow.atlassian.net/browse/SCRUM-12).
   Klucza prywatnego nie przekazuje.

## Kolejne prace

Aktualne przypisania i statusy są w [Jirze](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog).
[Podział pracy](TASKS.md) opisuje scalony zakres oraz następne przyrosty:
ręczną kartotekę pojazdu, dokumenty, historię przejazdów i QA.

Frontend i backend pracują według [modelu danych](DATA_MODEL.md)
oraz [kontraktu API](../contracts/api-design.json). Nowe pola uzgadniamy w zadaniu
przed równoległą implementacją. Kierowcy są wpisywani ręcznie.

Weryfikacja frontendu: `npm test` i `npm run build` w `frontend/` oraz zachowanie
w przeglądarce. Weryfikacja backendu: `ruff check .`, `ruff format --check .`
i `pytest` w `backend/`. Testy działają bez prawdziwych danych i sekretów;
szczegóły osobnej bazy testowej opisuje instrukcja backendu.

Scalenie PR nie oznacza automatycznie odbioru całej Story. Pozostałe kryteria
i QA nadal realizujemy w Jirze. Przegląd przez płatne API AI oraz stałe
automatyczne scalanie wymagają osobnej decyzji i konfiguracji.
