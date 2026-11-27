# Wdrożenie rozwojowe — SCRUM-18

Stos pozostaje uzgodniony: React/TypeScript, FastAPI i PostgreSQL. Frontend
i obraz backendu buduje GitHub Actions. Caddy obsługuje
HTTPS i przekazuje `/api` do niepublicznego backendu. Baza nie publikuje portu.
Synchronizacja WEBFLEET domyślnie pozostaje wyłączona. Compose respektuje
`SYNC_ENABLED` z prywatnego środowiska; nie nadpisuje go stałym `false`.
[Runbook SCRUM-64](../../docs/qa/SCRUM-64.md) opisuje canary, pomiar aktualności
i rollback. Kod nie stanowi potwierdzenia uruchomienia źródła na VPS.

Cykliczny szyfrowany backup poza VPS i izolowane sprawdzenie odtworzenia opisuje
[SCRUM-84](../backup/README.md). Wymaga osobnej konfiguracji storage i aktywacji
timerów; lokalny dump przy deployu nie zastępuje tej kopii.

20 października 2026 przetestowano na VPS wydanie `e30cadd` z PR #23 pod
`https://vps-9171bf52.vps.ovh.net/`. Przeszły także ponowne wdrożenie, kopia
zmigrowanej bazy i próba jej odtworzenia. Trzy sekrety Actions są zapisane,
a dedykowany klucz odrzuca polecenia inne niż `deploy <SHA>`. Zwykłe konta SSH
zespołu zachowują dotychczasowy dostęp.

Historyczny test z 20 października nie jest dowodem aktualnego wydania.
3 listopada 2026 główna domena `fleet-flow.pl` została skierowana na VPS;
potwierdzono HTTPS i gotowość API na wersji `4ce144e`. `DEV_PUBLIC_URL`,
`APP_DOMAIN`, CORS i istniejący sekret Actions mają już nową domenę.
Przekierowania aliasów z tego PR wymagają review i wdrożenia. Pełny stan,
odbiór oraz rollback opisuje [SCRUM-67](../../docs/qa/SCRUM-67.md).
Nie ma domyślnych kont aplikacji. WEBFLEET pozostaje wyłączony.

## CI i publikacja

`CI` działa dla **każdego PR**, także zmieniającego wyłącznie dokumentację,
oraz każdego pushu do `main`. Nie ma filtrów `paths`. Kontrola `Required CI`
przechodzi tylko po udanej budowie frontendu, obrazu backendu i testach obu
wersji Pythona.
Wymagaj jej w ochronie `main`; nazwy tej kontroli nie zmieniaj bez aktualizacji
reguły. CI nie korzysta z kont WEBFLEET, SMTP ani danych klientów.

Po pushu do `main` i zielonym CI job wdrożenia pobiera frontend i przeskanowany
obraz backendu dla tego samego commita. Dołącza plik środowiska dopiero w jobie
deploymentu i przesyła wydanie przez SSH. Sekret nie trafia do publicznego
artefaktu Actions ani cache.
PR nie uruchamia deploymentu i nie dostaje sekretów wdrożenia.

Na VPS powstaje oddzielne wydanie w `/opt/fleet-flow/releases/`. Skrypt robi
kopię bazy oraz rzeczywistą próbę odtworzenia do tymczasowej bazy, uruchamia
migracje i usługi, a potem sprawdza HTTP z SHA i gotowość API przez HTTPS.
Dopiero wtedy podmienia wskaźnik `current`. Przy błędzie próbuje przywrócić
poprzednią aplikację i jej środowisko; migracji bazy nie cofa automatycznie.
Zmiany niezgodne ze starym schematem wymagają osobnego planu migracji.

### Odbiór obrazu i aktualizacja odbiornika na VPS (SCRUM-100)

