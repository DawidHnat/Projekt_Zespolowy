# Oddanie 4.2 — Przegląd Sprintu 2 i bramy jakości

**Materiał roboczy, nie gotowe oddanie.** Stan 10.11.2026: Review Sprintu 2
jeszcze się nie odbyło; brak potwierdzonego pełnego DoD całej Story.
Technika: [SCRUM-127](https://fleet-flow.atlassian.net/browse/SCRUM-127).

## Kolejność dokończenia

1. Dawid lub Nazarewicz przegląda PR techniczny SCRUM-127; po approval zmiana
   trafia przez PR do main. Nazw istniejących checków nie zmieniać.
2. Dawid dodaje `Lint` i `Backend (3.13)` jako wymagane checki, zachowując
   `Required CI` i wszystkie istniejące zabezpieczenia. Konta współpracownika
   bez admin nie mogą tego wykonać. [Szczegóły](../infra/deploy/README.md#ochrona-main--wykonuje-właściciel-repozytorium).
3. Zebrać dwa jawnie oznaczone PR-y **NIE SCALAĆ**: błąd Ruff oraz rzeczywiście
   czerwony test jednostkowy. Zachować ID runów i końcowe wyniki jobów.
   Dawny PR #24 to błąd składni/budowy; sam nie dowodzi czerwonego testu.
4. Poczekać na udany push-run main z osobnym `Post-deploy smoke`. Test po
   wdrożeniu musi dotyczyć SHA **tego runu**, nie przypadkowej późniejszej wersji.
5. Marcel i niezależny reviewer odbierają wybraną całą Story. Jakub prowadzi
   [Review](SPRINT_2_REVIEW.md), zapisuje feedback oraz rzeczywiste retro.
6. PO rozlicza Sprint 2 i uruchamia istniejący `FF Sprint 3 - dane i konta`
   z celem i zgłoszeniami SCRUM-128/129. Nie tworzy nowego sprintu ani nie
   zaczyna równoległego tylko dla zrzutu.

## Polecenia do zebrania po scaleniu i odbiorze

Uruchamiać w klonie repozytorium zespołu. Kopiować rzeczywiste wyniki,
bez wpisywania przyszłego `success`.

```bash
git fetch origin
curl -s http://57.129.179.53/ | grep -c "$(git rev-parse --short=7 origin/main)"
gh api 'repos/{owner}/{repo}/branches/main' --jq '.protection.required_status_checks.contexts[]'
# Alternatywnie tylko gdy stosowany jest ruleset:
gh api 'repos/{owner}/{repo}/rules/branches/main' --jq '.[] | select(.type == "required_status_checks") | .parameters.required_status_checks[].context'
# ID runów dwóch PR-ów dowodowych:
gh run list --branch NAZWA_GALEZI --event pull_request --limit 1
gh run view ID --json jobs --jq '.jobs[] | "\(.name) \(.conclusion)"'
# Z wdrożonego main, nie z gałęzi PR:
git show origin/main:.github/workflows/ci.yml
# Wyciąć blok deploy z needs oraz osobny blok smoke.
gh run list --branch main --event push --limit 1
gh run view ID_MAIN --json jobs --jq '.jobs[] | "\(.name) \(.conclusion)"'
gh run view ID_MAIN --log | grep 'PASS deployed SHA'
```

Oczekiwane dowody po dokończeniu: `Lint failure` dla PR lintu;
`Frontend build failure` z błędem **npm test**, a `Deploy development server
skipped` dla PR testu; na main success testów, lintu, deploymentu i smoke.
`Required CI` może być failure w obu celowo czerwonych PR-ach — to prawidłowe
odrzucenie zależności, nie usterka do obchodzenia.

## Zweryfikowany punkt wyjścia — 10.11.2026

- Serwer <http://57.129.179.53/>: grep SHA `5b5fceb` wypisał `1` po fetch.
- Nowy weryfikator uruchomiony ręcznie na istniejącym wydaniu:
  `PASS deployed SHA 5b5fceb: HTTP status, HTTPS application, API readiness`.
- Obecna ochrona z API: tylko `Required CI`. Nie wpisywać tu docelowych checków
  jako już aktywnych.
- Ostatni push-run main: [42302297975](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/42302297975)
  miał sukces starych jobów, bez osobnego `Lint` i `Post-deploy smoke`.
  Nie jest dowodem nowych bram.
- [DoD](https://github.com/DawidHnat/Projekt_Zespolowy/blob/main/DEFINITION_OF_DONE.md)
  i [retro S2](https://github.com/DawidHnat/Projekt_Zespolowy/blob/main/docs/retro/sprint-2.md)
  należy linkować do main dopiero po scaleniu tego PR.
- Planowany Sprint 3: `FF Sprint 3 - dane i konta`, 19.11–02.12. Cel obejmuje
  ręcznych kierowców, kartotekę i dokumenty pojazdu, historię i ewidencję MVP,
  ręczne auta/archiwizację oraz konta, profil, reset i monitoring; najpierw
  kontrakty/API, potem UI i QA. Pełny aktualny cel i status należy skopiować
  z Jiry po prawdziwym starcie.
- [SCRUM-128](https://fleet-flow.atlassian.net/browse/SCRUM-128): działanie retro;
  [SCRUM-129](https://fleet-flow.atlassian.net/browse/SCRUM-129): duży bundle,
  `frontend/vite.config.ts` i import Mapbox w
  `frontend/src/features/fleet/components/VehicleMap.tsx`.

Każdy członek zespołu oddaje własną odpowiedź. Ten plik nie potwierdza
uczestnictwa, QA ani wykonania przeglądu przez inną osobę.
