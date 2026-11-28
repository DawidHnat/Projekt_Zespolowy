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

## Profil i bezpieczeństwo konta — SCRUM-49 (pierwszy przyrost)

- `GET /api/v1/auth/profile`: własna nazwa, login, e-mail lub `null` i rola;
  wymaga sesji, nie udostępnia edycji roli/statusu.
- `POST /api/v1/auth/password/change`: `current_password`, `new_password`.
  Nowe hasło ma 12–1024 znaki i musi być inne. Wymaga sesji oraz Origin;
  dostępne także dla viewer. Limit prób: 5/15 min na konto, 10/15 min na IP.
  Błędne obecne hasło daje 400 bez wylogowania. Błędy walidacji nie odbijają
  haseł. Udana zmiana usuwa wszystkie stare sesje i tokeny resetu; bieżąca
  przeglądarka otrzymuje nowy losowy token HttpOnly/SameSite=Strict/Secure w HTTPS.
- `POST /api/v1/auth/sessions/logout-all`: unieważnia wszystkie sesje własnego
  konta, także bieżącą, i usuwa cookie. Kolejny odczyt wymaga logowania.

Operacje oraz logowanie blokują rekord User w PostgreSQL. Po uzyskaniu blokady
zmiana hasła/wylogowanie ponownie sprawdzają ważność sesji, aby drugie żądanie
ze starym tokenem nie ominęło unieważnienia. Nie potrzeba nowej migracji.

Powiadomienie o zmianie hasła trafia wyłącznie na przypisany adres, gdy jest
skonfigurowane SMTP. Nie zawiera haseł ani linku resetu. Jest zadaniem w tle,
bez gwarancji trwałego doręczenia; awaria SMTP nie cofa udanej zmiany hasła.
Zmiana adresu i jego potwierdzanie pozostają poza tym przyrostem. Testy używają
atrap SMTP, a rzeczywista wysyłka wymaga osobnego uzgodnienia.

Gdy dostawa linku resetu przez SMTP zgłosi błąd, poprzedni niewykorzystany
link zachowuje ważność do swojego terminu. Po potwierdzonej dostawie nowego
linku starsze linki tego konta są usuwane. Publiczna odpowiedź pozostaje
neutralna. Log `fleet_flow.auth` emituje jeden stały sygnał
`password_reset_smtp_failed` dla nieudanej dostawy. Komunikaty setup/state
wskazują problemy konfiguracji lub zapisu i mają własne stałe kody.
Żaden z nich nie zawiera adresu odbiorcy, tokena ani wyjątku SMTP.

## Synchronizacja pojazdów — SCRUM-15

Operator ma `python -m app.sync_control once` (pojedynczy **żywy import**, tylko
po wyraźnym uzgodnieniu) oraz `python -m app.sync_control status` (odczyt cache,
bez wywołania dostawcy). Status zwraca niezerowy kod przy braku/awarii lub wieku
ostatniego sukcesu ponad 180 s. Procedura VPS i wymagane dowody:
[SCRUM-64](../docs/qa/SCRUM-64.md). Nieoczekiwane błędy workera mają stały kod
zdarzenia i losowe event_id; log nie zawiera wyjątku, SQL ani telemetryki.

`SYNC_ENABLED=true` w lokalnym `.env` włącza jeden wspólny odczyt. `SYNC_INTERVAL_SECONDS`
ustawia częstotliwość (domyślnie 60 s, minimum 10 s zgodnie z limitem źródła),
a `STALE_SECONDS` próg nieaktualności pomiaru (domyślnie 900 s). Ten sam próg
obowiązuje przy ocenie alertu po synchronizacji (w tym ręcznym odświeżeniu)
i przy tworzeniu lub edycji reguły. Obie wartości
są walidowane przy starcie; nie ustawiaj częstotliwości przed sprawdzeniem limitów
WEBFLEET dla używanego konta.
PostgreSQL advisory lock i zapis czasu próby chronią limit także przy kilku
procesach. Nie uruchamiaj równolegle diagnostyki w pętli. Awaria zachowuje dane
ostatniego sukcesu. Pierwszy pusty odczyt jest poprawny, jeżeli oba raporty
są puste. Brak dowolnego wcześniej aktywnego pojazdu w raporcie głównym daje
`INCOMPLETE_REPORT`: cały ostatni stan pozostaje w cache, a źródło jest
`degraded` do czasu poprawnego odczytu. Sama nieobecność w raporcie nie jest
dowodem dezaktywacji. Import aktualizuje wyłącznie pojazdy i pomiary.
Kierowcy i przypisania są wprowadzane ręcznie.
Synchronizator ponawia timeout, błąd połączenia, limit źródła i błędy HTTP 408,
425 oraz 5xx maksymalnie do trzech prób na każdy raport (dwie ponowne próby),
z co najmniej 10 s przerwy wymaganej przez raport i z uwzględnieniem `Retry-After`
do 60 s. Adapter i diagnostyka pozostają bez automatycznych ponowień. Po
wyczerpaniu prób API nadal udostępnia ostatni zapisany cache ze statusem źródła
`degraded` i czasem ostatniego sukcesu.
### Import historii pojazdu — SCRUM-24

