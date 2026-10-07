# Praca lokalna

## Najprostszy start: Docker Compose

Wymagania: Git, Python 3.12+ i uruchomiony Docker Desktop z Compose v2.
Na Windows polecenia `python3` można zastąpić `python`, zależnie od instalacji.
Komendy wykonujemy w katalogu głównym repozytorium.

```bash
python3 scripts/bootstrap.py
docker compose up --build -d --wait
docker compose exec api python -m app.db.seed
```

- Aplikacja: http://localhost:5173
- Dokumentacja API: http://localhost:8000/docs
- Health: http://localhost:8000/health
- PostgreSQL: lokalnie `127.0.0.1:5432`, dane dostępowe w własnym `.env`.

Setup tworzy `.env` z losowym hasłem lokalnej bazy, nie wypisuje go i nie
nadpisuje istniejącego pliku. `.env.example` jest szablonem bez sekretów.
Jeżeli `.env` był już utworzony, sprawdź samodzielnie komplet wymaganych zmiennych.
Nie wklejaj zawartości `.env` do PR, Jira, komunikatora ani rozmowy z agentem.

Seed dodaje przykładowe dane jawnie i służy wyłącznie do trybu `demo`.
Backend podczas uruchomienia wykonuje migracje; frontend i backend mają hot reload.
Zmiana zależności lub Dockerfile wymaga ponownego `docker compose up --build`.

```bash
docker compose logs --tail=100 api web
docker compose down
```

`down` zachowuje nazwany wolumen bazy. Nie dodawaj `-v`, gdy chcesz zachować
przejazdy i opisy — ta opcja usuwa lokalne dane. Każda osoba ma własny wolumen.

## API WEBFLEET

Zespół posiada dostęp do API; każdy uprawniony developer ustawia dane w lokalnym
`.env`. Sekrety pozostają po stronie backendu:

```dotenv
DATA_SOURCE=webfleet
WEBFLEET_ACCOUNT=
WEBFLEET_USERNAME=
WEBFLEET_PASSWORD=
WEBFLEET_API_KEY=
```

Po uzupełnieniu danych odtwórz kontener API i wykonaj importer:

```bash
docker compose up -d --force-recreate api
docker compose exec api python -m app.integrations.webfleet.sync
```

Importer pobiera odczyty pojazdów i zapisuje je do lokalnej bazy. Nie wysyła
komend do pojazdów. Historia tras i dane do bardziej rozbudowanej analityki
wymagają kolejnych implementacji; pusta historia w trybie live nie jest błędem
uprawniającym do podłożenia danych demo. Wersję i pola odpowiedzi trzeba
sprawdzić na Waszym koncie przed rozszerzaniem mapowania.

Mapbox wymaga osobnego publicznego tokenu przeglądarkowego `VITE_MAPBOX_TOKEN`.
Ogranicz go do odpowiednich domen. Po jego zmianie odtwórz kontener web.
Bez tokenu reszta interfejsu działa, a mapa pokazuje stan braku konfiguracji.
Żaden sekret backendu nie może mieć prefiksu `VITE_`.

## Uruchomienie bez kontenerów aplikacji

Potrzebne są Node w wersji zgodnej z `frontend/package.json`, Python 3.12+
i `uv`. Bazę można nadal uruchomić w Dockerze:

```bash
python3 scripts/bootstrap.py
docker compose up -d db
cd backend
uv sync --frozen
uv run alembic upgrade head
uv run python -m app.db.seed
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

W drugim terminalu, z katalogu głównego:

```bash
cd frontend
npm ci
npm run dev
```

Frontend używa `/api` i proxy do lokalnego portu 8000. `API_PROXY_TARGET`
może zmienić adres backendu bez zmian w kodzie przeglądarki.

## Kontrole przed pushem

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run python scripts/export_openapi.py
```

Następnie w `frontend/`:

```bash
npm ci
npm run api:generate
npm run lint
npm run format:check
npm run typecheck
npm test
npm run build
```

Testy skryptów GitHub, z katalogu głównego:

```bash
python3 -m unittest discover -s scripts/github/tests
```

Na systemie z Make odpowiadają temu `make setup`, `make dev`, `make seed`,
`make contracts`, `make check` i `make stop`. Windows może użyć poleceń powyżej.

## Typowy problem: zajęty port

Jeżeli 5432, 8000 lub 5173 używa inna aplikacja, zatrzymaj tę aplikację lub
świadomie zmień port hosta w Compose oraz adresy lokalnego API i CORS.
Nie uruchamiaj wszystkich usług na publicznym `0.0.0.0` hosta jako obejścia.

Zasady gałęzi, PR i przeglądu AI: [CONTRIBUTING.md](../CONTRIBUTING.md).
