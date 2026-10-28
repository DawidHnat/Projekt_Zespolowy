# SCRUM-95 — wymagane bramki bezpieczeństwa

Baza PR: SCRUM-98 / PR39 → SCRUM-83 / PR37 → SCRUM-26 / PR30. Należy scalać
po review w tej kolejności i przestawiać kolejne PR na main z ponowieniem CI.
Nie włączono automerge ani płatnych usług.

## Zakres i progi

Required CI zależy od frontend, dwóch wersji backendu, obrazu, E2E oraz trzech
jobów bezpieczeństwa. Niepowodzenie, anulowanie lub pominięcie któregokolwiek
z nich daje czerwony Required CI. Nie zmieniono nazwy wymaganego checka.

* Dependency security: dependency review zmian PR od poziomu High, pełny
  `npm audit --audit-level=high` (także devDependencies) oraz pip-audit wszystkich
  zainstalowanych zależności aplikacji i testów w osobnym venv. pip-audit blokuje
  każdą znaną podatność; awaria skanera/źródła danych także zatrzymuje gate.
* Source security: Semgrep CE lokalnie, osiem przeglądalnych reguł Python/TS/React
  w `.github/security/semgrep.yml`: dynamiczny kod, shell, interpolowany SQL,
  niebezpieczna deserializacja, wyłączone TLS i surowy HTML. ERROR blokuje.
  `--strict` blokuje wadliwe reguły, `--disable-nosem` zapobiega cichej supresji.
  To ograniczony zestaw reguł, nie kompletny audyt ASVS ani analiza między plikami.
* Secret security: Gitleaks pełnej historii **HEAD**, bez sieci i z redakcją 100%.
  Celowo nie używa `--all`: odrębna niescalana gałąź dowodowa ma zawierać atrapę
  sekretu i nie może zatruwać wyników poprawnych gałęzi. Każde znalezisko blokuje.
* Backend image: Trivy bada zbudowany obraz, bez uruchamiania aplikacji,
  oraz IaC w infra (w tym nazwę backend.Dockerfile). Każde High/Critical blokuje,
  również bez dostępnej poprawki. Skan IaC działa także po nieudanym skanie obrazu.

Dependabot proponuje cotygodniowe aktualizacje npm, pip, narzędzi skanowania,
Actions i obrazu. Aktualizacje wymagają takich samych PR/review/CI. Wszystkie
Actions mają pełne SHA odczytane z oficjalnych repozytoriów 28.10.2026. Trivy
0.76.1 i Gitleaks 8.30.1 mają przypięte digesty OCI; wersje pip-audit/Semgrep są
w requirements narzędzi. Nie używa się tokena platformy Semgrep, zdalnych reguł,
telemetrii, trace ani płatnego API. SCA pobiera publiczne dane pakietów/CVE.

## Usunięte problemy

pip-audit wykrył podatne certifi 2026.7.22 i stary pip środowiska testowego.
certifi zaktualizowano do 2026.10.23, a bootstrap venv do pip 26.2.2.
Trivy wykrył High/Critical w starej bazie Debian slim. Nawet aktualna baza miała
niezałatane znaleziska, więc zamiast wyłączać kontrole zmniejszono obraz:
Python 3.13 Alpine 3.24.3 z oficjalnym digestem, aktualne certifi, bez runtime pip.
UID 10001 i ścieżki aplikacji pozostają zgodne z Compose. Nowa baza wymaga
zwykłego odbioru rollout/rollback przed wdrożeniem; w tym zadaniu nie wdrażano VPS.

## Weryfikacja developerska 28.10.2026

* Ruff check i format --check PASS, 124 pytest PASS na host Python 3.12.
* 124 pytest PASS **wewnątrz** jednorazowego obrazu Python 3.13 Alpine, w tym
  migracje i PostgreSQL na osobnej syntetycznej bazie. Tylko w testowym kontenerze
  tymczasowo zainstalowano pytest; finalny obraz nie zawiera pip.
* Finalny obraz: import FastAPI, Argon2 hash/verify i UID 10001 PASS.
* pip-audit po poprawce: zero znanych podatności. npm audit: zero High/Critical.
* Semgrep: osiem reguł, 98 plików docelowych, zero znalezisk i błędów reguł.
* Gitleaks: 88 commitów / 1.86 MB, zero znalezisk; wartości redagowane.
* Trivy finalnego obrazu: zero High/Critical OS i Python; IaC zero High/Critical.

Wynik jest ważny dla bazy CVE z dnia odczytu. Przyszłe nowe CVE mogą zablokować CI;
nie jest to uzasadnienie dla wyłączenia kontroli.

## False positives i wyjątki

1. Powtórz wynik przypiętym narzędziem. Zapisz tylko ID reguły/CVE, wersję,
   ścieżkę/zakres, osiągalność i uzasadnienie; nie wklejaj wartości sekretu.
2. Usuń przyczynę, zaktualizuj pakiet albo ogranicz powierzchnię obrazu.
3. Gdy konieczny jest wyjątek, osobny PR musi wskazywać konkretne ID/zakres,
   dowód false positive lub zaakceptowane ryzyko, osobę odpowiedzialną,
   datę wygaśnięcia i zgłoszenie usunięcia. Review wykonuje inny developer;
   wpływ na dane zatwierdza ich właściciel. Wygasły wyjątek nie uprawnia do bypassu.
4. Nie dodawaj `continue-on-error`, globalnego ignore, `--ignore-unfixed`,
   `nosemgrep`, szerokich allowlist ani omijania Required CI.

Na tej gałęzi nie wprowadzono wyjątków. Nieznany stan zabezpieczenia to BLOCKED.

## Read-back main i pozostałe warunki odbioru

28.10.2026 odczyt `branches/main` potwierdza protected=true i wymagany
`Required CI`, app_id 15368, enforcement everyone. Pełny endpoint
`branches/main/protection` zwraca 404, lista rulesetów jest pusta. Z tych danych
**nie można** potwierdzić niezależnego approval, strict/up-to-date ani bypassów.
Nie zmieniano ochrony. Pełny odczyt pozostaje BLOCKED dla właściciela repozytorium
DawidHnat lub uprawnionego administratora: potrzebny datowany snapshot całych
reguł oraz dowód czerwonego wymaganego checka na kontrolnym niescalanym PR.

Finalny odbiór wymaga także niezależnego review/QA, zielonego CI na bieżącym SHA,
dowodów każdej klasy negatywnej i odbioru zmiany bazy obrazu. Późniejsze 107/108
muszą wejść w tę samą wymaganą kontrolę; ten PR nie udaje ich implementacji.
