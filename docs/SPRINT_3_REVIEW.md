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

Na `main` są rzeczywiste wkłady co najmniej dwóch osób z okna Sprintu 3:
[Jakub Czaja, poprawka prywatności wyszukiwania kierowców](https://github.com/DawidHnat/Projekt_Zespolowy/commit/9892f87) i
[Marcel Głowacki, automatyczny test odzyskania mapy](https://github.com/DawidHnat/Projekt_Zespolowy/commit/1e5c51d).
Dla wymaganej pary funkcji **SCRUM-42 + SCRUM-49** podstawowe PR-y #50,
#51 i #31 mają tego samego autora `jczaja51`. #162 również jest jego
autorstwa i trafił do gałęzi #161. Uznanie współautorstwa tej konkretnej
pary wymaga udokumentowanego wkładu drugiego autora z zakresu jednej z
tych Story albo wyboru przez zespół innej, rzeczywiście dostarczonej pary
i wspólnego scenariusza.

## Blokada

[SCRUM-49](https://fleet-flow.atlassian.net/browse/SCRUM-49) ma flagę
`Impediment` i relację `is blocked by` z
[SCRUM-48](https://fleet-flow.atlassian.net/browse/SCRUM-48).
Komentarz określa, czego brakuje i od kogo.
[Zapis komentarza](https://fleet-flow.atlassian.net/browse/SCRUM-49?focusedCommentId=10414).
Po faktycznym odbiorze i scaleniu zależności odnotuj **Gotowe** w SCRUM-48,
zdejmij flagę w SCRUM-49 i zachowaj link do dowodu w Jirze.

## Stan przed zjazdem, 27.11.2026

- `main` i publiczna wersja wskazują `17ea095`. Gotowość API HTTP 200,
  wymagane kontrole, deploy i dotychczasowy smoke są potwierdzone.
  [Wersja](https://fleet-flow.pl/status.html) ·
  [CI i deploy](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/46011237932) ·
  [Smoke](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/46011237932/job/140553505637)
- Kartoteka i podstawowy profil są na `main`. Właściwy odbiór kartoteki oraz
  potwierdzanie zmiany e-maila pozostają otwarte. Wyniki Marcela dla Chromium
  przyjęto jako dowód częściowy. [SCRUM-54](https://fleet-flow.atlassian.net/browse/SCRUM-54?focusedCommentId=10517) · [#31](https://github.com/DawidHnat/Projekt_Zespolowy/pull/31) · [#161](https://github.com/DawidHnat/Projekt_Zespolowy/pull/161)
- PO potwierdził pomocniczą ewidencję z sumą znanych kilometrów i liczbą przejazdów
  bez celu. Import i widok okresu wchodzą po uzgodnieniu grafu migracji i
  kontraktu #191/#192. [SCRUM-62](https://fleet-flow.atlassian.net/browse/SCRUM-62?focusedCommentId=10514)
- W próbie demonstracji #166 zapisz dwa profile CI i odczytowy smoke
  wydzielonego `viewer` po wdrożeniu tej zmiany. Dawid sprawdza gotowość
  środowiska, Marcel zapisuje niezależne QA, prowadzący spotkanie zapisuje
  wynik faktycznego demo. [SCRUM-178](https://fleet-flow.atlassian.net/browse/SCRUM-178) · [SCRUM-152](https://fleet-flow.atlassian.net/browse/SCRUM-152)

## Kolejność integracji i stan otwartych review

Poniżej odczyt 27.11. Na wszystkich wskazanych SHA przeszły `Required CI`,
`Backend (3.13)` i `Lint`. Ponowny przegląd wykazał otwarte poprawki.
Dawid potwierdza [kolejność i graf migracji](https://github.com/DawidHnat/Projekt_Zespolowy/pull/191#issuecomment-7222491233).
Każdy przyrost wraca do review i QA po aktualizacji bazy.

| Kolejność | PR i sprawdzony SHA | Blokada i właściciel |
| --- | --- | --- |
| 1 | [#191](https://github.com/DawidHnat/Projekt_Zespolowy/pull/191) · `df371ae` | Nazarewicz i Dawid. Blokada zapisów podczas downgrade, uzgodnienie wycofanych pozycji ze źródła z zachowaniem adnotacji, konflikt fixture E2E z #161. |
| 2 | [#192](https://github.com/DawidHnat/Projekt_Zespolowy/pull/192) · `a10e638` | Nazarewicz. Zgodność z definicją MVP, anulowane ładowanie w niepoprawnym okresie i konflikt stylów z #191. Marcel odbiera pokrycie i trwałość danych. |
| 3 | [#171](https://github.com/DawidHnat/Projekt_Zespolowy/pull/171) · `2e87bca` | Dawid. Przywrócony pojazd z flagą nieaktywny w źródle musi być dostępny w uzgodnionym widoku. Sprawdzić regresję historii. |
| 4 | [#173](https://github.com/DawidHnat/Projekt_Zespolowy/pull/173) · `3e94d6e` | Dawid. Powiązanie pojazdów musi przenieść przejazdy, postoje i dni pokrycia oraz rozwiązać kolizje kluczy w transakcji. |
| 5 | [#187](https://github.com/DawidHnat/Projekt_Zespolowy/pull/187) · `5b60b66` | Dawid. Trwały magazyn i wspólne odtworzenie bazy i plików, walidacja, skanowanie, limity i obsługa krótkiego zapisu. |
| 6 | [#188](https://github.com/DawidHnat/Projekt_Zespolowy/pull/188) · `c0d2290` | Dawid. Reguła D1 uwzględnia długość i miejsca. Brak danych daje „do sprawdzenia”. Uzgodnić transakcję przypisań i właściciela rewizji pełnej kartoteki. [Decyzja macierzy](https://github.com/DawidHnat/Projekt_Zespolowy/pull/188#issuecomment-7222483093) |
| 7 | [#204](https://github.com/DawidHnat/Projekt_Zespolowy/pull/204) · `096bbc8` | Nazarewicz i Dawid. Wydzielić pełną kartotekę po integracji stosu. Rewizja 0016 występuje także w #188. Przed downgrade zserializować kontrolę z zapisami. |
| Niezależnie | [#168](https://github.com/DawidHnat/Projekt_Zespolowy/pull/168) · `61053bb` | Przyrost przeniesiono do [#206](https://github.com/DawidHnat/Projekt_Zespolowy/pull/206) pod kluczem [SCRUM-181](https://fleet-flow.atlassian.net/browse/SCRUM-181). Dawid przegląda nowy PR. Marcel nadal prowadzi retesty i pełny odbiór SCRUM-120/121. |

## Zapis po Review 28.11

| Pole | Dowód do zebrania |
| --- | --- |
| Wersja i środowisko | Wdrożony SHA, adres, Actions i wynik readiness |
| Funkcje i wkład | Dwie Story, autorzy, commity na main i wspólny scenariusz |
| Rzeczywisty przebieg | Data, uczestnicy, co pokazano, wynik oraz uwagi |
| Niedostarczone elementy | Właściciele, blokady, decyzje o przeniesieniu i dalszy plan |

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