Artefakt `backend-image-<SHA>` zawiera archiwum obrazu, jego SHA-256, identyfikator
obrazu Dockera, SBOM CycloneDX oraz metadane przebiegu CI i commita. Odbiornik
sprawdza sumę archiwum i identyfikator po `docker load`. Po starcie porównuje
identyfikator uruchomionego kontenera z tym samym plikiem z CI, a log wypisuje
SHA wydania i identyfikator. Archiwum po załadowaniu jest usuwane. Lokalny obraz
i manifesty wydania należy zachować na czas określony dla rollbacku.

Przed aktywacją uzgodnij okno, wolne miejsce na przyjęcie archiwum i obraz,
dostęp do artefaktów Actions oraz kopię bieżącego odbiornika. W tym samym oknie
administrator instaluje `deploy.sh` i `load_backend_image.sh` z zatwierdzonego
commita przez `bootstrap.sh` i uruchamia pierwsze zgodne wydanie. Nowy odbiornik
wymaga nowych plików i odrzuci archiwum starszego workflow. W razie wycofania
pierwszej zmiany przywróć poprzedni odbiornik przed uruchomieniem starszego
workflow. Zwykły automatyczny rollback skryptu używa zachowanego obrazu
poprzedniego wydania. Przetestuj rollback po migracji na kopii przed aktywacją.

Protokół odbioru łączy commit, run CI, SBOM, wynik skanu, SHA archiwum,
identyfikator obrazu z joba `Backend image`, identyfikator kontenera na VPS i
publiczny smoke tego wydania. Właściciel operacyjny potwierdza okno aktywacji.

### Wycofanie aplikacji po migracjach kartoteki i historii (SCRUM-18 / SCRUM-119)

Próba syntetyczna 20.11.2026 objęła starszy backend `dff6240` i migracje
0011–0012 z `a8af891`. Po rozszerzeniu schematu starsze API nadal potwierdziło
gotowość, logowanie, odczyt floty i zapisanej historii. Te same odczyty przeszły
po odtworzeniu kopii schematu 0010 do osobnej bazy.

Stary zapis kartoteki może przejść na rozszerzonym schemacie bez ustawienia
własności konkretnego pola. W próbie taki zapis zostałby zastąpiony przez
następną synchronizację nowej aplikacji. Przy powrocie do wersji sprzed 0011
operator wstrzymuje zapisy kartoteki i synchronizację do czasu ponownego
wdrożenia albo uzgodnionego odtworzenia kopii. Jeśli stara wersja już przyjęła
zapisy, operator najpierw je identyfikuje i uzgadnia ich zachowanie lub zakres
odtworzenia z PO. Readiness i poprawny odczyt nie rozstrzygają zachowania zmian.

### Walidacja aktualności wydania i jawny rollback (SCRUM-137)

Przed rozpakowaniem artefaktu i jakąkolwiek zmianą stanu serwera (`releases/`,
`runtime.env`, `current`) skrypt `deploy.sh` uruchamia walidator
`validate_release.py` względem bare cache `/opt/fleet-flow/shared/repo.git`:

- Pierwsze wdrożenie oraz każde kolejne wymagają udanego `git fetch` (w trybie
  online), istnienia docelowego SHA i jego przynależności do gałęzi `main`.
  Błąd `git fetch` przerywa wdrożenie z kodem niezerowym i nie ufa staremu cache.
- Ponowienie tego samego SHA co `/opt/fleet-flow/current/commit` jest dozwolone
  (idempotentny retry).
- Starszy commit (przodek aktywnego wydania, np. ponowienie historycznego runu CI)
  lub rozbieżna historia są odrzucane przed rozpakowaniem archiwum.
- **Aktywacja na VPS:** po odbiorze i scaleniu PR administrator aktualizuje
  skrypty serwerowe przez ponowne wykonanie `sudo bash bootstrap.sh /ścieżka/do/klucza-CI.pub`
  (instaluje `/usr/local/libexec/fleet-flow/validate_release.py`, `deploy.sh` i
  `ssh-dispatch.sh`). Dowód odrzucenia przestarzałego przebiegu zbiera się w
  izolowanym symulatorze (`python3 tools/test_validate_release.py`), bez cofania
  działającego VPS.
