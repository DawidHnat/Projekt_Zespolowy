# SCRUM-65 — kolejka review i dowody usprawnienia

Pomiar **2026-11-19T10:56:27+01:00**, wykonawca: **agent Codex na polecenie Jakuba Czai (jczaja51)**. Kontekst main `cb634da0ece8cd93424bfc16a5185cf817a0cbb1`; środowisko: odczyt GitHub reviews/comments i dowodów Jira. Wynik metryki: **PASS wykonania pomiaru**. Zadanie 65: **BLOCKED pełnego zakończenia** do pełnego DoD jednej Story i rzeczywistej oceny efektu.

## Uzgodniony rytm i tabela całej czwórki

PO potwierdził 10.11 codzienny przegląd PR i pierwszą odpowiedź do 24 h w dniach dostępności. Dokument #73 ma niezależny Approved Dawida na `7db684c`, zielone CI 43481211119 i jest w main od 13.11. Nie jest nową blokadą. Dowód: [SCRUM-65/10228](https://fleet-flow.atlassian.net/browse/SCRUM-65?focusedCommentId=10228).

| Osoba | Własny scalony PR / head | Review cudzego na końcowym head |
| --- | --- | --- |
| Jakub Czaja / jczaja51 | [#55](https://github.com/DawidHnat/Projekt_Zespolowy/pull/55), `9cff7e9` | Approved [#28](https://github.com/DawidHnat/Projekt_Zespolowy/pull/28), autor mglowacki0, `5a4a5e6` |
| Dawid Hnat / DawidHnat | [#60](https://github.com/DawidHnat/Projekt_Zespolowy/pull/60), `cbd861c` | Approved [#22](https://github.com/DawidHnat/Projekt_Zespolowy/pull/22), autor jczaja51, `e736bd1` |
| Jakub Nazarewicz / jnazarewiczs | [#61](https://github.com/DawidHnat/Projekt_Zespolowy/pull/61), `81ffe1e` | Approved [#55](https://github.com/DawidHnat/Projekt_Zespolowy/pull/55), autor jczaja51, `9cff7e9` |
| Marcel Głowacki / mglowacki0 | [#28](https://github.com/DawidHnat/Projekt_Zespolowy/pull/28), `5a4a5e6` | Approved [#29](https://github.com/DawidHnat/Projekt_Zespolowy/pull/29), autor jczaja51, `d0fc9c7` |

**4/4 PASS** — autorstwo, merge i porównanie commit review z końcowym head sprawdzone 19.11. Bez przepisywania historii i cudzych podpisów.

## Aktualna zwykła kolejka

Otwarte łącznie: **14**. Aktywne zwykłe PR: **10**; osobno **#105 DEFERRED → SCRUM-84/S5** oraz dowody **#24/#77/#78 (NIE SCALAĆ)**. Zwykłe PR bez pierwszego formalnego review: **8**, w tym ponad 24 h: **0**. Bez pierwszej odpowiedzi człowieka (komentarz albo review) ponad 24 h: **0**.

| PR / head w chwili pomiaru | Właściciel | Niezależny reviewer | Czas do pierwszej odpowiedzi | Czas do pierwszego formalnego review | Co rzeczywiście czeka |
| --- | --- | --- | --- | --- | --- |
| [#101](https://github.com/DawidHnat/Projekt_Zespolowy/pull/101), `a8476ac` | jczaja51 | DawidHnat | 21.63 h | 21.63 h | nowe Approved po zmianie head; dawna pierwsza odpowiedź istnieje |
| [#110](https://github.com/DawidHnat/Projekt_Zespolowy/pull/110), `be609d7` | jczaja51 | DawidHnat | 21.82 h | 21.82 h | nowe Approved po zmianie head; dawna pierwsza odpowiedź istnieje; następny dopiero po #101 |
| [#118](https://github.com/DawidHnat/Projekt_Zespolowy/pull/118), `0295ad4` | jczaja51 | mglowacki0, DawidHnat | brak (11.22 h od otwarcia) | brak (11.22 h od otwarcia) | brak pierwszego review |
| [#119](https://github.com/DawidHnat/Projekt_Zespolowy/pull/119), `ed1181f` | jczaja51 | mglowacki0, jnazarewiczs, DawidHnat | brak (3.19 h od otwarcia) | brak (3.19 h od otwarcia) | brak pierwszego review; dostępność reviewera odłożona przez PO, bez ponawiania prośby; poza warunkami S2 |
| [#120](https://github.com/DawidHnat/Projekt_Zespolowy/pull/120), `746309d` | jczaja51 | mglowacki0, jnazarewiczs | brak (1.18 h od otwarcia) | brak (1.18 h od otwarcia) | brak pierwszego review |
| [#121](https://github.com/DawidHnat/Projekt_Zespolowy/pull/121), `6357d17` | jczaja51 | mglowacki0, DawidHnat | brak (1.18 h od otwarcia) | brak (1.18 h od otwarcia) | brak pierwszego review |
| [#122](https://github.com/DawidHnat/Projekt_Zespolowy/pull/122), `75fdbbb` | jczaja51 | mglowacki0, DawidHnat | brak (1.06 h od otwarcia) | brak (1.06 h od otwarcia) | brak pierwszego review |
| [#123](https://github.com/DawidHnat/Projekt_Zespolowy/pull/123), `2121763` | jczaja51 | mglowacki0 | brak (1.05 h od otwarcia) | brak (1.05 h od otwarcia) | brak pierwszego review |
| [#124](https://github.com/DawidHnat/Projekt_Zespolowy/pull/124), `ede00c9` | jczaja51 | mglowacki0, DawidHnat | brak (0.90 h od otwarcia) | brak (0.90 h od otwarcia) | brak pierwszego review |
| [#125](https://github.com/DawidHnat/Projekt_Zespolowy/pull/125), `a5efcdc` | jczaja51 | mglowacki0 | brak (0.01 h od otwarcia) | brak (0.01 h od otwarcia) | brak pierwszego review |

DISMISSED nie usuwa faktu, że pierwsza odpowiedź kiedyś nastąpiła; nie jest jednak aktualnym Approved. #101/#110 czekają na nowe zatwierdzenie zmienionego head, a nie na pierwsze review od zera. Właściciel PR nie może go zatwierdzić za reviewera. Prośba o dostępność dla #119/150 została już odrzucona przez PO; ten pomiar jej nie ponawia.

Metryki liczą nieautorskie formalne reviews oraz osobno komentarze człowieka. Czas to surowe godziny kalendarzowe od createdAt, bez korekty o weekendy, draft/ready i indywidualną dostępność. Nie jest to samodzielny zarzut naruszenia uzgodnionego rytmu. Snapshot ma własną datę i head; późniejsza zmiana dokumentu nie antydatuje pomiaru.

## Datowane wyniki i połowa sprintu

| Kiedy naprawdę zebrano | Co mierzy | Wynik |
| --- | --- | --- |
| 10.11 — bazowy, przed połową sprintu | Zwykłe PR bez pierwszego formalnego review >24 h | 2 (#67/#68); 4/4 osób z własnym PR/review; 0/3 pełnych DoD Story S1 |
| 16.11, komentarz 10228 | Nowy rzeczywisty odczyt kolejki | 0 zwykłych bez pierwszego review >24 h; #73 już dostarczony; nadal brak pełnego DoD jednej rozpoczętej Story |
| Rekonstrukcja wykonana 16.11 dla 11.11 godz. 12:00 | Daty otwarcia/formalnych reviews, bez dowodu ówczesnego draft/ready | 7 zwykłych PR >24 h (#67–73). To **nie dowód pomiaru wykonanego 11.11**; terminowość AC4 pozostaje niepotwierdzona |
| 2026-11-19T10:56:27+01:00 | Bieżący snapshot, bez przepisywania go na 11.11 | 0 bez pierwszego formalnego review >24 h; nowe Approved po zmianach head nadal potrzebne |

## Pełny DoD i rzeczywista retrospektywa

[SCRUM-141](https://fleet-flow.atlassian.net/browse/SCRUM-141) zbiera obie pełne macierze 16/91. W zebranych dowodach **0/2 wybranych Story ma pełny końcowy odbiór**, mimo administracyjnego Gotowe. Review auth i ocena restore są już PASS w komentarzach 10324/10345. Następny krok **Marcela**: końcowe brakujące AC/DoD i podpis QA; **PO Jakub** potwierdza zakres. Nie trzeba kończyć wszystkich przyszłych regresji produktu.

PO potwierdził 19.11, że Review i retro S2 odbyły się 18.11 z całą czwórką ([SCRUM-142/10347](https://fleet-flow.atlassian.net/browse/SCRUM-142?focusedCommentId=10347)). Nie rozpoznał jednak numeru 65 i przekazał ogólną ocenę aplikacji. **Ocena skuteczności tego konkretnego działania na retro nie została przekazana**; nie zastępujemy jej dzisiejszą statystyką ani samym faktem spotkania. Aktualizacja rzeczywistych protokołów: [PR #123](https://github.com/DawidHnat/Projekt_Zespolowy/pull/123).

Do zakończenia 65 pozostają: niezależny review/CI/main aktualizacji tej kolejki, pełny DoD jednej Story w 141 oraz **Jakub Czaja/uczestnicy retro — konkretna ocena efektu codziennego review i uzgodnione dalsze działanie**. Dostępność i plan 128/129 PO potwierdził 19.11; nie wpisujemy tej decyzji wstecz jako szczegółowego wyniku spotkania 18.11.
