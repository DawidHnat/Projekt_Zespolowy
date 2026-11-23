# Przegląd Sprintu 3 · przygotowanie na 28.11.2026

[Sprint 3 w Jirze](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1) trwa od 20.11.2026 07:15:30.480 do 27.11.2026 23:59:59.999 CET. Na zjeździe
zapisujemy faktyczne demo, SHA wdrożenia, wynik testów i uwagi zespołu.

## Proponowane demo

Kartoteka i przypisania kierowców [SCRUM-42](https://fleet-flow.atlassian.net/browse/SCRUM-42)
oraz profil i wylogowanie urządzeń [SCRUM-49](https://fleet-flow.atlassian.net/browse/SCRUM-49)
korzystają z tej samej sesji. Na wdrożeniu pokaż widok kierowców i własny
profil na dopuszczonym koncie. W środowisku syntetycznym pokaż kartę kierowcy
z przypisaniem, a następnie z poziomu profilu wyloguj wszystkie urządzenia.
Wspólny test sprawdza, że druga wcześniej aktywna sesja otrzymuje HTTP 401
podczas próby odczytu kartoteki.

Kod [SCRUM-178](https://fleet-flow.atlassian.net/browse/SCRUM-178) w [PR #166](https://github.com/DawidHnat/Projekt_Zespolowy/pull/166)
dodaje test Playwright z oboma kluczami oraz odczytowy smoke kartoteki
kierowców i własnego profilu w jednej sesji `viewer`. Przed scaleniem
operator konfiguruje wydzielone konto na serwerze deweloperskim oraz
sekrety `DEV_SPRINT3_SMOKE_USERNAME` i `DEV_SPRINT3_SMOKE_PASSWORD`
w środowisku GitHub `development`.
Smoke kończy wyłącznie własną sesję i wypisuje wynik bez treści odpowiedzi.

Do oddania potrzebne są rzeczywiste wkłady **dwóch autorów** w Story
Sprintu 3, z kodem dostępnym na `main`. W odczycie 23.11.2026 PR-y #50,
#51 i #31 oraz przyrost #162 mają autora `jczaja51`. #162 jest scalony do
gałęzi #161. Potrzebny jest wkład drugiego autora albo zatwierdzenie innej pary.

## Blokada

[SCRUM-49](https://fleet-flow.atlassian.net/browse/SCRUM-49) ma flagę
`Impediment` i relację `is blocked by` z
[SCRUM-48](https://fleet-flow.atlassian.net/browse/SCRUM-48).
Komentarz określa, czego brakuje i od kogo.
[Zapis komentarza](https://fleet-flow.atlassian.net/browse/SCRUM-49?focusedCommentId=10414).
Po faktycznym odbiorze i scaleniu zależności odnotuj **Gotowe** w SCRUM-48,
zdejmij flagę w SCRUM-49 i zachowaj link do dowodu w Jirze.

## Stan wdrożenia 23.11.2026

Ostatni zakończony przebieg `main` **45250031627** na `524f30f` ma
zielone testy, lint, wdrożenie i dotychczasowy smoke. Log potwierdza:

```text
PASS deployed SHA 524f30f: HTTP status, HTTPS application, API readiness
```

Dowód dotyczy gotowości aplikacji i wersji serwera.
[Przebieg bazowy](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/45250031627).

## Polecenia do indywidualnego oddania

Uruchom na zjeździe z katalogu głównego klonu repozytorium zespołu.

```bash
git fetch --prune origin
gh pr list --state merged --search "merged:2026-11-20..2026-11-27" \
  --limit 100 --json number,author,headRefName
run_id=$(gh run list --branch main --workflow CI --limit 1 \
  --json databaseId --jq '.[0].databaseId')
gh run view "$run_id" --log | grep -F "SCRUM-42 + SCRUM-49"
gh run view "$run_id" --json jobs --jq '.jobs[] | "\(.name) \(.conclusion)"'
git show origin/main:.github/workflows/ci.yml | sed -n '/^  smoke:/,$p'
gh pr view 165 --json reviews --jq \
  '[.reviews[] | select(.state == "APPROVED") | .author.login] | unique'
```

Uzupełnij odpowiedź o ID przebiegu, dwa klucze Story, wycięty krok smoke,
blokadę z komentarzem, odnośniki do plików na `main` oraz nazwę, cel i sumę
SP rzeczywiście aktywnego Sprintu 4. Każdy członek zespołu oddaje odpowiedź
we własnym imieniu.

[Raport wkładu](contribution.md) · [Kontrakt zespołu](../TEAM_CONTRACT.md) ·
[Retrospektywa i plan S4](retro/sprint-3.md) · [Przegląd kontraktu #165](https://github.com/DawidHnat/Projekt_Zespolowy/pull/165).