- **Jawny rollback:** celowe przywrócenie wcześniejszego wydania wymaga najpierw
  weryfikacji zgodności schematu PostgreSQL (migracje Alembic między bieżącym a
  docelowym SHA oraz kopia bazy), a następnie jawnego wywołania na serwerze z
  flagą `--allow-rollback` (lub `FLEET_FLOW_ALLOW_ROLLBACK=1`). Standardowy klucz
  SSH CI nie przekazuje tej flagi automatycznie.

## Jednorazowe przygotowanie przez administratora

1. Skieruj rekord A `fleet-flow.pl` na `57.129.179.53`. Rekord AAAA dodaj tylko
   z poprawnym IPv6 VPS. Zachowaj rekordy poczty, TXT i weryfikacji domeny.
   Domena kanoniczna to `fleet-flow.pl`; po wdrożeniu konfiguracji SCRUM-67
   `www.fleet-flow.pl` i `vps-9171bf52.vps.ovh.net` przekierowują do niej.
   Alias `www` musi mieć rekord A tego samego VPS. Powrót do hostname VPS
   jako domeny kanonicznej wymaga poprzedniego wydania Caddyfile.
2. Na VPS zainstaluj Docker z `docker compose`, Python 3.12+ i curl ze
   wspieranych pakietów.
   Zachowaj działające konta SSH zespołu.
3. Wygeneruj osobny klucz ED25519 dla Actions **poza repozytorium**. Nie używaj
   kluczy prywatnych członków zespołu. Klucz CI ma dostęp do wdrażania aplikacji;
   należy traktować go jako sekret administracyjny.
4. Po przeglądzie prześlij katalog `infra/deploy` i publiczny klucz CI na VPS.
   Z konta `ubuntu` wykonaj `sudo bash bootstrap.sh /ścieżka/do/klucza-CI.pub`.
   Skrypt przygotowuje `fleetdeploy`, odbiornik i ograniczony rozkaz SSH.
5. Zachowując regułę OpenSSH, dopuść TCP 80 i 443 w UFW. Pozostałe porty aplikacji
   i bazy pozostają niepubliczne. Nie włączaj niepotrzebnych portów Dockera.
6. W ustawieniach repozytorium / Actions lub środowiska `development` zapisz:

| Sekret | Zawartość |
| --- | --- |
| `DEV_SSH_PRIVATE_KEY` | Prywatny dedykowany klucz CI ED25519 bez interaktywnego hasła. |
| `DEV_SSH_KNOWN_HOSTS` | Wpis OpenSSH dla `57.129.179.53` sprawdzony z odciskiem hosta w KVM; nie wynik ślepego `ssh-keyscan`. |
| `DEV_RUNTIME_ENV` | Uzupełniony prywatnie [runtime.env.example](runtime.env.example), ze stałym hasłem i URL bazy. |

Opcjonalne variables: `DEV_HOST` (domyślnie IP VPS), `DEV_PUBLIC_URL`
(domyślnie `https://fleet-flow.pl`) oraz publiczny token `MAPBOX_PUBLIC_TOKEN`.
Host z `DEV_PUBLIC_URL` musi zgadzać się z `APP_DOMAIN` w sekrecie. Brak tokenu
Mapbox pozostawia istniejący jawny pusty stan mapy. Żadnych rzeczywistych `.env`
nie wysyłamy do repozytorium. Hasła bazy nie generujemy ponownie przy każdym runie.

Nie ma domyślnych kont aplikacji ani haseł. Administrator tworzy konta przez
istniejące interaktywne `python -m app.manage create-user` w kontenerze API,
według instrukcji backendu. Nie publikuje haseł w PR ani w logu Actions.

### Konfiguracja integracji na kolejnych wdrożeniach

