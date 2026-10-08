# Integracje backendu — SCRUM-14

Backend ma adapter WEBFLEET i polecenia diagnostyczne integracji. Python 3.12 lub
3.13. Testy działają bez konta WEBFLEET, skrzynki SMTP i danych klientów.
FastAPI, PostgreSQL, migracje i health są zakresem SCRUM-39. Uwierzytelnienie
aplikacji — SCRUM-16, a endpointy listy pojazdów — SCRUM-19. Nie uruchamiamy
odpytywania API w przeglądarce.

## Uruchomienie z czystego checkoutu

W katalogu głównym repozytorium:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
cp .env.example .env
```

Jeżeli `.env` już istnieje, zachowaj jego zawartość i dopisz brakujące ustawienia
z `.env.example`. Wpisuj dane w lokalnym edytorze. Hasła z `#`, `$` lub spacjami
ujmij w pojedynczy albo podwójny cudzysłów zgodnie ze składnią dotenv. Interpolacja
`${...}` jest wyłączona, żeby nie zmieniała haseł. Zmienne środowiska procesu mają
pierwszeństwo przed plikiem. W systemie Windows aktywuj `.venv\Scripts\Activate.ps1`.

Uzupełnij trzy wartości `POSTGRES_*` i odpowiadający im `DATABASE_URL`.
Hasło w URL wymaga kodowania znaków specjalnych. Uruchom Docker Desktop, następnie:

```bash
docker compose -p fleet-flow-dev -f compose.local.yml up -d --wait
cd backend
alembic upgrade head
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

`/api/health/live` sprawdza proces, `/api/health/ready` — połączenie z bazą.
Nie zwracają adresu bazy ani wyjątków. Migracje wykonujemy jawnie przed startem.
`docker compose ... down` zatrzymuje bazę, zachowując wolumen. Nie dodawaj `-v`,
jeśli chcesz zachować dane. Baza i API są dostępne lokalnie; wystawienie na VPS
wymaga osobnego zadania z HTTPS, `COOKIE_SECURE=true` i konkretnym Origin.

CI sprawdza także upgrade/check/downgrade/upgrade na pustej bazie PostgreSQL 17.
Lokalnie test migracji wymaga `TEST_DATABASE_URL` do osobnej bazy o nazwie
zaczynającej się od `fleet_flow_test`; test odrzuca pozostałe bazy.

## WEBFLEET — test tylko do odczytu

Uzupełnij `WEBFLEET_ACCOUNT`, `WEBFLEET_USERNAME`, `WEBFLEET_PASSWORD` i
`WEBFLEET_API_KEY`. Konto, login użytkownika i klucz API to osobne wartości.
Użytkownik WEBFLEET musi mieć uprawnienia WEBFLEET.connect i dostęp do potrzebnych
obiektów. Konto pocztowe samo nie nadaje tych uprawnień.

```bash
cd backend
python -m app.diagnostics webfleet
```

Polecenie wykonuje pojedynczy `showObjectReportExtern`. Zwraca JSON: `ok`, liczbę
rekordów, liczbę poprawnych identyfikatorów i pokrycie pól. Nie wypisuje wartości
identyfikatorów, nazw ani współrzędnych. Nie zapisuje odpowiedzi do pliku.
Kod wyjścia `0` oznacza udany test, `1` — błąd. Pusta lista jest poprawną odpowiedzią,
ale nie potwierdza istnienia pojazdów ani uprawnień do szerszej floty.

Adapter używa HTTPS i HTTP Basic Auth. Hasło nie trafia do URL. Klucz API pozostaje
parametrem żądania wymaganym przez dostawcę; szczegóły tych żądań są ukrywane
w logach HTTPX/httpcore. Przekierowania są odrzucane, certyfikaty sprawdzane,
a błędy dostawcy nie są kopiowane do komunikatów aplikacji. Timeout wynosi domyślnie
20 sekund; można ustawić 1–120. Brak automatycznych ponowień.

Limit tej operacji to 6 żądań/minutę. Jedna instancja klienta nie pozwala na
ponowne żądanie przed upływem 10 sekund. To nie jest wspólny limiter wszystkich
procesów i uruchomień CLI. Docelowa synchronizacja w SCRUM-15 musi mieć jednego
właściciela odpytywania, wspólny limit i bufor ostatniego wyniku; proponowany
interwał startowy to 60 sekund. Nie uruchamiaj kilku kopii testu w pętli.

## Poczta OVH — test logowania bez wysyłki

```dotenv
SMTP_HOST=smtp.mail.ovh.net
SMTP_PORT=465
SMTP_USERNAME=kontakt@fleet-flow.pl
SMTP_PASSWORD=
SMTP_TIMEOUT_SECONDS=20
```

`SMTP_PASSWORD` to hasło tej skrzynki. Serwer SMTP używa TLS na porcie 465 oraz
pełnego adresu jako loginu. Jeżeli webmail żąda zmiany hasła przy pierwszym
logowaniu, właściciel skrzynki musi zakończyć ją i uaktualnić lokalne `.env`.

```bash
python -m app.diagnostics smtp
```

Test sprawdza TLS, wykonuje `LOGIN` i `NOOP`, po czym zamyka połączenie. Nie wysyła
wiadomości. Udane logowanie nie potwierdza dostarczalności do innych domen.
Certyfikaty weryfikuje zestaw CA `certifi`, również na Macach bez skonfigurowanego
systemowego magazynu CA dla Pythona. Nie wyłączamy weryfikacji TLS.

Jeśli logowanie jest odrzucone, sprawdź hasło przez webmail, aktywność skrzynki
w OVH oraz zapis `.env`. Nie uruchamiaj seryjnych prób. Obsługa wysyłki resetów haseł
dojdzie do modułu uwierzytelniania: token jednorazowy z datą ważności, limit prób,
neutralna odpowiedź dla nieistniejących kont i ograniczenie częstotliwości wysyłki.
Diagnostyka nie udostępnia publicznego endpointu wysyłania e-maili.

## Inny katalog pliku .env i weryfikacja kodu

```bash
python -m app.diagnostics webfleet --env-file /sciezka/do/lokalnego/.env
python -m app.diagnostics smtp --env-file /sciezka/do/lokalnego/.env
ruff check .
ruff format --check .
pytest
```

CI wykonuje te kontrole na Pythonie 3.12 i 3.13, używając wyłącznie fikcyjnych
przypadków testowych. Prawdziwych danych i sekretów nie dodajemy do Git, PR,
załączników ani GitHub Actions. Zasady mapowania i ograniczenia dalszej integracji
są opisane w [WEBFLEET_INTEGRATION.md](../docs/WEBFLEET_INTEGRATION.md).
