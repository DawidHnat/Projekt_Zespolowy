# Plan backlogu MVP — aktualizacja 27.10.2026

Źródłem bieżącego statusu pozostaje [backlog SCRUM](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog).
Kolejność ośmiu Story MVP zachowuje zależności: logowanie i synchronizacja,
lista/mapa, historia i opisy, analityka/alerty oraz ręczna kartoteka kierowców.
Punkty to robocza względna złożoność, a nie godziny. Opisy i estymaty są w Jirze.

27.10.2026 na polecenie PO rozplanowano cały backlog, wydzielono rozszerzenia
SCRUM-68–76, a następnie połączono plan w pięć sprintów. Cztery opróżnione
sprinty 6–9 usunięto po wyraźnym potwierdzeniu PO. Zgłoszenia, ich właściciele,
estymaty i statusy pozostały zachowane; podzadania są razem z rodzicami.

Trzy Story Sprintu 1 nadal mają 21 SP. Suma jego wycenionych zgłoszeń głównych
wynosi 27 SP po uwzględnieniu wsparcia SCRUM-64/66. Nie sumujemy punktów
podzadań ponownie. Zasady i kolejka QA: [estymaty i testowanie](ESTIMATION_AND_QA.md).

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

## Podział pracy w Sprincie 1

| Osoba | Odpowiedzialność |
| --- | --- |
| Jakub Czaja | Logowanie SCRUM-16, PO i planowanie, kontrakt API SCRUM-36, kalendarz SCRUM-66 oraz własne przyrosty listy/układu |
| Dawid Hnat | Synchronizacja SCRUM-15, mapowanie źródła SCRUM-14, API i infrastruktura, uruchomienie odczytu VPS SCRUM-64 |
| Jakub Nazarewicz | Lista/mapa SCRUM-5, mapa SCRUM-21, aktualność SCRUM-22 i przepływy/prototyp SCRUM-35 |
| Marcel Głowacki | Plan QA SCRUM-37, odbiory SCRUM-23/40/56 |

Sprint ma 16 zgłoszeń głównych. Podstawowe trzy Story nie są ukończone przez
samo scalenie ich fragmentów. Materiały organizacyjne i wspólny kalendarz są
pracą wspierającą; nie tworzą kolejnych głównych funkcji MVP.

## Aktualny plan pięciu sprintów

Wartości obejmują pola zgłoszeń głównych; podzadań nie liczymy drugi raz.
Nowe wyceny są robocze, do potwierdzenia na Planningu. Połączenie etapów
zwiększa zakres sprintów i nie gwarantuje wykonania całej listy w pięciu
cyklach po dwa tygodnie. Przyszłe daty i długość ustala zespół.

| Sprint | Zgłoszenia główne | SP w polach | Cel etapu |
| --- | --- | --- | --- |
| 1 — flota i mapa | 16 | 27 | Logowanie, synchronizacja, lista/mapa i jawna aktualność; dotychczasowe daty 24.10–7.11.2026. |
| 2 — historia i auta | 7 | 38 | Historia, podstawowa ewidencja, ręczni kierowcy, pełna kartoteka, zdjęcia i dokumenty; odbiór SCRUM-63, usprawnienie po retro SCRUM-65. |
| 3 — serwis i alerty | 7 | 32 | Analityka i alerty dystansu, regresja, wdrożenie/domena SCRUM-67, olej i centrum terminów. |
| 4 — ewidencja/konta | 6 | 39 | Ręczne wpisy, filtry i kolejność tras, zgodność uprawnień, konta/profil oraz trwałe e-maile. |
| 5 — paliwo i raporty | 5 | 32 | Karty paliwowe, anonimowe wzory MOL/ORLEN, import i deduplikacja, statystyki i CSV. |

Sprint 1 jest jedynym aktywnym. Sprinty 2–5 pozostają planowane bez dat.
Przed startem trzeba potwierdzić dostępność w danym okresie i terminy spotkań;
orientacyjne godziny w kontrakcie nie zastępują tego uzgodnienia. Ten dokument
nie deklaruje odbycia Planningu, Review, retro ani zaliczenia QA.