Zapisz publiczny token Mapbox jako zmienną repozytorium
`MAPBOX_PUBLIC_TOKEN`. Frontend odczytuje ją podczas budowy.

W środowisku Actions `development` zapisz prywatny sekret
`DEV_WEBFLEET_ENV` w formacie dotenv. Zawiera wyłącznie
`WEBFLEET_ACCOUNT`, `WEBFLEET_USERNAME`, `WEBFLEET_PASSWORD` i
`WEBFLEET_API_KEY`. Workflow dodaje je do pliku środowiska API przy każdym
wdrożeniu. Ustawienia domeny i bazy nadal pochodzą z `DEV_RUNTIME_ENV`.
Jeśli osobny sekret jest pusty, workflow korzysta z ustawień integracji
zapisanych w dotychczasowym `DEV_RUNTIME_ENV`.

Zmienna środowiska Actions `DEV_WEBFLEET_SYNC_ENABLED` ma domyślnie wartość
`false` dla osobnego sekretu. Po odbiorze SCRUM-64 operator może ustawić
`true` i wdrożyć zatwierdzoną wersję. Powrót do `false` zatrzymuje kolejne
cykle po wdrożeniu bez czyszczenia zapisanych danych.

Po uzgodnieniu uruchomienia SMTP administrator zapisuje konfigurację w
`/opt/fleet-flow/shared/smtp.raw.env` na VPS. Plik należy do `root:root` i ma
uprawnienia `0600`. Każde ustawienie wpisz w postaci `KLUCZ=wartość`.
Docker Compose 2.30 lub nowszy przekazuje wartość dosłownie, łącznie ze
znakami `$` i cudzysłowami należącymi do hasła. Dotychczasowy opcjonalny
`smtp.env` zachowuje składnię dotenv. Ustawienia z `smtp.raw.env` mają
pierwszeństwo dla tych samych kluczy. Po zmianie pliku odtwórz kontener API.
[Konfiguracja i diagnostyka SMTP](../../backend/README.md#poczta-ovh--test-logowania-bez-wysyłki) ·
[Format plików Compose](https://docs.docker.com/reference/compose-file/container-spec/#format).

## Ochrona main — wykonuje właściciel repozytorium

Repozytorium jest publiczne. Odczyt 10.11.2026 pokazuje aktywną ochronę
`main` i wymagany `Required CI`; konto jczaja51 ma push, bez admin/maintain.
Pełną konfigurację i zmianę reguły potwierdza właściciel Dawid Hnat.

Po sprawdzeniu PR SCRUM-127 i zielonym runie nowych jobów właściciel otwiera
istniejącą regułę `main` w Settings → Branches (albo istniejący ruleset).
Zachowuje wszystkie dotychczasowe wymagania, w tym `Required CI`, wymagany
PR/approval, aktualność gałęzi, rozmowy i zakaz bypassu/force push/deletion.
Dodaje dokładne konteksty **Backend (3.13)** (pytest) i **Lint** (Ruff).
Nie dodaje deploymentu ani smoke jako wymaganego checku PR.
Nie zastępuje całej reguły szablonem: pełne ustawienia obecnej reguły mogą
być szersze od [main-protection.json](main-protection.json), który podaje
minimalny docelowy zestaw, a nie potwierdzenie aktywacji.

Właściciel zapisuje wynik z klonu zespołu:

```bash
gh api 'repos/{owner}/{repo}/branches/main' --jq '.protection.required_status_checks.contexts[]'
# Dla rulesetu zamiast klasycznej ochrony:
gh api 'repos/{owner}/{repo}/rules/branches/main' --jq '.[] | select(.type == "required_status_checks") | .parameters.required_status_checks[].context'
```

Po PR SCRUM-127 `Required CI` wymaga również `Lint`, a deployment jawnie
wymienia testy i lint w `needs`. Osobny job `Post-deploy smoke` po deployment
sprawdza publiczne strony wersji HTTP i HTTPS oraz readiness API. Wymaga
SHA bieżącego przebiegu; przy niezgodności workflow kończy się błędem.
Całe push-workflow main ma `cancel-in-progress: false`, więc następne
wdrożenie nie wyprzedza smoke bieżącego przebiegu. Weryfikator nie korzysta
z kont aplikacji i nie zapisuje odpowiedzi API ani sekretów w logu.
Lokalne sprawdzenie bez deploymentu:

```bash
python3 tools/verify_deployment.py --sha "$(git rev-parse origin/main)" \
  --status-origin http://57.129.179.53 --app-origin https://fleet-flow.pl
```

Na lokalnym Pythonie macOS bez skonfigurowanego CA można wskazać standardowy
magazyn przez `SSL_CERT_FILE=/etc/ssl/cert.pem`; weryfikacji TLS nie wyłączamy.
[Materiały do oddania Sprintu 2](../../docs/SPRINT_2_SUBMISSION.md).

## HTTP z zadania i HTTPS aplikacji

Polecenie kursowe używa `curl -s http://<IP>/` bez `-L`; dlatego HTTP po IP
nadal zwraca publiczną stronę wersji z linkiem do aplikacji HTTPS. Nie
udostępnia formularza logowania, API ani danych floty. HTTP po nazwach domeny,
`www` i starego hostname przekierowuje 308 na domenę kanoniczną, zachowując
ścieżkę i parametry. HTTPS aliasów robi to samo. Strona wersji i aplikacja
otrzymują to samo siedmioznakowe SHA podczas budowy.

## Pełny odbiór wydania MVP — SCRUM-18

Pojedyncze health checki i strona z SHA są tylko częściowymi dowodami wdrożenia.
Odbiór wymaga wypełnienia jednego śladu dla dokładnego wydania i środowiska,
niezależnego review, wymaganych QA oraz dowodów dla każdej bramy P0.
Stosuj [protokół odbioru MVP](MVP_RELEASE_PROTOCOL.md): brak dowodu oznacza
`BLOCKED`, błędny wynik `FAIL`, a brak digestu nie może być ukrywany deklaracją
zgodności. Protokół określa wymagania, nie potwierdza wykonania kontroli ani
gotowości bieżącego wydania.

## Dowody do oddania — tylko rzeczywiste wyniki

Poniższe polecenia potwierdzają tylko wybrane elementy: publiczny SHA i gotowość
API. Nie stanowią samodzielnego odbioru. Zbieraj też pozostałe dowody zgodnie z
[pełnym protokołem SCRUM-18](MVP_RELEASE_PROTOCOL.md).

Po scaleniu i zakończeniu jobu wdrożenia:

```bash
git fetch origin
curl -fsS http://57.129.179.53/ | grep -F "$(git rev-parse --short=7 origin/main)"
curl -fsS https://fleet-flow.pl/api/health/ready
```

Właściciel sprawdza odrzucenie pushu z **nowym** commitem. Samo „Everything
up-to-date” nie potwierdza ochrony. Próby nie wykonujemy, dopóki reguła nie
jest włączona i odczytana z API. Użyj osobnego tymczasowego klonu, by nie
zmieniać bieżącej pracy; przygotuj pusty commit, następnie uruchom dokładnie
`git push origin main` i zapisz rzeczywiste odrzucenie z konta właściciela.

Osobny demonstracyjny PR ma mieć celowy błąd składni w TypeScript, czerwone
`Frontend build` i `Required CI` oraz blokadę scalenia przez ochronę. Nie scalaj
tego PR. Sam draft bez ochrony gałęzi nie dowodzi wymuszenia CI.

Dowody zawierają datę, numer PR, URL runu i sprawdzone SHA. Nie wpisuj do
oddania zmyślonego wyniku, planowanej konfiguracji ani starego SHA.

Źródła: [ochrona gałęzi](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches),
[pomijanie workflowów](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs),
[automatyczny HTTPS Caddy](https://caddyserver.com/docs/automatic-https).