Importer działa jako oddzielny proces operatora. Po migracji 0012 i uzgodnieniu
próby dostawcy operator wskazuje wewnętrzne UUID pojazdu oraz od jednego do 93
zakończonych dni w Europe/Warsaw. Przykład poniżej jest poleceniem **żywego**
odczytu. W testach używamy wyłącznie atrapy.

```shell
python -m app.trip_history_control --vehicle 11111111-1111-4111-8111-111111111111   --from 2026-10-24 --through 2026-10-25
```

Jedna próba przetwarza jeden najwcześniejszy dzień wymagający pobrania. Kolejne
uruchomienie wznawia pracę po wspólnym limicie 60 s na konto i uwzględnia
`Retry-After`. PostgreSQL blokuje drugi proces dla konta. Doba liczy 23, 24 lub
25 godzin. Raport dostawcy filtruje po czasie końca, a API historii pokazuje
zdarzenia pokrywające wybrany okres. Pokrycie informuje, które dobowe raporty
odebrano i które mają błąd. Opóźnione zgłoszenie można pobrać ponownie dla jednego
dnia z `--refresh`; pełna ciągła replikacja pozostaje dalszym zakresem SCRUM-24.

Przejazd zachowuje UUID, adnotację i identyfikację wynikającą z pojedynczego
znanego przypisania w chwili rozpoczęcia. Przy niejednoznaczności identyfikacja
pozostaje pusta. Korekty licznika nie są przejazdami. Dystans jest w kilometrach,
postój ma czasy, czas trwania w sekundach i dostępny opis miejsca. Odczyt
`/trips/stops` domyślnie obejmuje postoje od 300 s, parametr
`min_duration_seconds=0` pozwala zobaczyć także krótsze. Zakres operacji i
jednostki opisuje [dokumentacja WEBFLEET](https://media.webfleet.com/fl_attachment/media/doc/documentations/webfleet.connect-doc-1.74.0.pdf#page=244).
Ponowny import zakończonego dnia traktuje raport jako kompletny: postoje i przejazdy
bez lokalnej adnotacji, których nowy raport już nie zawiera, są usuwane, a przejazd
z celem lub opisem zostaje zachowany i oznaczony `withdrawn_at` („Wycofany z raportu
źródła”, kolumna z migracji `0016_trip_withdrawn`). Powrót przejazdu do raportu czyści
oznaczenie, zachowując UUID i adnotację. Downgrade `0016` odmawia, gdy istnieją takie przejazdy.
Rollback aplikacji zachowuje nowe kolumny i tabele; poprzednia wersja aplikacji
działa na rozszerzonym schemacie. Downgrade poniżej `0012_trip_history` jest
blokowany, gdy istnieją zaimportowane postoje, pokrycie raportów, adresy lub
kierowcy przejazdów, bo usunąłby te dane. Przy wycofaniu zachowaj schemat
i cofnij tylko aplikację; DDL cofaj wyłącznie na bazie bez zaimportowanej historii.
Przed downgrade zatrzymaj worker importu historii. Migracja i tak pobiera blokady
`ACCESS EXCLUSIVE` na tabelach historii przed sprawdzeniem, więc równoległy import
czeka i nie może zapisać danych pomiędzy kontrolą a usunięciem tabel.
`0012_trip_history` leży na równoległej gałęzi grafu (scalonej w `0015`), więc jej
cofnięcie wymaga dwóch kroków: `alembic downgrade 0014_merge_account_links`
(usuwa `0016` i `0015`), a potem `alembic downgrade 0012_trip_history@-1`.
Samo `downgrade 0014_merge_account_links` nie cofa historii przejazdów.

## API floty — SCRUM-19

Po zalogowaniu: `/api/v1/fleet/vehicles`, `/fleet/map`, `/fleet/summary` oraz
`/fleet/vehicles/{UUID}` (wspólny prefiks `/api/v1`). Lista i mapa obsługują `q`
i `status`; lista dodatkowo `page`, `page_size` i `sort` (`name-asc`, `name-desc`,
`status`, `odometer-asc`, `odometer-desc`). Sortowanie odbywa się przed
paginacją. Mapa zwraca GeoJSON i obejmuje
pasujące pozycje z całej listy, niezależnie od jej bieżącej strony. Pojazdy bez
GPS pozostają na liście. Prędkość świeżego, poprawnego pomiaru jest podawana
w `speed_kmh` (km/h, 0–300); brak, stary/przyszły pomiar, niedostępne źródło
lub niepotwierdzony GPS oznaczają `null`, bez zastępowania braku zerem.
[Kontrolne potwierdzenie jednostki](../docs/qa/SCRUM-14-speed-unit.md).

Synchronizacja przyjmuje czas pozycji najwyżej równy zakończeniu odczytu
(tolerancja przyszłości 0 s). Pomiar przyszły, spóźniony, powtórzony lub bez
czasu nie zastępuje ostatniej poprawnej pozycji. Przy równych znacznikach czasu
pozostaje pierwszy zapis. Poprawna próbka może zastąpić stary rekord zapisany
z przyszłym czasem. Taki rekord nie jest punktem odniesienia przy obliczaniu
dystansu.

Edycja kartoteki (PATCH) wymaga aktualnej wartości `card_version` zwróconej
przez odczyt pojazdu oraz co najmniej jednego pola. Wersja rośnie po zapisie.
Konflikt zwraca HTTP 409 `VERSION_CONFLICT`. Podanie ręcznej nazwy,
rejestracji lub typu blokuje nadpisywanie wyłącznie tego pola. Pusta ręczna
rejestracja lub typ pozostają puste. Numer obiektu pochodzi ze źródła.
Migracja 0011 zachowuje nazwę, rejestrację i typ starych kartotek oznaczonych
jako edytowane, ponieważ wcześniejsza flaga nie wskazuje konkretnego pola.
Rollback aplikacji zachowuje rozszerzony schemat i wartości. Cofnięcie DDL
usuwa szczegółową własność oraz wersję, dlatego przed odtworzeniem zachowaj
kopię rozszerzonego schematu.
Publiczne API nie zwraca UID źródła.
`/docs` pokazuje aktualny OpenAPI; plan kolejnych operacji jest w contracts/.

### Pomiar zapytań i odpowiedzi HTTP — SCRUM-123

Na lokalnej syntetycznej bazie PostgreSQL `fleet_flow_test_benchmark` uruchom
migracje (`alembic upgrade head`). Z katalogu `backend` uruchom oba narzędzia
z `TEST_DATABASE_URL` wskazującym tę bazę i `PYTHONPATH=.`.

```shell
python tools/benchmark_fleet_queries.py
python tools/benchmark_fleet_http.py
```

Każdy pomiar ma rozgrzewkę i 20 kolejnych prób dla 100, 1 000 oraz 10 000
syntetycznych pojazdów. Pierwszy raport porównuje SQL historycznego i obecnego
odczytu w tym samym procesie. Drugi mierzy p95 oraz bajty JSON osobno dla listy
25 pojazdów, mapy i podsumowania, z prawdziwym HTTP na loopback. Do porównania
na hostingu trzeba dodać kompresję, profil sieci i współbieżność użytkowników.

## Ręczne odświeżanie floty — SCRUM-150

`GET /api/v1/fleet/refresh` zwraca `enabled`, `running`, `server_time`,
`next_allowed_at` i `retry_after_seconds`. Działa też przed pierwszym odczytem
floty. Wymaga zalogowania; odpowiedzi nie są cache'owane w przeglądarce.

`POST /api/v1/fleet/refresh` wymaga również zaufanego `Origin`. Może go użyć
każda zalogowana rola, w tym viewer: operacja odczytuje źródło i aktualizuje
wspólny cache, nie zmienia danych u dostawcy. Używa tego samego `sync_once`,
blokady konta i stanu limitera co automatyczny worker. Domyślny odstęp wynosi
60 s według `SYNC_INTERVAL_SECONDS`; backoff dostawcy może go wydłużyć.
Kliknięcia z innych kart/użytkowników nie omijają tego odstępu.

Odpowiedź HTTP 200 zawiera metadane dostępności oraz wynik polecenia:
`updated`, `cooldown`, `busy`, `failed` lub `disabled`. To wynik próby,
nie obietnica nowego pomiaru GPS. Dla `cooldown`/`busy`/`disabled` nie ma nowego
odczytu dostawcy. Niespodziewany błąd zwraca bezpieczne 503. Przycisk nie włącza
źródła: wymaga istniejącego `SYNC_ENABLED=true` i konfiguracji backendu.

Status trwającej synchronizacji pochodzi z odczytu `pg_locks`, bez zajmowania
blokady, która mogłaby opóźnić workera. Sposób identyfikacji klucza bigint:
[dokumentacja PostgreSQL](https://www.postgresql.org/docs/17/view-pg-locks.html).
[Scenariusze i wyniki weryfikacji](../docs/qa/SCRUM-150.md).

## Preferencje konta — SCRUM-91

`GET` i `PUT /api/v1/preferences/dashboard` oraz `/api/v1/preferences/vehicles`
wymagają sesji. Każdy moduł ma osobny rekord dla użytkownika. Odpowiedź zawiera
`module`, `version`, `value` i `updated_at`; zapis przyjmuje
`{"version": <odczytana wersja>, "value": <ustawienia>}`. Zmiana zapisanej już
wersji wymaga bieżącej wartości `version`; niezgodność zwraca `409
VERSION_CONFLICT`, bez cichego nadpisania. Wartości są walidowane według modułu.

Pulpit przechowuje widoczne widgety i układy desktop/compact. Pojazdy przechowują
układ kafelków, sortowanie, filtry wyszukiwania/statusu i limit strony. Migracja
`0006` tworzy tabelę `account_preferences`. Import zastanych ustawień
`localStorage` wykonuje się dopiero po wyborze użytkownika i wyłącznie przy
wersji 0, więc nie zastępuje istniejących preferencji konta.

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

## Metryki i bezpieczny identyfikator korelacji (SCRUM-114)

- Każde żądanie HTTP oraz cykl workera synchronizacji posiada ograniczony
  identyfikator korelacji (`X-Correlation-ID`, akceptowane `^[A-Za-z0-9._-]{8,64}$`,
  w przeciwnym razie losowe `uuid4().hex`), zwracany w nagłówku odpowiedzi,
  w `error.correlation_id` dla błędów `5xx` oraz w bezpiecznych logach błędów `5xx` i synchronizacji.
- `GET /api/v1/observability/metrics` (`?format=json` lub `?format=prometheus`)
  wymaga uwierzytelnionego konta z rolą `admin` (`403 FORBIDDEN` dla `editor`
  i `viewer`). Udostępnia `api_up`, liczniki i `p95` żądań HTTP po szablonach tras,
  stan puli połączeń DB, wiek i kody synchronizacji WEBFLEET, wolne miejsce na dysku,
  stan znaczników backupu/odtworzenia (`not_configured` z `deferred_to: "SCRUM-84"`
  gdy `FLEET_FLOW_BACKUP_STATE` jest puste), dni ważności certyfikatu TLS
  (`TLS_CERT_PATH`, progi `TLS_WARNING_DAYS=21` i `TLS_CRITICAL_DAYS=7`) oraz
  zanonimizowane kody zdarzeń auth i SMTP.
- Szczegóły granic prywatności, uprawnień i retencji:
  [SCRUM-114 observability](../docs/security/SCRUM-114-observability.md).
