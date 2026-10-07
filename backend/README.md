# Backend Fleet-Flow

Modularny monolit FastAPI: `modules/fleet`, `modules/trips`, `modules/analytics`.
`core` zawiera konfigurację, `db` połączenie i jawny seed, a `integrations/webfleet`
transport i mapowanie dostawcy. Routery obsługują HTTP, modele ORM zapisują dane,
schematy Pydantic opisują kontrakt dla frontendu. Nie dodajemy mikroserwisów ani
kolejek przed rzeczywistą potrzebą.

Z katalogu `backend`, Python 3.12+ i [uv](https://docs.astral.sh/uv/):

```sh
uv sync --frozen
uv run alembic upgrade head
uv run python -m app.db.seed
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API: `http://localhost:8000/docs`. `/health` sprawdza proces, `/ready` połączenie
z bazą. Migracje wykonujemy osobno; samo uruchomienie API nie tworzy tabel,
nie dopisuje danych demonstracyjnych i nie wysyła zapytań do Webfleet.

W repozytorium głównym uruchom `python3 scripts/bootstrap.py`, aby utworzyć `.env`
z losowym hasłem lokalnej bazy. Backend odczytuje ten plik
niezależnie od katalogu roboczego. Opcjonalny `backend/.env` ma pierwszeństwo,
a zmienne środowiska procesu mają pierwszeństwo przed plikami. PostgreSQL jest
docelową bazą; SQLite służy tylko do izolowanych testów.

## Źródła i synchronizacja

`DATA_SOURCE=demo` wybiera wyłącznie rekordy oznaczone `demo`. Seed jest jawny,
idempotentny i zachowuje istniejące opisy. `DATA_SOURCE=webfleet` wybiera wyłącznie
rekordy `webfleet`; pusta baza daje pustą listę, nigdy zastępcze dane demo.

Uzupełnij lokalnie `WEBFLEET_ACCOUNT`, `WEBFLEET_USERNAME`, `WEBFLEET_PASSWORD`,
`WEBFLEET_API_KEY`; opcjonalnie `WEBFLEET_TIMEOUT_SECONDS` (domyślnie 15):

```sh
uv run python -m app.integrations.webfleet.sync
```

Adapter wykonuje dwa odczyty HTTPS GET: `showVehicleReportExtern` oraz
`showObjectReportExtern`; łączy je przez `objectuid` (awaryjnie `objectno`).
Używa Basic Auth dla loginu i hasła, parametrów `account` i `apikey`, JSON,
UTF-8 i dat UTC. Dla tych odczytów dokumentacja nie dopuszcza POST. Podstawą jest
[oficjalny WEBFLEET.connect Reference Guide 1.58, rozdziały HTTP i Objects](https://media.webfleet.com/fl_attachment/media/doc/documentations/webfleet.connect-doc-1.58.0).
Nie loguj pełnego adresu żądania: zawiera klucz API; adapter wyłącza logi INFO
`httpx`/`httpcore` i zwraca bezpieczne komunikaty bez odpowiedzi dostawcy.

Synchronizacja zapisuje całą odpowiedź w jednej transakcji. Nie usuwa pojazdów
ani lokalnych opisów przejazdów; pojazdy pominięte przez dostawcę oznacza jako
offline (pominięcie może wynikać też ze zmiany uprawnień). Nie uruchamia się
automatycznie. Przy ręcznych uruchomieniach zostaw co najmniej 10 sekund przerwy
między próbami; limit raportu obiektów wynosi 6 zapytań/minutę według dokumentacji.

Brak odczytu prędkości lub licznika oznacza `null`, a nierozpoznany stan oznacza
`unknown`. `odometer_long` jest przeliczany z metrów, starszy `odometer` ze
100 metrów, współrzędne `*_mdeg` z mikrostopni. Stan jazdy jest uproszczonym
wnioskiem z prędkości i GPS, nie oficjalnym polem stanu Webfleet. Ostatnia pozycja
starsza niż 24 godziny oznacza offline. `updated_at` to czas pozycji dostawcy;
gdy go brakuje, czas pobrania rekordu, ze stanem unknown i bez współrzędnych.
Brak rejestracji/nazwy zastępujemy numerem obiektu (etykietą identyfikacyjną).

**Historia przejazdów Webfleet nie jest jeszcze importowana.** W trybie live
historia i dystans przejazdów są puste/zerowe do czasu dodania osobnego zadania
mapowania `showTripReportExtern`, zakresu dat i stabilnych identyfikatorów.
PATCH celu/notatki dotyczy tylko naszej bazy; nie zapisuje nic do Webfleet.
Analityka liczy zapisane przejazdy, nie sumę liczników. Alert prędkości >90 km/h
jest przykładową regułą techniczną, nie oceną legalności jazdy ani docelowym
konfigurowalnym mechanizmem alertów.

## Kontrola zmian

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run python scripts/export_openapi.py
uv run python scripts/export_openapi.py --check
uv run alembic check
```

Eksport OpenAPI jest deterministyczny i nie potrzebuje działającej bazy ani kluczy.
`alembic check` potrzebuje zmigrowanej bazy i wykrywa rozjazd modeli z migracjami.
Nową zmianę schematu dodajemy przez `uv run alembic revision --autogenerate -m ...`
i przeglądamy wygenerowaną migrację przed zatwierdzeniem.

To podstawa do lokalnej pracy zespołu. Przed publicznym wdrożeniem API wymagane
są osobne zadania uwierzytelniania, autoryzacji, HTTPS oraz zasad dostępu do danych
floty. Uruchamiaj API i PostgreSQL na localhost lub przez tunel SSH.
