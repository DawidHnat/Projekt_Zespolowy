# Integracje backendu — SCRUM-14

Backend ma adapter WEBFLEET i polecenia diagnostyczne integracji. Python 3.12 lub
3.13. Testy działają bez konta WEBFLEET, skrzynki SMTP i danych klientów.
FastAPI, PostgreSQL, migracje i health: SCRUM-39. Logowanie i sesje: SCRUM-16.
Synchronizacja pojazdów: SCRUM-15. Zabezpieczone API listy/mapy: SCRUM-19.
Reguły i alerty dziennego dystansu: SCRUM-31.
Cel i opis zapisanych przejazdów, audyt i konflikt wersji: SCRUM-26.
Przeglądarka nie odpytuje WEBFLEET bezpośrednio.

SCRUM-26 wymaga migracji `0005_trip_annotations` (`alembic upgrade head`).
GET `/api/v1/trips` i `/api/v1/trips/{id}` czytają zapisane przejazdy;
PATCH `/api/v1/trips/{id}/annotation` zapisuje wyłącznie ręczne pola.
Import historii ze źródła pozostaje w SCRUM-24. Szczegóły kontraktu i scenariusze
odbioru: [model danych](../docs/DATA_MODEL.md) i [QA SCRUM-26](../docs/qa/SCRUM-26.md).

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
procesów i uruchomień CLI. Synchronizacja w SCRUM-15 ma jednego wspólnego właściciela odpytywania,
limit przez bazę i cache ostatniego wyniku; interwał wynosi 60 sekund. Nie uruchamiaj kilku kopii testu w pętli.

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
w OVH oraz zapis `.env`. Nie uruchamiaj seryjnych prób. Opcjonalny reset hasła
jest zaimplementowany w module uwierzytelniania: token jednorazowy z datą ważności,
limit prób i neutralna odpowiedź dla nieistniejących kont. Konfiguracja konta
oraz ograniczenia dostawy są opisane w sekcji SCRUM-44 poniżej.
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

## Konta aplikacji — SCRUM-16

Nie ma publicznej rejestracji. Administrator lokalnie tworzy konta:

```bash
python -m app.manage create-user jczaja51 --name 'Jakub Czaja' --role admin
python -m app.manage create-user DawidHnat --name 'Dawid Hnat' --role editor
python -m app.manage set-password jczaja51
```

Polecenie pyta o hasło bez pokazywania go i bez argumentu w historii powłoki.
Zmiana hasła unieważnia sesje. Konto użytkownika aplikacji i ręczny wpis kierowcy
są osobnymi encjami. Login jest normalizowany do małych liter. Hasła mają Argon2id,
a baza przechowuje tylko hash losowego tokenu sesji; sesja trwa 12 h. Cookie jest
HttpOnly/SameSite=Strict, `Secure` zależy od `COOKIE_SECURE`. Zapisy wymagają Origin
z `CORS_ORIGINS`; nie ustawiaj `*`. Dozwolone role: admin/editor/viewer.

`POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `POST /api/v1/auth/logout`.
Login jest limitowany przez bazę do 10 prób/minutę na IP i login. Nagłówki proxy
nie są używane jako tożsamość IP. Wdrożenie za proxy wymaga osobnego ustawienia
zaufanych proxy; przed wystawieniem zdalnie wymagane są HTTPS i Secure cookie.
Reset e-mail jest osobnym przyrostem SCRUM-44 opisanym poniżej.
Administrator może także ustawić hasło lokalnym poleceniem powyżej.

## Synchronizacja pojazdów — SCRUM-15

Operator ma `python -m app.sync_control once` (pojedynczy **żywy import**, tylko
po wyraźnym uzgodnieniu) oraz `python -m app.sync_control status` (odczyt cache,
bez wywołania dostawcy). Status zwraca niezerowy kod przy braku/awarii lub wieku
ostatniego sukcesu ponad 180 s. Procedura VPS i wymagane dowody:
[SCRUM-64](../docs/qa/SCRUM-64.md). Nieoczekiwane błędy workera mają stały kod
zdarzenia i losowe event_id; log nie zawiera wyjątku, SQL ani telemetryki.

`SYNC_ENABLED=true` w lokalnym `.env` włącza jeden wspólny odczyt co 60 s.
PostgreSQL advisory lock i zapis czasu próby chronią limit także przy kilku
procesach. Nie uruchamiaj równolegle diagnostyki w pętli. Awaria zachowuje dane
ostatniego sukcesu; brak kompletnego raportu nie dezaktywuje pojazdów. Import
aktualizuje wyłącznie pola pojazdu/pomiaru — nigdy ręcznych kierowców/przypisań.
Historia przejazdów nie jest jeszcze synchronizowana. Jej import, postoje
i harmonogram należą do SCRUM-24; adnotacje są kolejnym przyrostem.

## API floty — SCRUM-19

Po zalogowaniu: `/api/v1/fleet/vehicles`, `/fleet/map`, `/fleet/summary` oraz
`/fleet/vehicles/{UUID}` (wspólny prefiks `/api/v1`). Lista i mapa obsługują `q`
i `status`; lista dodatkowo `page`/`page_size`. Mapa zwraca GeoJSON i obejmuje
pasujące pozycje z całej listy, niezależnie od jej bieżącej strony. Pojazdy bez
GPS pozostają na liście. Dane stare i brakujące mają jawne oznaczenia; prędkość
pozostaje `null` do potwierdzenia jednostki. Publiczne API nie zwraca UID źródła.
`/docs` pokazuje aktualny OpenAPI; plan kolejnych operacji jest w contracts/.

## Reset hasła przez e-mail — SCRUM-44

SMTP TLS i logowanie zweryfikowano; test diagnostyczny nie wysłał wiadomości.
Administrator przypisuje **własny adres danej osoby**, nie wspólną skrzynkę:

```bash
python -m app.manage set-email jczaja51 --email owner@example.com
```

`owner@example.com` jest przykładem; wpisz adres wybrany przez właściciela konta.
`create-user` przyjmuje opcjonalne `--email`. Zmiana adresu lub ustawienie hasła
lokalnie unieważnia tokeny resetu. SMTP nadawcą jest `SMTP_USERNAME`.

Ekran „Nie pamiętam hasła” wywołuje `POST /api/v1/auth/password/request` z loginem.
Odpowiedź pozostaje neutralna, także przy braku konta/e-maila i limitach: 3/h na
login i 10/h na IP, współdzielone przez bazę. Link wskazuje dokładnie dozwolony
Origin aplikacji i ma token we fragmencie URL, który nie trafia do HTTP access log.
Token ma 20 minut ważności; baza przechowuje tylko SHA-256. Potwierdzenie resetu
(`/auth/password/confirm`) blokuje rekordy w PostgreSQL i umożliwia dokładnie
jedno użycie, ustawia Argon2id i unieważnia wszystkie sesje oraz tokeny konta.

Wysyłka jest zadaniem w tle procesu, bez trwałej kolejki. Przerwanie procesu lub
awaria SMTP może przerwać wysyłkę; użytkownik może później poprosić o nowy link.
Trwały outbox pozostaje dalszym usprawnieniem. Testy używają atrapy SMTP — nie
wysyłają do prawdziwych skrzynek. Dostarczenie wiadomości wymaga osobnego odbioru
QA na zatwierdzony adres. Konta startowe bez przypisanego e-maila nadal mogą
logować się hasłem ustawionym przez administratora.

## Reguły i alerty dziennego dystansu — SCRUM-31

Migracja `0004` dodaje reguły, obserwowany dzienny dystans, alerty i osobny stan
przeczytania każdej osoby. Uruchom `alembic upgrade head` przed startem nowej wersji.
Wszystkie operacje poniżej mają prefiks `/api/v1/analytics` i wymagają sesji:

- `GET /rules` — lista z `page` / `page_size` (domyślnie 25, maksymalnie 100).
- `POST /rules` — `type: "daily_distance_threshold"`, dodatni `threshold_km`
  z dokładnością do 0,1 km, opcjonalny `vehicle_id` i `active` (domyślnie true).
  `vehicle_id: null` obejmuje całą flotę bieżącego konta źródła; UUID wskazuje
  jeden aktywny pojazd. Zapis wymaga roli admin/editor i poprawnego Origin.
- `PATCH /rules/{UUID}` — zmiana progu, pojazdu lub aktywności; co najmniej jedno
  pole. `{"active": false}` wyłącza regułę i zachowuje wcześniejsze alerty.
- `GET /alerts` — paginacja jak wyżej, opcjonalne `read=true/false`; najnowsze
  zdarzenie najpierw, UUID rozstrzyga ten sam czas. Odpowiedź zawiera próg,
  `distance_km`, `event_day`, czas zdarzenia i `read_at` danej osoby.
- `PATCH /alerts/{UUID}/receipt` — `{"read": true}` lub false; dostępne także
  dla viewer, z kontrolą Origin. Nie zmienia odczytu innych użytkowników.

Próg dotyczy **dystansu przejechanego w dniu**, a nie wartości licznika. Worker
wykorzystuje już pobierane odczyty WEBFLEET, bez dodatkowych wywołań dostawcy.
Sumuje dodatnie różnice licznika pomiędzy kolejnymi pomiarami z tego samego dnia
`Europe/Warsaw`, oddalonymi o maksymalnie 15 minut. Pierwszy odczyt ustala punkt
startowy. Powtórzony/starszy lub przyszły pomiar, brak wartości, cofnięcie licznika,
luka dłuższa niż 15 minut i odcinek przez północ nie dopisują dystansu.
Po cofnięciu licznika następny poprawny odcinek może rozpocząć nową obserwację.

To dolna granica zaobserwowanego dystansu. API podaje `coverage: "partial"`;
nie udaje pełnej historii dnia ani zerowego dystansu przy braku danych.
Historia przejazdów i pełne zestawienia pozostają SCRUM-24/29. Dane utrzymują się
po ponownym uruchomieniu, ponieważ dystans i checkpoint pomiaru są w PostgreSQL.

Świeża obserwacja (do 15 minut) **ściśle większa** od progu generuje alert.
Równość nie wystarcza. Przeliczenie następuje w transakcji udanej synchronizacji
oraz po utworzeniu/edycji reguły. Klucz UNIQUE `(rule_id, vehicle_id, event_day)`
i UPSERT chronią ponowne odczyty i równoległe procesy. Dzień jest przypisany
według pomiaru w polskiej strefie; znaczniki czasu API są UTC. Alert przechowuje
próg i dystans z chwili wykrycia, więc późniejsza edycja reguły nie zmienia historii.
Reguły i alerty są ograniczone do bieżącego konta źródła. Formularze i lista we
frontendzie pozostają SCRUM-32; odbiór zespołowy alertów jest w SCRUM-33.

Przypadki testowe i instrukcja sprawdzenia: [QA SCRUM-31](../docs/qa/SCRUM-31.md).

## Dokumentacja API i role (SCRUM-103)

Swagger `/docs`, ReDoc `/redoc` i `/openapi.json` są domyślnie dostępne przy
lokalnych CORS_ORIGINS. Zdalny origin wyłącza je; jawne włączenie docs dla
zdalnego originu jest odrzucane. `API_DOCS_ENABLED=false` wyłącza docs także
lokalnie. Testy kontraktu nadal używają schematu wewnętrznie.

Role `admin`, `editor`, `viewer` mają constraint bazy. Migracja nie poprawia
nieznanych ról za operatora i nie zmienia istniejących uprawnień.
[Sprawdzenie danych, rollout i rollback](../docs/security/SCRUM-103.md).

## Ręczna kartoteka kierowców (SCRUM-52)

Chronione `/api/v1/drivers` udostępnia profile, katalog kategorii i historię
przypisań wiele do wielu. POST `/api/v1/drivers/search` przenosi wyszukiwanie
kontaktu do treści żądania. Zapis wymaga admin/editor i bieżącego version;
viewer ma odczyt. Ocena kategorii pozostaje not_evaluated do SCRUM-70.
[Migracja 0008, stare rekordy i instrukcja odbioru](../docs/qa/SCRUM-52.md).


Integracja SCRUM-53 rozszerza odczyt kierowców o `missing_categories` i sort
`custom` z `custom_order` (unikalne UUID, maks. 2000). Sort jest stosowany w SQL
przed paginacją, a pozostałe osoby mają stabilną kolejność A–Z. Obce UUID
nie rozszerzają źródła. POST search zwraca te same filtry w agregatach, niezależnie
od strony; kontakt nadal pozostaje w body. Telefon dopuszcza jeden opcjonalny
plus na początku i 7–20 cyfr, ze spacjami/nawiasami/kropkami/myślnikami.