### Sprint 2 — kolejność wykonania

| Zgłoszenie | Właściciel | SP | Powiązania |
| --- | --- | --- | --- |
| SCRUM-6 — historia | Jakub Nazarewicz | 8 | API SCRUM-24 Dawida; UI SCRUM-25; QA SCRUM-28 Marcela |
| SCRUM-62 — podstawowa ewidencja | Jakub Czaja | 5 | Cel/opis SCRUM-26; sumy SCRUM-27 Nazarewicza |
| SCRUM-42 — ręczni kierowcy | Dawid Hnat | 8 | API SCRUM-52; UI SCRUM-53 Nazarewicza; QA SCRUM-54 Marcela |
| SCRUM-57 — zdjęcia, daty i dokumenty | Jakub Czaja | 8 | API SCRUM-58 Dawida; UI SCRUM-59 Nazarewicza; QA SCRUM-60 Marcela |
| SCRUM-68 — pełna kartoteka/leasing | Dawid Hnat | 8 | Wspólne pola i zdjęcie z SCRUM-57; UI Nazarewicza, odbiór Marcela |
| SCRUM-63 — odbiór przekrojowy | Marcel Głowacki | — | Historia, ewidencja i kierowcy; nie zastępuje końcowej regresji SCRUM-17 |
| SCRUM-65 — usprawnienie z retro | Jakub Czaja | 1 | Codzienne review PR i kompletne dowody DoD; potwierdzenie na rzeczywistej retrospektywie |

### Granice rozszerzeń

- SCRUM-5/51: podstawowe metadane i rzeczywista telemetria w Sprincie 1.
  Pełny formularz, leasing i dodatkowe dane są w SCRUM-68 (Sprint 2).
- SCRUM-42/52/53/54: ręczna kartoteka i przypisania w Sprincie 2.
  Egzekwowanie macierzy uprawnień kierowca–pojazd: SCRUM-70 (Sprint 4).
- SCRUM-62/26/27: trwały cel/opis i podstawowe sumy w Sprincie 2.
  Rozbudowane CRUD, filtry i KPI: SCRUM-71; kolejność i ostrzeżenia:
  SCRUM-72 (Sprint 4).
- SCRUM-7/32/33: alerty dziennego dystansu w Sprincie 3. Centrum terminów:
  SCRUM-69 w tym samym sprincie, e-mail: SCRUM-73 w Sprincie 4.
- SCRUM-43: rejestr kart w Sprincie 5. Anonimowe wzory SCRUM-74 poprzedzają
  import SCRUM-75; statystyki SCRUM-76 korzystają z potwierdzonych danych.

W opisach zachowano wcześniejsze wymagania i dodano datowane granice etapów.
Domyślne progi pilności, macierz uprawnień i formaty MOL/ORLEN trzeba
potwierdzić przed implementacją odpowiedniego zakresu. Automatyczne
podpowiadanie celu przejazdu pozostaje pomysłem do dalszego Refinementu.

## Uzgodnienia z plikiem wymagań

Punkt 16 `wymagania.txt` przewiduje pobieranie kierowców z WEBFLEET,
co jest sprzeczne z dotychczasową decyzją PO i `AGENTS.md`. Zachowano
ręczne wprowadzanie kierowców; import wymaga osobnego uzgodnienia.
Raporty i CSV mają już SCRUM-50 zależne od historii, agregacji i kartoteki;
nie dodano drugiego zgłoszenia o tym samym zakresie.

Serwis, karty paliwowe, eksporty, rozbudowana administracja i dokumenty
pozostają rozszerzeniami MVP, z miejscem w planowanych Sprintach 2–5.
Plan w Jirze nie potwierdza ich implementacji ani nie rozszerza automatycznie
bieżącego zobowiązania Sprintu 1.
