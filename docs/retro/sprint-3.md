# Retrospektywa Sprintu 3

**Przygotowanie do zjazdu 28.11.2026.** Wyniki rozmowy, decyzje uczestników
i ankietę uzupełnimy podczas spotkania na podstawie rzeczywistego
odczytu. [SCRUM-175](https://fleet-flow.atlassian.net/browse/SCRUM-175).

## Działania z retrospektywy Sprintu 2

| Działanie | Stan odczytany 27.11.2026 |
| --- | --- |
| Jakub Czaja codziennie sprawdza kolejkę PR-ów i przypomina reviewerom | W toku. SCRUM-128 zawiera pierwszą migawkę z 21.11. Próbny odczyt 27.11 o 16:48:27 dał 39 otwartych, 29 gotowych do review, 0 bez odpowiedzi i 0 ponad 24 h. Start 21.11 dał odpowiednio 25, 13, 3 i 0. Odczyt po siedmiu dniach przypada 28.11, po 22:50:22 CET. [SCRUM-128](https://fleet-flow.atlassian.net/browse/SCRUM-128) |
| Dokończyć pakiet S2 i uruchomić istniejący Sprint 3 | Działanie zakończone. Jira wskazuje zamknięcie S2 i start S3 20.11.2026. [SCRUM-142](https://fleet-flow.atlassian.net/browse/SCRUM-142) · [SCRUM-143](https://fleet-flow.atlassian.net/browse/SCRUM-143) |
| Doprowadzić jedną Story S3 do pełnego DoD i powtórzyć pomiar kolejki | W toku. Na dzień odczytu żadna Story S3 nie jest w kategorii Gotowe. [SCRUM-128](https://fleet-flow.atlassian.net/browse/SCRUM-128) |
| Poprawić rozmiar bundla mapy i zmierzyć efekt | Cel ustalono na odroczone ładowanie i mniejszy transfer. Odbiór pomiaru i niezależne review końcowej wersji pozostają otwarte. [SCRUM-129](https://fleet-flow.atlassian.net/browse/SCRUM-129) · [PR #159](https://github.com/DawidHnat/Projekt_Zespolowy/pull/159) |

[Zapis ustaleń retrospektywy S2](sprint-2.md).

## Proponowane nowe działanie

Na Planningu Sprintu 4 wybrać dwie powiązane Story do demonstracji.
Najpóźniej po pierwszym dniu sprintu w Jirze zapisać dwóch rzeczywistych
autorów, drogę review, wspólny scenariusz CI i warunki sprawdzenia na serwerze.
Właścicielem propozycji jest **Jakub Czaja**. Zespół rozstrzyga na retrospektywie,
czy przyjmuje to działanie. [SCRUM-176](https://fleet-flow.atlassian.net/browse/SCRUM-176).

## Ankieta bezpieczeństwa psychologicznego

Każdy członek zespołu wypełnia ankietę bez nazwiska w skali od 1 do 7.
Ocena 1 oznacza, że stwierdzenie zupełnie nie opisuje zespołu, a 7, że
opisuje go bardzo trafnie. W tabeli są skrócone etykiety siedmiu pozycji Amy
Edmondson. [Źródło skali i pełne sformułowania](https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Group_Performance/Edmondson%20Psychological%20safety.pdf).

| Pozycja | Skrócona etykieta | Średnia po przeliczeniu |
| --- | --- | ---: |
| 1 (R) | Wypominanie błędów | — |
| 2 | Poruszanie problemów i trudnych tematów | — |
| 3 (R) | Odrzucanie osób z powodu odmienności | — |
| 4 | Swoboda podejmowania ryzyka | — |
| 5 (R) | Trudność proszenia o pomoc | — |
| 6 | Brak celowego utrudniania pracy innym | — |
| 7 | Docenianie i wykorzystywanie indywidualnych umiejętności | — |
| | **Średnia całości** | **—** |

Dla każdej odpowiedzi z pozycji 1, 3 i 5 liczymy `8 − ocena`. Następnie
liczymy średnią dla każdej pozycji i średnią z siedmiu średnich przed
zaokrągleniem. Do repozytorium wpisujemy wyłącznie osiem zagregowanych liczb.

## Prędkość i Sprint 4

Prędkość to suma istniejących estymat Story ukończonych w sprincie.
Dla zamkniętych sprintów granicą jest faktyczny czas zamknięcia Jira.
Dla aktywnego Sprintu 3 wynik jest odczytem wstępnym.

| Sprint | Ukończone Story | Prędkość |
| --- | --- | ---: |
| 1 | SCRUM-5 (8), SCRUM-15 (8), SCRUM-16 (5), SCRUM-83 (3) | 24 SP |
| 2 | SCRUM-91 (5) | 5 SP |
| 3 | Odczyt z 27.11.2026 · 27 zgłoszeń, 11 Story o łącznej estymacie 68 SP, żadna Story w kategorii Gotowe | 0 SP wstępnie |

Odczyt można powtórzyć w Jira dla `project = SCRUM AND issuetype = Story`
z warunkiem `sprint = 1`, `sprint = 3` i `sprint = 4`. Daty statusu Gotowe
należy porównać z datą zamknięcia odpowiedniego sprintu.

Jira pokazuje **FF Sprint 4 - moduły i alerty** (ID 36) jako przyszły sprint.
Obecny cel obejmuje analitykę i alerty, serwis i koszty, ewidencję, karty
paliwowe, wyszukiwanie oraz usprawnienia CD i prywatności. Razem w
sprincie jest **74 SP**, w tym 71 SP Story oraz 3 SP zadania SCRUM-74.
[Tablica Jira](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1).

Przy dotychczasowej najwyższej prędkości 24 SP robocza propozycja dla
Planningu to **21 SP**: SCRUM-7 (8), SCRUM-61 (5) i SCRUM-69 (8).
Proponowany cel to przejście od porównania wykorzystania pojazdu do odczytu
i obsługi jego alertu. Ostateczny zakres, cel, start i ewentualne uzasadnienie
przekroczenia wynikają z decyzji zespołu 28.11.

### Ustalenia do zapisania po spotkaniu

| Pole | Dowód |
| --- | --- |
| Wynik działań z retro S2 | Faktyczne wnioski zespołu i pomiar kolejki z 28.11 |
| Nowe działania | Treść, właściciel, termin i mierzalne sprawdzenie |
| Zamknięcie S3 | Czas zamknięcia Jira, ukończone Story, końcowe SP i linki QA |
| Decyzja S4 | Uzgodniony cel, zakres, SP, pojemność oraz decyzja o przenoszonych pracach |

Odbiory na urządzeniach i decyzję o pull-to-refresh PO przełożył do
Sprintu 4. Wcześniej przejdź zależności kont, historii i kartoteki,
ustal środowisko QA i dobierz zakres do rzeczywistej pojemności zespołu.
