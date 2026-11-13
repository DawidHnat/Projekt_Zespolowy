# Przegląd Sprintu 2 i bramy jakości — oddanie 4.2

Stan **12.11.2026**. Technika SCRUM-127 jest na main po
[PR #76](https://github.com/DawidHnat/Projekt_Zespolowy/pull/76).
**Kompletne oddanie nadal czeka na osobne wymagane checki, pełne DoD Story,
Review/retro S2 i start S3.** [Macierz i zadania](COURSE_READINESS.md).
PO potwierdził 12.11, że spotkania i pełny odbiór S2 jeszcze się nie odbyły.

## 1. Bieżący serwer

```bash
git fetch && curl -s http://57.129.179.53/ | grep -c "$(git rev-parse --short=7 origin/main)"
```

12.11: `origin/main=2b3f2ba`, wynik **1**. Aplikacja:
<https://fleet-flow.pl/>; HTTPS readiness HTTP 200, `{"status":"ok"}`.
Wynik odświeżyć po ostatnim merge i wdrożeniu.

## 2. Wymagane checki i czerwony lint

```bash
gh api 'repos/{owner}/{repo}/branches/main' --jq '.protection.required_status_checks.contexts[]'
# Alternatywa dla repo z rulesetem:
gh api 'repos/{owner}/{repo}/rules/branches/main' --jq '.[] | select(.type == "required_status_checks") | .parameters.required_status_checks[].context'
```

Rzeczywisty odczyt 12.11:

```text
Required CI
```

To **jeszcze nie spełnia** wymagania dwóch osobnych wymaganych checków.
Dawid dodaje `Backend (3.13)` oraz `Lint` w
[SCRUM-140](https://fleet-flow.atlassian.net/browse/SCRUM-140), zachowując
`Required CI`, pozostałe zabezpieczenia i nazwy jobów.

Dowód lintu: [PR #77 — NIE SCALAĆ](https://github.com/DawidHnat/Projekt_Zespolowy/pull/77),
run [42815387118](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/42815387118).

```bash
gh run view 42815387118 --json jobs --jq '.jobs[] | "\(.name) \(.conclusion)"'
```

Końcowe wyniki: `Lint failure`, `Required CI failure`, pozostałe testy/buildy
success, `Deploy development server skipped`, `Post-deploy smoke skipped`.
Celowe F401 dotyczy nieużytego importu `math`.

## 3. Testy przed wdrożeniem i smoke

Wycinek `.github/workflows/ci.yml` z aktualnego main:

```yaml
deploy:
  name: Deploy development server
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  needs: [required, frontend, backend, e2e, lint]
# dalsze kroki wdrażają artefakt tego samego SHA
smoke:
  name: Post-deploy smoke
  needs: [deploy]
# weryfikator wymaga SHA danego runu, HTTP/HTTPS i gotowości API
```

Do odpowiedzi wyciąć rzeczywisty blok z wyniku:

```bash
git show origin/main:.github/workflows/ci.yml
gh run list --branch main --event push --limit 1
gh run view 43105067278 --json jobs --jq '.jobs[] | "\(.name) \(.conclusion)"'
gh run view 43105067278 --log | grep 'PASS deployed SHA'
```

Ostatni run odczytany 12.11: **43105067278**, SHA `2b3f2ba`:

```text
Lint success
Backend image success
Critical browser flows success
Backend (3.13) success
Backend (3.12) success
Frontend build success
Required CI success
Deploy development server success
Post-deploy smoke success
```

Linia logu:

```text
PASS deployed SHA 2b3f2ba: HTTP status, HTTPS application, API readiness
```

Po nowym pushu wybrać nowe ID z `gh run list`, a nie kopiować historycznego.
Test smoke dotyczy SHA swojego runu; dodatkowy fetch/grep dotyczy najnowszego main.

Dowód czerwonego testu: [PR #78 — NIE SCALAĆ](https://github.com/DawidHnat/Projekt_Zespolowy/pull/78),
run [42815401269](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/42815401269).

```bash
gh run view 42815401269 --json jobs --jq '.jobs[] | "\(.name) \(.conclusion)"'
```

`Frontend build failure` nastąpił na **npm test**, celowe `1 !== 2`.
`Lint`, oba backendy, obraz i browser flows mają success; `Required CI failure`,
`Deploy development server skipped`, `Post-deploy smoke skipped`.
PR #24 to dawny błąd składni/budowy, a nie zastępstwo dowodu czerwonego testu.

## 4. DoD i przyrost

[DEFINITION_OF_DONE.md](../DEFINITION_OF_DONE.md) oznacza wykonawcę przy każdym
warunku. Pipeline wykonuje testy, lint i smoke; człowiek odbiera kryteria,
scenariusze UI, dokumentację i zakres. Macierz nie jest wynikiem QA.

[SCRUM-141](https://fleet-flow.atlassian.net/browse/SCRUM-141) zbiera pełne
DoD rzeczywistej Story z S2. Aktualni kandydaci to SCRUM-84 i SCRUM-91;
wybór PO musi odpowiadać rzeczywiście wykonanej i odebranej funkcji.
Zielone bramy SCRUM-127 ani sam dashboard SCRUM-38 nie są całą Story S2.

## 5. Retro i Sprint 3

[Retro S2](retro/sprint-2.md) jest materiałem do spotkania. Po rzeczywistej
retrospektywie dopisać datę, uczestników, ocenę działań S1 i uzgodnione nowe
działanie z właścicielem. [SCRUM-142](https://fleet-flow.atlassian.net/browse/SCRUM-142)
prowadzi Review/retro, rozliczenie S2 i start istniejącego S3.

Odczyt Jiry 12.11: **FF Sprint 3 - dane i konta**, id 4, **future**, plan
19.11–02.12. W zadaniu wymagany jest sprint aktywny — tego kroku jeszcze nie wykonano.
Cel zapisany w Jirze:

> Dostarczyć ręcznych kierowców, kartotekę i dokumenty pojazdu, historię oraz cele/ewidencję MVP, ręczne auta i archiwizację. Równolegle konta/profil/reset i wspólny dziennik zmian oraz monitoring. Najpierw wspólne kontrakty i API, potem UI i odbiór integracji. Historia wymaga działającej synchronizacji; pliki uzgodnionego magazynu i kopii. Rzeczywista wysyłka SMTP tylko po osobnym poleceniu. Po tym sprincie sprawdzić pozostałe godziny względem pojemności do końca roku. Założenie PO: 10–15 h/osobę/tydzień, z review i QA; dostępność i pozostały wysiłek potwierdzają wykonawcy. SP są istniejącą wyceną pełnego zakresu, nie pozostałymi godzinami. Nie sumować punktów rodzica i podzadań.

Zgłoszenia już w planowanym S3:

- [SCRUM-128](https://fleet-flow.atlassian.net/browse/SCRUM-128): działanie retro,
  Jakub Czaja — wybór jednej Story i pomiar kolejki review. Propozycję zatwierdza zespół.
- [SCRUM-129](https://fleet-flow.atlassian.net/browse/SCRUM-129): wybite okno,
  Jakub Nazarewicz — duży bundle, `frontend/vite.config.ts` i
  `frontend/src/features/fleet/components/VehicleMap.tsx`.

Do odpowiedzi linkować pliki **na main**, po ich review/merge i uzupełnieniu
rzeczywistych ustaleń. Każdy członek oddaje osobno; szkic nie zastępuje protokołu.
