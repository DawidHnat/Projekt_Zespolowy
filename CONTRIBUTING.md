# Wspólna praca nad Fleet-Flow

Jedno zadanie z Jiry to jedna gałąź i jeden PR. Mały PR łatwiej zrozumieć,
przetestować i połączyć z pracą pozostałych osób. Nie czekamy z pushem do końca
zadania: regularnie wysyłamy działające fragmenty, a niedokończony PR oznaczamy
jako **draft**.

## Od zadania do PR

1. Wybierz zadanie w [backlogu SCRUM](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog),
   przypisz je sobie i ustaw **In Progress**. Dopisz kryteria akceptacji oraz
   ewentualne zależności przed rozpoczęciem większej zmiany.
2. Pobierz aktualną gałąź główną i utwórz gałąź z rzeczywistym kluczem zadania:

   ```bash
   git switch main
   git pull --ff-only
   git switch -c feat/SCRUM-123-filtrowanie-pojazdow
   ```

   Dostępne prefiksy: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.
   Opis zapisuj małymi literami, bez spacji i polskich znaków.
3. Wprowadź zmianę w jej module. Gdy zmieniasz API, najpierw uzgodnij kontrakt
   z osobą pracującą nad frontendem; gdy zmieniasz schemat bazy, dodaj migrację.
4. Uruchom kontrole dotyczące zmiany, sprawdź diff i wyślij commit:

   ```bash
   git diff
   git status --short
   git add frontend/src/features/fleet
   git commit -m "SCRUM-123: dodaj filtrowanie pojazdow"
   git push -u origin feat/SCRUM-123-filtrowanie-pojazdow
   ```

   Dodawaj konkretne pliki lub katalogi. Nigdy nie commituj `.env`, kluczy,
   haseł ani eksportów danych klientów.
5. Po zakończeniu CI GitHub utworzy PR automatycznie, również kiedy testy
   się nie powiodą. Uzupełnij opis i instrukcję sprawdzenia. Przenieś zadanie
   w Jirze do **In Review**, kiedy zmiana jest gotowa do przeglądu.

Automatyczne tworzenie PR działa po scaleniu konfiguracji workflow do `main`
i włączeniu wymaganych uprawnień Actions przez właściciela repozytorium.
Zawsze można utworzyć PR ręcznie: `gh pr create --base main`. Nie wysyłaj kodu
bezpośrednio na `main`.

## Kontrole lokalne

Backend — z katalogu `backend`:

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run python scripts/export_openapi.py --check
```

Frontend — z katalogu `frontend`:

```bash
npm ci
npm run lint
npm run format:check
npm run typecheck
npm run test
npm run build
```

Po zmianie schematu API wygeneruj kontrakt i typy, a następnie dołącz oba pliki:

```bash
cd backend
uv run python scripts/export_openapi.py
cd ../frontend
npm run api:generate
```

`npm ci` oraz `uv sync --frozen` korzystają z zatwierdzonych lockfile'ów.
Przy zmianie zależności aktualizuj odpowiednio `package-lock.json` lub `uv.lock`.
Migracje PostgreSQL są dodatkowo sprawdzane w CI na nowej, tymczasowej bazie.

## Podział pracy

| Obszar | Pierwszy kontakt / przegląd |
| --- | --- |
| Zakres produktu, kryteria akceptacji, frontend | Jakub Czaja (`jczaja51`) |
| Backend i integracja WEBFLEET | Jakub Nazarewicz (`jnazarewiczs`) i Jakub Czaja |
| Docker, VPS, Azure, GitHub Actions | Dawid Hnat (`DawidHnat`) |
| Testy, scenariusze użytkownika, sprawdzenie PR | Marcel Głowacki (`mglowacki0`) |

To wskazanie osoby do konsultacji, a nie ograniczenie praw do modyfikacji kodu.
Konkretnego właściciela zadania wybieramy w Jirze. `.github/CODEOWNERS` podpowiada
recenzentów dla poszczególnych katalogów.

## Przegląd i scalanie

CI zawsze sprawdza backend, frontend, kontrakt API, migracje i reguły automatyzacji.
**Płatny przegląd przez API AI jest domyślnie wyłączony**. Gdy zespół zdecyduje
się go włączyć, AI skomentuje diff, a automat może scalić tylko zmianę, która
spełnia wszystkie warunki opisane w [WORKFLOW.md](docs/WORKFLOW.md).

Na początek automatyczny merge dopuszcza wyłącznie pliki `.md` w `docs/user/`
i `docs/guides/` oraz pliki `.css` w `frontend/src/`: najwyżej 8 plików i 200
dodanych/usuniętych linii. Kod aplikacji, API, migracje, zależności, infrastruktura,
zasady zespołu i automatyzacja wymagają przeglądu drugiej osoby. Etykieta
`human-review` lub tryb draft blokują automatyczny merge każdej zmiany.

Bez płatnego API druga osoba może obejrzeć PR samodzielnie lub z pomocą Codex
i scalić go na GitHubie po zielonym CI. Nie uznajemy samego komentarza AI za
dowód poprawności funkcji: sprawdzamy kryteria akceptacji i działanie aplikacji.

Jeśli `main` zmienił się podczas pracy, zaktualizuj gałąź i ponownie wykonaj push:

```bash
git fetch origin
git merge origin/main
git push
```

Rozwiąż konflikty i ponownie uruchom właściwe kontrole. Nie wykonuj force pusha
na wspólnej gałęzi. Automat stosuje merge commit, żeby zachować oryginalnych
autorów commitów widocznych w `git shortlog -sn --all`. Po scaleniu właściciel zadania ustawia **Done** w Jirze,
zapisuje link do PR i usuwa swoją gałąź, jeśli nie jest już potrzebna.

## Definition of Done

- Kryteria akceptacji są spełnione i sprawdzone ręcznie.
- Kontrole CI przechodzą dla aktualnego kodu; istotna logika ma testy.
- PR zawiera kontekst, klucz SCRUM i instrukcję sprawdzenia.
- UI uwzględnia ładowanie, brak danych i błąd, jeśli widok pobiera dane.
- Migracje, OpenAPI, typy frontendu i dokumentacja odpowiadają zmianie.
- Dane WEBFLEET oraz sekrety pozostają poza repozytorium i logami.
- Zmiana została scalona, a właściciel zaktualizował zadanie w Jirze.
