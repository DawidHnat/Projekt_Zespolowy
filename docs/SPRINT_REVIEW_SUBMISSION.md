# Przegląd Sprintu i Pull Requesty — dowody do oddania

Jira: [SCRUM-3](https://fleet-flow.atlassian.net/browse/SCRUM-3).
Każdy oddaje osobno. Polecenia wykonujemy w repozytorium po ostatnim scaleniu
i udanym wdrożeniu; nie zastępujemy wyników planem ani przykładem.

## 1. Serwer i ostatni main

- Aplikacja: https://vps-9171bf52.vps.ovh.net/
- Strona wersji HTTP do zadania: http://57.129.179.53/

```bash
git fetch && curl -s http://57.129.179.53/ | grep "$(git rev-parse --short=7 origin/main)"
```

Zapisać rzeczywisty HTML i SHA po zakończeniu wdrożenia. Dodatkowo:

```bash
curl -fsS https://vps-9171bf52.vps.ovh.net/api/health/ready
```

Poprawne SHA i health nie zastępują jednej odebranej Story zgodnej z całym DoD.
Pokaz przeprowadzamy według [historyjek](SPRINT_1_REVIEW.md).

## 2. Autorzy, review, gałęzie i klucze Jiry

W treści zadania nie ma filtra z „kroku 6 tutorialu”. Poniższy jawny filtr
pokazuje wymagane dane; jeżeli prowadzący dostarczy swój filtr, użyć jego wersji.

```bash
gh pr list --state merged --limit 100 --json number,headRefName,author,reviews,body \
  --jq '.[] | {number, branch: .headRefName, author: .author.login, jira: ([.body | scan("SCRUM-[0-9]+")]|unique), reviews: [.reviews[] | {reviewer: .author.login, state: .state}]}'
```

Sprawdzić, czy każdy z `jczaja51`, `DawidHnat`, `jnazarewiczs`, `mglowacki0`
jest autorem scalonego PR i recenzentem cudzego PR. Zwrócony wpis review nie
może być własnym komentarzem autora. Samo przypisanie jako reviewer nie jest
wykonanym przeglądem. Do dowodów używamy rzeczywistych review, a do przyjęcia
zmiany wymaganego aktualnego approval.

Stan po scaleniu PR #28 dnia 26.10.2026:

| Członek | Własny scalony PR | Wykonane review cudzego PR | Pozostała praca |
| --- | --- | --- | --- |
| Jakub Czaja — jczaja51 | np. #26 | #28, APPROVED | Dokończyć odbiór wybranej Story Sprintu 1 z QA. |
| Dawid Hnat — DawidHnat | Brak | np. #26, APPROVED | Dostarczyć własny PR rzeczywistej zmiany z kluczem Jiry i uzyskać review/merge. |
| Jakub Nazarewicz — jnazarewiczs | Brak | Brak | Dostarczyć własny PR i przejrzeć cudzy. |
| Marcel Głowacki — mglowacki0 | #28 | Brak | Przejrzeć cudzy PR oraz wykonać odbiory QA. |

Starsze PR-y #1/#2 nie mają klucza Jiry w nazwie gałęzi ani opisie, #4 nie ma
klucza w opisie; nie są dowodem wymaganej poprawnej konwencji. Nie zmieniamy
historycznego autorstwa ani nie tworzymy pustych commitów dla statystyki.
Każdy przyszły PR ma klucz Jiry w opisie i nazwie gałęzi oraz review innej osoby.

## 3. Conventional Commits od włączenia ochrony

Dawid potwierdza dokładną datę/godzinę włączenia reguły. Zapisany test
`23dd927` z 20.10 był jeszcze przyjęty bez PR, późniejszy `be4bc42` został
odrzucony. API pełnej ochrony jest niedostępne współpracownikowi (404), więc
nie wyprowadzamy dokładnej godziny z daty pliku konfiguracyjnego.

Po potwierdzeniu daty wykonać polecenia z zadania:

```bash
git fetch
git log --no-merges --since="<data włączenia ochrony>" --format=%s origin/main | grep -vcE '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|breaking)(\([^)]+\))?!?: .+'
```

Kontrola szerszego, konserwatywnego zakresu od `2026-10-20T00:00:00+02:00`
zwróciła 0 podczas przygotowania 26.10.2026. To nie jest potwierdzenie dokładnej
godziny włączenia ochrony. Przy `grep -vcE` wynik 0 jest oczekiwany; samo `grep`
może wtedy zakończyć się kodem 1, bo nie znalazło niedopasowanych linii.

Przykładowy właściwy temat: `feat(SCRUM-51): uzupełnij dane pojazdu`.
Przy squash osoba scalająca sprawdza temat końcowego commita. Nigdy nie
przepisujemy chronionego `main`, by poprawić historię.

## 4. Konflikt scalania — jeszcze do wykonania

Nie zebrano dotąd dowodu spełniającego to kryterium. PR #27 łączy się
z aktualnym main bez konfliktu; nie opisujemy go jako rozwiązanego konfliktu.
Samo zielone CI i zdanie w opisie nie wystarczają.

Zespół wybiera dwie uzasadnione zmiany tego samego fragmentu kodu w osobnych
zadaniach. Obie gałęzie powstają z tego samego `main`, mają klucze swoich
zgłoszeń i własnych autorów. Pierwszy PR przechodzi review/CI i zostaje scalony.
Na drugiej gałęzi developer wykonuje:

```bash
git fetch origin
git merge origin/main
git status
# Ręcznie połączyć obie intencje w plikach z konfliktem, usunąć znaczniki.
# Uruchomić wymagane testy; git add z konkretnymi nazwami plików.
git commit -m "fix(SCRUM-NUMER): rozwiąż konflikt z main z zachowaniem obu zmian"
git push
```

W opisie drugiego PR podać: wcześniejszy scalony PR, plik i wspólne linie,
przyczynę konfliktu, zachowane zachowanie obu zmian i wynik testów. Poczekać
na zielone CI ostatniego commita oraz ponowne review. Wkleić jego numer/link
do odpowiedzi dopiero po rzeczywistym rozwiązaniu.

## 5. Review, retrospektywa i Sprint 2

- Doprowadzić co najmniej jedną Story Sprintu 1 do pełnego DoD na VPS,
  zapisać QA i przeprowadzić rzeczywisty [Review](SPRINT_1_REVIEW.md).
- Potwierdzić z zespołem i uzupełnić
  [docs/retro/sprint-1.md](retro/sprint-1.md) — trzy części, właściciele,
  terminy sprawdzenia i feedback. Obecnie jest to materiał roboczy.
- [SCRUM-65](https://fleet-flow.atlassian.net/browse/SCRUM-65) jest działaniem
  usprawniającym przypisanym Jakubowi Czai i dodanym do planowanego Sprintu 2.
- Na Planningu potwierdzić daty, pojemność i cel **FF Sprint 2 - historia**,
  uporządkować prace niedokończone, zakończyć Sprint 1 i uruchomić Sprint 2.
  Potem wkleić rzeczywistą nazwę i cel z Jiry. Stan planowany nie spełnia
  wymagania „w Jirze trwa Sprint 2”.

Gotowa odpowiedź musi zawierać bieżący wynik SHA, zestawienie PR z filtrem,
wynik 0 dla komunikatów, numer rzeczywistego PR z konfliktem, link do
zatwierdzonej retrospektywy na main i aktywny Sprint 2. Puste pola lub
niniejsza instrukcja nie są kompletnym oddaniem.
