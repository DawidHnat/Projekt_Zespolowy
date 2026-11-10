# Retrospektywa Sprintu 1

Jira: [SCRUM-3](https://fleet-flow.atlassian.net/browse/SCRUM-3).

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
`FF Sprint 2 - podstawa i QA` (4–18.11.2026; nazwa po przeplanowaniu 09.11).
10.11 PO potwierdził uzgodnienie przez zespół codziennego przeglądu
otwartych PR-ów i pierwszej odpowiedzi do 24 h w dniach dostępności. Jakub codziennie
przegląda kolejkę PR-ów, udziela pierwszej odpowiedzi do 24 godzin
w dniach dostępności i zbiera dowody DoD dla rozpoczętych historyjek.
W połowie sprintu Jakub sprawdzi liczbę PR-ów bez odpowiedzi po 24 godzinach
i liczbę w pełni odebranych historyjek. Zespół oceni wynik na retro Sprintu 2.
[SCRUM-65](https://fleet-flow.atlassian.net/browse/SCRUM-65)

[Tabela rzeczywistych autorów/review, kolejka i pomiar DoD z 10.11](../REVIEW_QUEUE.md).
Każda z czterech osób ma własny scalony PR i review cudzego PR. Pomiar bazowy:
2 zwykłe PR-y bez formalnego review ponad 24 h; 0/3 historyjek produktu
Sprintu 1 z potwierdzonym kompletem dowodów DoD. Administracyjny status Gotowe
nie uzupełnia braków niezależnego odbioru. Pomiar w połowie sprintu i ocena
na retro Sprintu 2 pozostają do wykonania.

| Osoba | Co przygotować i zrobić | Gdzie zapisać wynik |
| --- | --- | --- |
| Dawid Hnat | Podać stan wdrożenia i blokady synchronizacji. Na Planningu określić dostępność i zależności backendu. Przejrzeć zapis retro po dopisaniu ustaleń. | SCRUM-64 i review PR #32 |
| Jakub Nazarewicz | Podać, które zachowania listy i mapy są sprawdzone i czego brakuje. Na Planningu uzgodnić z zespołem zakres frontendu historii pojazdu i kierowców. | SCRUM-5 i decyzja w SCRUM-3 |
| Marcel Głowacki | Uzupełnić odbiór logowania. W raporcie zapisać testowane SHA, wyniki PASS/FAIL/BLOCKED i pozostałe scenariusze sesji oraz ochrony API. Na Planningu wskazać czas potrzebny na odbiór Sprintu 2. | SCRUM-56 i plan QA w SCRUM-63 |
| Jakub Czaja | Zebrać feedback zespołu, pilnować realizacji SCRUM-65 i rozliczyć otwarte prace Sprintu 1. | SCRUM-3, SCRUM-65 i backlog Jira |

Sprint 2 pierwotnie ruszył z celem historii tras i kartoteki. Po przeplanowaniu
09.11 celem jest domknięcie floty/UI, danych WEBFLEET, kartoteki,
backup/odtworzenie i synchronizacja oraz preferencje konta i decyzje prywatności.
Priorytetem są review/QA i blokady przed nowymi funkcjami. Sprint 1 został
zamknięty w Jirze; niezakończony zakres jest w kolejnych sprintach.
Zamknięcie sprintu nie potwierdza pełnego DoD jego historyjek.
[Backlog Jira](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog)

Data i uczestnicy Review są potwierdzeni w uzupełnieniu z 06.11.
Szczegółowe uwagi, decyzje dotyczące dalszego zakresu i termin osobnego spotkania
retrospektywy nie zostały przekazane. Działanie SCRUM-65 i jego właściciel
pozostają zapisanym usprawnieniem. [Protokół i scenariusz Review](../SPRINT_1_REVIEW.md)
