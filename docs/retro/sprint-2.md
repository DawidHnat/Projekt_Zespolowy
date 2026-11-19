# Retrospektywa Sprintu 2 — potwierdzone ustalenia

**Data: 18.11.2026**, uczestnicy: **Jakub Czaja, Dawid Hnat, Jakub Nazarewicz,
Marcel Głowacki**. Potwierdził PO Jakub Czaja 19.11 w bieżącej rozmowie;
godziny/miejsce nieustalone. Zapis: **agent Codex na polecenie PO**, nie uczestnik.
[Dowód SCRUM-142/10347](https://fleet-flow.atlassian.net/browse/SCRUM-142?focusedCommentId=10347).
[Uzupełnienie relacji PO 19.11](https://fleet-flow.atlassian.net/browse/SCRUM-142?focusedCommentId=10365).
[Review i stan 12 otwartych prac S2](../SPRINT_2_REVIEW.md).

## Co poszło dobrze

Potwierdzona ogólna ocena PO: „działa wszystko co powinno”, dostępność jest
stabilna i „nawet ok”. To relacja PO, bez przypisywania jej imiennie innym
uczestnikom i bez wniosku o pełnym technicznym odbiorze Story.

Osobno od wyniku spotkania: main `cb634da` ma zielone
[CI/deploy/smoke 44386951054](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/44386951054).
Agent 19.11 potwierdził zgodny HTTP/HTTPS i readiness. Nie przypisujemy tego
SHA spotkaniu 18.11.

## Co poszło źle / co poprawić

PO ocenił przyrost jako w porządku, ale nadal mało widoczny na stronie.
Wskazał potrzebę jak najszybszego odbioru Story i dokończenia S2.
SHA i dokładne środowisko pokazu pozostają nieustalone. Zakres demonstracji
PO uzupełnił 19.11 w [protokole Review](../SPRINT_2_REVIEW.md). Sam pokaz
i termin nie zastępują pełnych AC/QA/DoD.

## Efekt działania SCRUM-65

Działanie z S1: codzienne review, pierwsza odpowiedź do 24 h w dniach
obecności i doprowadzenie jednej rozpoczętej Story do pełnego DoD.
[Tabela i datowane pomiary](../REVIEW_QUEUE.md). Dokument #73 i tabela 4/4
są już dostarczone. Pomiar bazowy 10.11 wykazał 2 zwykłe PR bez pierwszego
formalnego review >24 h. Odczyt 16.11: 0; rekonstrukcja stanu 11.11 wykonana
16.11: 7, nie terminowy pomiar z 11.11. Nie antydatujemy tych wyników.

**Ocena retro 18.11, przekazana przez Jakuba 19.11:** spotkania pomagały,
ale bez nich codzienne regularne sprawdzanie PR-ów nie odbywało się w pełni.
To potwierdzona relacja PO o efekcie SCRUM-65, nie nowy pomiar ilościowy ani
indywidualny podpis każdego uczestnika. Pełne DoD 16/91 jest w SCRUM-141;
review auth i ocena restore Dawida pozostają wykonane. Końcowy QA Marcela
nadal oczekuje, z ograniczonym wyjątkiem prób Mac/Safari wykonywanych przez Jakuba.

## Dalsze działania i plan S3

| Działanie | Właściciel / źródło decyzji | Stan |
| --- | --- | --- |
| **Codziennie sprawdzać kolejkę PR-ów i przypominać przypisanym reviewerom** | **Jakub Czaja**, nowa decyzja PO z **19.11**, bez antydatowania na retro 18.11 | Uzgodnione działanie; to zadanie Jakuba, nie automatyczna wysyłka agenta |
| Dokończyć bieżący zakres S2, zebrać odbiory i przygotować osobne 3.2/4.2; następnie rozpocząć istniejący S3 | **Jakub Czaja**, priorytet PO potwierdzony 19.11 po relacji ze spotkań | W toku; termin „dziś” jest celem, nie dowodem odbioru |
| [SCRUM-128](https://fleet-flow.atlassian.net/browse/SCRUM-128): od początku S3 prowadzić jedną całą Story do DoD i mierzyć kolejkę | **Jakub Czaja**; zakres i dostępność do istniejącego planu potwierdził PO 19.11 | Zaplanowane w istniejącym S3; nie twierdzimy, że dokładnie ten tekst był uzgodnionym wynikiem retro 18.11 |
| [SCRUM-129](https://fleet-flow.atlassian.net/browse/SCRUM-129): poprawić rozmiar bundla/import Mapbox bez wyciszenia ostrzeżenia | **Jakub Nazarewicz**; plan i dostępność potwierdzone przez PO 19.11 | Zaplanowane w istniejącym S3; frontend/vite.config.ts i VehicleMap.tsx, potrzebny pomiar przed/po |

Nie dopisano indywidualnych zobowiązań uczestników ani fikcyjnego terminu
wykonania tych zadań. Nie trzeba dziś kończyć S3. Backup/recovery **84 jest
odłożony do końcowego S5**, a nie brakującym nowym działaniem na dziś.

## Pozostałe rozliczenie

Ocena 65 i właściciel nowego działania są uzupełnieni. Pozostają pełne odbiory,
niezależny review/CI/main dokumentów i rozliczenie bieżącego zakresu S2.
142 i końcowy 143 kończą się dopiero po rzeczywistym przełączeniu S2→S3.
