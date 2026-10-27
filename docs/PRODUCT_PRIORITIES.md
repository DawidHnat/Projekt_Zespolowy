# Priorytety produktu — SCRUM-2

Stan: 27.10.2026. Właściciel decyzji o zakresie: Jakub Czaja, PO.
[Zadanie SCRUM-2](https://fleet-flow.atlassian.net/browse/SCRUM-2).

## Źródło potrzeb i granice potwierdzenia

Zebrano wymagania przekazane przez PO podczas pracy nad projektem: problemy
z odczytem aktualności, prędkości i lokalizacji, trwała historia podróży,
kartoteka pojazdu, ewidencja, kierowcy, serwis, alerty i karty paliwowe.
Ich doprecyzowania są zapisane w opisach zgłoszeń Jiry z 27.10.2026.
PO polecił uporządkować cały backlog, a następnie połączyć plan w pięć sprintów.

Nie udokumentowano osobnej rozmowy z reprezentatywnym kierownikiem floty.
W tej sesji nie było dostępu do takiej osoby; użyto feedbacku PO jako
materiału wejściowego. Poniższe scenariusze są propozycją odbioru produktu,
a nie wynikami badań, odbytego Review lub testów z użytkownikiem.
Nie przypisujemy PO roli zewnętrznego respondenta.

Feedback zbieramy przez pokaz trzech scenariuszy opisanych niżej. PO zapisuje
w odpowiedniej Story obserwowany problem, oczekiwane zachowanie i decyzję
o zmianie kryteriów. Gdy będzie dostępny docelowy użytkownik, należy sprawdzić
z nim tę samą kolejność potrzeb. Brak odpowiedzi nie oznacza akceptacji.

## Trzy najważniejsze potrzeby

| Priorytet | Potrzeba kierownika floty | Scenariusz pracy | Wynik, który można odebrać |
| --- | --- | --- | --- |
| 1 | Szybko znaleźć pojazd i ocenić wiarygodność jego ostatniej pozycji. | Po zalogowaniu wyszukuję rejestrację, filtruję status, wybieram pojazd na liście/mapie i sprawdzam czas pomiaru. | Lista i mapa mają zgodne filtry oraz wybór. Brak GPS/adresu/prędkości jest obsłużony bez fikcyjnego zera. Stary pomiar jest jawnie oznaczony; samo odświeżenie cache nie odmładza pozycji. |
| 2 | Odtworzyć przejazdy i opisać wykorzystanie auta bez przepisywania danych z WEBFLEET. | Wybieram pojazd i dzień lub okres, przeglądam przejazdy i zapisuję cel oraz opis. | Zapisana historia i notatki pozostają po ponownym wejściu. Import nie nadpisuje celu ani opisu użytkownika. Suma okresu i braki danych są jawne. |
| 3 | Porównać wykorzystanie aut i zauważyć przekroczenie ustalonego dystansu. | Wybieram okres do porównania, ustawiam regułę dziennego dystansu i przeglądam alerty. | Agregaty mają jasne jednostki i pokrycie okresu. Ponowne przeliczenie nie tworzy duplikatów alertów. Odczyt alertu nie zmienia faktów źródłowych. |

## Powiązanie z backlogiem i kryteriami

Odczytano opisy Story i ich podział etapów po zapisaniu zmian w Jirze.
Ta kontrola sprawdza spójność wymagań; nie potwierdza implementacji.

| Story | Zakres MVP i sprawdzona granica | Dalsze rozszerzenie |
| --- | --- | --- |
| [SCRUM-5](https://fleet-flow.atlassian.net/browse/SCRUM-5) | Lista/mapa z API, filtry, wybór, rzeczywiste dane oraz jawna aktualność. SCRUM-51 dostarcza podstawowe ręczne metadane, prędkość i dostępny tekst lokalizacji. | Pełna kartoteka, leasing i dodatkowe dane: [SCRUM-68](https://fleet-flow.atlassian.net/browse/SCRUM-68); zdjęcia, daty i skany: [SCRUM-57](https://fleet-flow.atlassian.net/browse/SCRUM-57). |
| [SCRUM-6](https://fleet-flow.atlassian.net/browse/SCRUM-6) | Historia wybranego auta, zakres dat i trwałe przejazdy. Cel/opis i podstawowa suma okresu są osobną Story [SCRUM-62](https://fleet-flow.atlassian.net/browse/SCRUM-62). Import historii pozostaje w SCRUM-24. | Ręczne dodawanie/edycja/usuwanie, filtry i KPI: [SCRUM-71](https://fleet-flow.atlassian.net/browse/SCRUM-71); trwała kolejność i ostrzeżenia: [SCRUM-72](https://fleet-flow.atlassian.net/browse/SCRUM-72). |
| [SCRUM-7](https://fleet-flow.atlassian.net/browse/SCRUM-7) | Reguła dziennego dystansu, lista alertów i odczyt. Porównanie wykorzystania jest osobną Story [SCRUM-61](https://fleet-flow.atlassian.net/browse/SCRUM-61). Scalony backend SCRUM-31 nie zastępuje widoku SCRUM-32 i QA. | Centrum alertów terminowych: [SCRUM-69](https://fleet-flow.atlassian.net/browse/SCRUM-69); kolejka i szablon e-mail: [SCRUM-73](https://fleet-flow.atlassian.net/browse/SCRUM-73). |

Logowanie [SCRUM-16](https://fleet-flow.atlassian.net/browse/SCRUM-16)
i synchronizacja [SCRUM-15](https://fleet-flow.atlassian.net/browse/SCRUM-15)
są warunkami bezpiecznego korzystania z tych funkcji. Ręczna kartoteka
kierowców [SCRUM-42](https://fleet-flow.atlassian.net/browse/SCRUM-42)
wspiera historię i ewidencję; kierowcy nie są importowani z WEBFLEET.

## Zakres obowiązkowy i dalszy rozwój

- **MVP:** bezpieczne logowanie, synchronizacja floty, lista/mapa,
  historia, trwały cel/opis i podstawowe sumy, ręczni kierowcy,
  porównanie wykorzystania oraz alerty dziennego dystansu.
- **Kolejne przyrosty:** pełna kartoteka i dokumenty, olej i terminy,
  centrum alertów, rozbudowana ewidencja, zgodność kategorii kierowcy
  z pojazdem, administracja kontami, profil i e-mail, karty paliwowe,
  importy MOL/ORLEN i raporty CSV.
- **Do dalszego Refinementu:** automatyczne podpowiadanie celu przejazdu,
  SMS i dalsze automatyzacje. Nie są częścią aktualnego zobowiązania MVP.

Istniejące motywy, układ pulpitu i lokalne zdjęcia pozostają częścią aplikacji.
Nowa personalizacja nie wyprzedza brakującej historii, wiarygodności danych
ani odbioru podstawowych funkcji. Zakupione paliwo nie jest automatycznie
rzeczywistym spalaniem; Google Maps z punktami A/B nie udowadnia śladu GPS.

## Plan kolejności po korekcie PO

Źródło statusów i szczegółowego zakresu:
[backlog SCRUM](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog).

| Sprint | Zakres etapu |
| --- | --- |
| 1 — flota i mapa | Domknięcie logowania, synchronizacji, listy/mapy i oznaczania aktualności danych. |
| 2 — historia i auta | Historia i podstawowa ewidencja, kierowcy, kartoteka pojazdu, zdjęcia i dokumenty. |
| 3 — serwis i alerty | Analityka i alerty MVP, wdrożenie/domena, serwis olejowy i centrum terminów. |
| 4 — ewidencja/konta | Rozbudowana ewidencja, kolejność i zgodność uprawnień, konta/profil oraz e-mail. |
| 5 — paliwo i raporty | Karty, anonimowe wzory plików, importy, statystyki i raporty. |

W każdym etapie najpierw domykamy niezbędny zakres i jego QA. Przeniesienie
zadania do sprintu nie oznacza ukończenia ani gwarantowanego terminu.
Daty, dostępność i robocze estymaty przyszłych sprintów potwierdza zespół
na Planningu. Kryterium odbioru pozostaje [Definition of Done](../DEFINITION_OF_DONE.md).

## Odbiór SCRUM-2

| Kryterium zadania | Materiał do sprawdzenia |
| --- | --- |
| Źródło feedbacku lub udokumentowany brak dostępu do reprezentatywnego użytkownika. | Rozdział „Źródło potrzeb i granice potwierdzenia”: feedback PO i metoda zebrania dalszych uwag. |
| Trzy potrzeby i przykładowe scenariusze. | Tabela priorytetów 1–3 z obserwowalnymi wynikami. |
| Spójność SCRUM-5/6/7 i zmian w backlogu. | Tabela powiązań i datowane plany etapów w opisach Jiry. |
| Oddzielenie MVP od dalszych raportów, personalizacji i powiadomień. | Rozdział zakresu i plan kolejności. |

Dokument wymaga niezależnego przeglądu w PR. Po zatwierdzeniu i scaleniu
PO może odebrać rezultat rozpoznawczy SCRUM-2; nie zamyka to powiązanych
Story aplikacji ani nie zastępuje ich QA.
