# Plan backlogu MVP — aktualizacja 24.10.2026

Źródłem bieżącego statusu pozostaje [backlog SCRUM](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog).
Poniższą bazową kolejność ustawiono w Jirze i sprawdzono 23.10.2026
po odświeżeniu tablicy. Podział pracy i plan Sprintu 2 zaktualizowano
24.10.2026 zgodnie z sekcjami poniżej.
Porządkuje zależności przyrostów; punkty to względna
złożoność, a nie godziny. Estymaty wpisano do pól Story point estimate.
Każda z ośmiu Story ma formę Jako/chcę/aby oraz listę co najmniej czterech
kryteriów akceptacji w opisie.

Przegląd 24–25.10 uzupełnił również 30 podzadań o robocze estymaty,
uzasadnienia i zasady ich odrębnego liczenia. Logowanie i szkielet oraz
trzy zadania odbioru są w fazie Testowanie. Szczegóły, zapisane punkty,
kolejka QA i ocena obecnej bazy: [estymaty i testowanie](ESTIMATION_AND_QA.md).

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
SCRUM-26/27 należą do SCRUM-62, a SCRUM-29/30 do SCRUM-61. SCRUM-62
pozostaje w planowanym Sprincie 2 razem z historią, a SCRUM-61 w planowanym
Sprincie 3 przed alertami. Na polecenie PO 24.10.2026 SCRUM-42 przeniesiono
z dalszego backlogu do planowanego Sprintu 2; estymata pozostaje 8 SP.

## Sprint 1

Istniejący **FF Sprint 1 - flota i mapa** jest aktywny i obejmuje trzy Story:
SCRUM-16, SCRUM-15 oraz SCRUM-5, łącznie 21 SP. [Prototyp](PROTOTYPE.md) ma osobny nazwany
przepływ dla każdej z nich. Zadania infrastruktury i QA pozostają wsparciem
tych historyjek.

Zapisany cel: zalogowany kierownik floty widzi na wspólnym VPS listę i mapę
pojazdów z synchronizacją WEBFLEET oraz jawną aktualnością danych; zakres
obejmuje trzy Story i wspierające zadania szkieletu, infrastruktury i QA.

Na polecenie PO 24.10.2026 zapisano nowy zakres sprintu:
**24.10.2026, godz. 18:33 – 7.11.2026, godz. 18:33** (Europe/Warsaw).
Początek odpowiada dacie zmiany już aktywnego sprintu, a koniec przypada
dwa tygodnie później. Daty i obie godziny sprawdzono po ponownym otwarciu
formularza w Jirze; zachowano godzinę lokalną mimo zmiany czasu.
Zaktualizowano daty istniejącego sprintu; Jira zachowała aktywny status,
cel, trzy Story oraz historię. Zmiana dat nie oznacza odbioru historyjek.

## Podział pracy — 24.10.2026

Główne przypisania Sprintu 1 pokazują pracę całej czwórki:

| Osoba | Odpowiedzialność w Sprincie 1 |
| --- | --- |
| Jakub Czaja | SCRUM-16 — logowanie; PO, kontrakt i zasady ukończenia |
| Dawid Hnat | SCRUM-15 — synchronizacja; API i infrastruktura |
| Jakub Nazarewicz | SCRUM-5 — właściciel listy i mapy; SCRUM-21 — mapa |
| Marcel Głowacki | SCRUM-37 — plan QA; odbiór w SCRUM-23/40/56 |

SCRUM-37 przeniesiono z backlogu do Sprintu 1. Sprint ma teraz dziewięć
zgłoszeń głównych, w tym te same trzy Story o łącznej estymacie 21 SP.
Zachowano wykonawców podzadań i ich stany; zmiana właściciela Story
nie przepisuje autorstwa dotychczasowej implementacji ani nie oznacza Done.

## Plan Sprintu 2

**FF Sprint 2 - historia** pozostaje planowany, bez dat i bez uruchamiania.
Cel obejmuje historię pojazdu, trwały cel/opis i sumę okresu oraz ręczną
kartotekę kierowców. Trzy Story mają razem **21 SP**:

| Zgłoszenie | Właściciel przyrostu | SP | Podzadania |
| --- | --- | --- | --- |
| [SCRUM-6](https://fleet-flow.atlassian.net/browse/SCRUM-6) — historia | Jakub Nazarewicz | 8 | API SCRUM-24 — Dawid; UI SCRUM-25 — Nazarewicz; QA SCRUM-28 — Marcel |
| [SCRUM-62](https://fleet-flow.atlassian.net/browse/SCRUM-62) — ewidencja | Jakub Czaja | 5 | Cel/opis SCRUM-26 — Czaja; podsumowanie SCRUM-27 — Nazarewicz |
| [SCRUM-42](https://fleet-flow.atlassian.net/browse/SCRUM-42) — ręczni kierowcy | Dawid Hnat | 8 | API SCRUM-52 — Dawid; UI SCRUM-53 — Nazarewicz; QA SCRUM-54 — Marcel |

Dodano [SCRUM-63](https://fleet-flow.atlassian.net/browse/SCRUM-63), zadanie
Marcela dotyczące przekrojowego odbioru historii, ewidencji i ręcznych
kierowców. Ma pięć kryteriów akceptacji, zależności od implementacji
i odbiorów SCRUM-28/54 oraz stan Do zrobienia. Nie ma osobnych SP,
aby nie dublować estymat Story. Nie zastępuje końcowej regresji MVP SCRUM-17.
Sprint 2 ma cztery zgłoszenia główne oraz osiem podzadań w trzech Story.
Ostateczny zakres wymaga potwierdzenia dostępności zespołu na Planningu.

## Uzgodnienia z plikiem wymagań

Punkt 16 `wymagania.txt` przewiduje pobieranie kierowców z WEBFLEET,
co jest sprzeczne z dotychczasową decyzją PO i `AGENTS.md`. Zachowano
ręczne wprowadzanie kierowców; import wymaga osobnego uzgodnienia.
Raporty i CSV mają już SCRUM-50 zależne od historii, agregacji i kartoteki;
nie dodano drugiego zgłoszenia o tym samym zakresie.

Poza tym zakresem pozostają m.in. serwis, karty paliwowe, eksporty,
rozbudowana administracja kontami i dokumenty pojazdów. Ich istniejące
zgłoszenia zachowano jako dalszy backlog produktu.
