# Wdrożenie rozwojowe — SCRUM-18

Stos pozostaje uzgodniony: React/TypeScript, FastAPI i PostgreSQL. Frontend
buduje się w GitHub Actions, backend w obrazie Pythona na VPS. Caddy obsługuje
HTTPS i przekazuje `/api` do niepublicznego backendu. Baza nie publikuje portu.
Synchronizacja WEBFLEET jest wyłączona w tym przyroście.

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

Po pushu do `main` i zielonym CI job wdrożenia pobiera zbudowany artefakt tego
samego commita, dodaje sekret środowiska dopiero w jobie deploymentu i wysyła
go przez SSH. Sekret nie trafia do publicznego artefaktu Actions ani cache.
PR nie uruchamia deploymentu i nie dostaje sekretów wdrożenia.

Na VPS powstaje oddzielne wydanie w `/opt/fleet-flow/releases/`. Skrypt robi
kopię bazy oraz rzeczywistą próbę odtworzenia do tymczasowej bazy, uruchamia
migracje i usługi, a potem sprawdza HTTP z SHA i gotowość API przez HTTPS.
Dopiero wtedy podmienia wskaźnik `current`. Przy błędzie próbuje przywrócić
poprzednią aplikację i jej środowisko; migracji bazy nie cofa automatycznie.
Zmiany niezgodne ze starym schematem wymagają osobnego planu migracji.

## Jednorazowe przygotowanie przez administratora

1. Skieruj rekord A `fleet-flow.pl` na `57.129.179.53`. Rekord AAAA dodaj tylko
   z poprawnym IPv6 VPS. Zachowaj rekordy poczty, TXT i weryfikacji domeny.
   Domena kanoniczna to `fleet-flow.pl`; po wdrożeniu konfiguracji SCRUM-67
   `www.fleet-flow.pl` i `vps-9171bf52.vps.ovh.net` przekierowują do niej.
   Alias `www` musi mieć rekord A tego samego VPS. Powrót do hostname VPS
   jako domeny kanonicznej wymaga poprzedniego wydania Caddyfile.
2. Na VPS zainstaluj Docker z `docker compose`, Python 3.12+ i curl ze
   wspieranych pakietów. Budowa obrazu wymaga też wtyczki Buildx.
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
