# Plan backlogu MVP — 20.10.2026

Źródłem bieżącego statusu pozostaje [backlog SCRUM](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog).
Poniższa kolejność porządkuje zależności przyrostów; punkty to względna
złożoność, a nie godziny. Estymaty wpisano do pól Story point estimate.
Każda z ośmiu Story ma formę Jako/chcę/aby oraz listę co najmniej czterech
kryteriów akceptacji w opisie.

| Kolejność planu | Story | Przyrost | SP |
| --- | --- | --- | --- |
| 1 | [SCRUM-16](https://fleet-flow.atlassian.net/browse/SCRUM-16) | Logowanie i ograniczenie dostępu do floty | 5 |
| 2 | [SCRUM-15](https://fleet-flow.atlassian.net/browse/SCRUM-15) | Synchronizacja pojazdów i pomiarów WEBFLEET | 8 |
| 3 | [SCRUM-5](https://fleet-flow.atlassian.net/browse/SCRUM-5) | Lista, mapa i filtrowanie floty | 8 |
| 4 | [SCRUM-6](https://fleet-flow.atlassian.net/browse/SCRUM-6) | Historia przejazdów wybranego pojazdu | 8 |
| 5 | [SCRUM-62](https://fleet-flow.atlassian.net/browse/SCRUM-62) | Cel, opis przejazdu i podsumowanie okresu | 5 |
| 6 | [SCRUM-61](https://fleet-flow.atlassian.net/browse/SCRUM-61) | Porównanie wykorzystania pojazdów | 5 |
| 7 | [SCRUM-7](https://fleet-flow.atlassian.net/browse/SCRUM-7) | Reguła dziennego dystansu i lista alertów | 8 |
| 8 | [SCRUM-42](https://fleet-flow.atlassian.net/browse/SCRUM-42) | Ręczna kartoteka kierowców i przypisania | 8 |

## Podział dużych historyjek

- Dawne SCRUM-6 (13 SP) rozdzielono na historię SCRUM-6 (8 SP) oraz
  ewidencję SCRUM-62 (5 SP). Trwałość celów i opisów, autor i czas edycji,
  niezmienność pomiarów oraz suma okresu pozostają w kryteriach SCRUM-62.
  SCRUM-24/25 dotyczą historii, SCRUM-26/27 ewidencji; SCRUM-28 sprawdza
  oba przyrosty.
- Dawne SCRUM-7 (13 SP) rozdzielono na analitykę SCRUM-61 (5 SP) oraz
  alerty SCRUM-7 (8 SP). Agregaty i porównanie SCRUM-29/30 dotyczą
  analityki; SCRUM-31/32 dotyczą alertów, a SCRUM-33 ich odbioru QA.
  Istniejący kod backendu alertów nie oznacza ukończenia widoku.
- Nowe Story należą do istniejących epików SCRUM-9 i SCRUM-10.
  Zachowano historię, autorów i stany istniejących zgłoszeń.

Przypisania rodziców czterech wydzielonych podzadań są zapisane i sprawdzone:
SCRUM-26/27 należą do SCRUM-62, a SCRUM-29/30 do SCRUM-61. Kolejność Rank
w Jirze wymaga jeszcze końcowego ustawienia. Powyższa tabela opisuje plan
kolejności; nie stanowi potwierdzenia zmiany pola Rank.

## Sprint 1

Istniejący **FF Sprint 1 - flota i mapa** jest aktywny i obejmuje trzy Story:
SCRUM-16, SCRUM-15 oraz SCRUM-5. [Prototyp](PROTOTYPE.md) ma osobny nazwany
przepływ dla każdej z nich. Zadania infrastruktury i QA pozostają wsparciem
tych historyjek.

Zapisany termin sprintu, 19.10.2026, minął. PO powinien uzgodnić dalszy
termin i aktualizację celu; nie resetowano sprintu ani jego historii.
Wymagany rezultat celu: zalogowany kierownik widzi listę i mapę floty
z synchronizacją oraz jawną aktualnością danych na wspólnym VPS.

Poza tym zakresem pozostają m.in. serwis, karty paliwowe, eksporty,
rozbudowana administracja kontami i dokumenty pojazdów. Ich istniejące
zgłoszenia zachowano jako dalszy backlog produktu.
