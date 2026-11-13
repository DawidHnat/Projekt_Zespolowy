# Retrospektywa Sprintu 1

Jira: [SCRUM-3](https://fleet-flow.atlassian.net/browse/SCRUM-3).

**Aktualizacja stanu 12.11.2026:** Sprint 1 zakończono 09.11; aktywny jest
`FF Sprint 2 - podstawa i QA`, z działaniem SCRUM-65. Każdy członek ma już
własny scalony PR i review cudzego, a PR #62 jest odebranym dowodem konfliktu
kodu. Dalszy zapis poniżej zachowuje obserwacje z 4–6.11, w tym ówczesne
braki i nazwy sprintów; nie opisuje aktualnej kolejki. Pełne DoD jednej Story
S1 pozostaje do zebrania w SCRUM-141. [Aktualna macierz oddania](../COURSE_READINESS.md).
Potwierdzenie Review z 06.11 nie oznacza potwierdzenia osobnego spotkania retro.

**Retrospektywa na podstawie obserwacji i zapisów z 4.11.2026.**
Uzupełnienie 06.11.2026: PO potwierdził odbyty tego dnia Review z udziałem
całego zespołu i pozytywną ocenę pokazanych funkcji. To potwierdzenie Przeglądu,
nie informacja o osobnym spotkaniu retrospektywy ani odbiór wszystkich warunków DoD.

## Co poszło dobrze

- Na Review 06.11 uczestniczył cały zespół: Jakub Czaja, Dawid Hnat,
  Jakub Nazarewicz i Marcel Głowacki. Według potwierdzenia PO przejrzane
  funkcje oceniono pozytywnie. Szczegółowego feedbacku nie przekazano.
- Aplikacja działa przez HTTPS na docelowej domenie. Kontrola gotowości
  zwróciła HTTP 200, a wersja `4ce144e` na stronie serwera zgadzała się
  z `origin/main` po pobraniu zmian. [Fleet-Flow](https://fleet-flow.pl/)
  · [Wynik CI i wdrożenia](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/40400220960)
- Powstał klikalny prototyp trzech przepływów Sprintu 1 oraz jawne kryteria
  akceptacji i Definition of Done.
- Marcel przygotował plan QA z 57 scenariuszami. W odbiorze logowania
  potwierdził m.in. poprawne logowanie, odrzucenie błędnego hasła i utrzymanie
  sesji po odświeżeniu strony. [PR #28](https://github.com/DawidHnat/Projekt_Zespolowy/pull/28)
  · [Raport SCRUM-56](https://fleet-flow.atlassian.net/browse/SCRUM-56)

## Co poszło źle

- Review i odbiory spowalniają domknięcie pracy. Logowanie nadal czeka na pełny
  odbiór sesji i ochrony API oraz dowód niezależnego przeglądu implementacji.
  Lista i mapa są w toku, a synchronizacja jest w weryfikacji.
  [SCRUM-16](https://fleet-flow.atlassian.net/browse/SCRUM-16)
  · [SCRUM-5](https://fleet-flow.atlassian.net/browse/SCRUM-5)
  · [SCRUM-15](https://fleet-flow.atlassian.net/browse/SCRUM-15)
- Autorstwo scalonych PR-ów było skupione na jednej osobie. W odczycie
  z 4.11 własne scalone PR-y mieli Jakub Czaja i Marcel. Dawid i Jakub
  Nazarewicz nie mieli jeszcze własnych scalonych PR-ów. W zapisanych
  recenzjach cudzych scalonych PR-ów brakowało Marcela i Nazarewicza.
- Odbiór danych floty wymaga udokumentowanego pierwszego odczytu źródła
  i niezależnej weryfikacji listy, mapy oraz aktualności danych.
  [SCRUM-64](https://fleet-flow.atlassian.net/browse/SCRUM-64)
  · [SCRUM-23](https://fleet-flow.atlassian.net/browse/SCRUM-23)

## Działania z właścicielami

Jakub Czaja jest właścicielem działania SCRUM-65 w aktywnym sprincie
`FF Sprint 2 - historia i auta` (4–18.11.2026). Jakub codziennie
przegląda kolejkę PR-ów, udziela pierwszej odpowiedzi do 24 godzin
w dniach dostępności i zbiera dowody DoD dla rozpoczętych historyjek.
W połowie sprintu Jakub sprawdzi liczbę PR-ów bez odpowiedzi po 24 godzinach
i liczbę w pełni odebranych historyjek. Zespół oceni wynik na retro Sprintu 2.
[SCRUM-65](https://fleet-flow.atlassian.net/browse/SCRUM-65)

| Osoba | Co przygotować i zrobić | Gdzie zapisać wynik |
| --- | --- | --- |
| Dawid Hnat | Podać stan wdrożenia i blokady synchronizacji. Na Planningu określić dostępność i zależności backendu. Przejrzeć zapis retro po dopisaniu ustaleń. | SCRUM-64 i review PR #32 |
| Jakub Nazarewicz | Podać, które zachowania listy i mapy są sprawdzone i czego brakuje. Na Planningu uzgodnić z zespołem zakres frontendu historii pojazdu i kierowców. | SCRUM-5 i decyzja w SCRUM-3 |
| Marcel Głowacki | Uzupełnić odbiór logowania. W raporcie zapisać testowane SHA, wyniki PASS/FAIL/BLOCKED i pozostałe scenariusze sesji oraz ochrony API. Na Planningu wskazać czas potrzebny na odbiór Sprintu 2. | SCRUM-56 i plan QA w SCRUM-63 |
| Jakub Czaja | Zebrać feedback zespołu, pilnować realizacji SCRUM-65 i rozliczyć otwarte prace Sprintu 1. | SCRUM-3, SCRUM-65 i backlog Jira |

Sprint 2 ruszył z celem udostępnienia historii tras, podstawowej ewidencji,
ręcznej kartoteki kierowców i pełnych danych pojazdu (leasing, zdjęcie,
OC, badanie i dokumenty). Sprint 1 wciąż jest aktywny. Jira wskazuje
otwarte podzadania SCRUM-1 i SCRUM-66 jako blokadę jego zakończenia.
[Backlog Jira](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog)

Data i uczestnicy Review są potwierdzeni w uzupełnieniu z 06.11.
Szczegółowe uwagi, decyzje dotyczące dalszego zakresu i termin osobnego spotkania
retrospektywy nie zostały przekazane. Działanie SCRUM-65 i jego właściciel
pozostają zapisanym usprawnieniem. [Protokół i scenariusz Review](../SPRINT_1_REVIEW.md)
