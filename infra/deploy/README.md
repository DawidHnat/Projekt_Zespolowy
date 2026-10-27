# Wdrożenie rozwojowe — SCRUM-18

Stos pozostaje uzgodniony: React/TypeScript, FastAPI i PostgreSQL. Frontend
buduje się w GitHub Actions, backend w obrazie Pythona na VPS. Caddy obsługuje
HTTPS i przekazuje `/api` do niepublicznego backendu. Baza nie publikuje portu.
Synchronizacja WEBFLEET jest wyłączona w tym przyroście.

Cykliczny szyfrowany backup poza VPS i izolowane sprawdzenie odtworzenia opisuje
[SCRUM-84](../backup/README.md). Wymaga osobnej konfiguracji storage i aktywacji
timerów; lokalny dump przy deployu nie zastępuje tej kopii.

20 października 2026 przetestowano na VPS wydanie `e30cadd` z PR #23 pod
`https://vps-9171bf52.vps.ovh.net/`. Przeszły także ponowne wdrożenie, kopia
zmigrowanej bazy i próba jej odtworzenia. Trzy sekrety Actions są zapisane,
a dedykowany klucz odrzuca polecenia inne niż `deploy <SHA>`. Zwykłe konta SSH
zespołu zachowują dotychczasowy dostęp.

Nie jest to jeszcze dowód wdrożenia aktualnego `main`. PR wymaga review,
a właściciel musi włączyć ochronę gałęzi. Domena `fleet-flow.pl` nadal wskazuje
parking OVH; tymczasowo `DEV_PUBLIC_URL` i `APP_DOMAIN` wskazują hostname VPS.
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
   Do tego czasu można używać istniejącego hostname `vps-9171bf52.vps.ovh.net`;
   ustaw go zgodnie w `DEV_PUBLIC_URL` i `APP_DOMAIN`.
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

## Ochrona main — wykonuje właściciel repozytorium

Repozytorium jest prywatne i należy do osobistego konta `DawidHnat`.
Potrzebny jest plan właściciela obsługujący ochronę, np. GitHub Pro z aktywnego
Student Developer Pack. Plan współpracownika nie rozszerza planu tego repo.
Uprawnienia zwykłego współpracownika nie wystarczają do zmiany ochrony.

Po udanym runie nowego CI właściciel stosuje regułę z
[main-protection.json](main-protection.json):

```bash
gh api --method PUT repos/DawidHnat/Projekt_Zespolowy/branches/main/protection \
  --input infra/deploy/main-protection.json
```

W UI odpowiednikiem jest wymaganie PR, jednego approval, aktualnych zielonych
checks oraz opcji **Do not allow bypassing the above settings**. Nie dodawaj
wyjątku dla administratora, osób ani aplikacji. Nie włączaj automerge.

Pierwsze połączenie konfiguracji z `main` także wymaga review. Po tym runie
ochrona ma wymagać dokładnie `Required CI`, a nie starych nazw osobnych workflowów.

## HTTP z zadania i HTTPS aplikacji

Polecenie kursowe używa `curl -s http://…` bez `-L`; zwykłe przekierowanie do
HTTPS nie udostępniłoby treści zawierającej SHA. Dlatego HTTP `/` zwraca
publiczną stronę wersji z linkiem do aplikacji HTTPS. Nie udostępnia formularza
logowania, API ani danych floty. Zarówno ona, jak i strona aplikacji HTTPS
otrzymują to samo siedmioznakowe SHA podczas budowy.

## Dowody do oddania — tylko rzeczywiste wyniki

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
