# Retrospektywa Sprintu 1

Jira: [SCRUM-3](https://fleet-flow.atlassian.net/browse/SCRUM-3).
Stan obserwacji: 26.10.2026. **Materiał roboczy do rozmowy zespołu**, nie protokół
odbytego spotkania. Sprint 1 nadal trwa; feedback uczestników, decyzję o zakończeniu
i końcowe wyniki należy dopisać po rzeczywistym Review i retrospektywie.
Nie uznajemy częściowego kodu ani zielonego CI za ukończoną Story.

## Co poszło dobrze

- Działa wspólny VPS, HTTPS, PostgreSQL i health check. Wersja aplikacji ma
  widoczne siedem znaków SHA, które można porównać z aktualnym `origin/main`.
- `main` jest chroniony, wymagany jest `Required CI`, a kolejne PR-y przechodzą
  budowę frontendu, testy backendu na Pythonie 3.12/3.13 i budowę obrazu API.
- Powstał klikalny prototyp trzech przepływów Sprintu 1 oraz jawne kryteria
  akceptacji i Definition of Done.
- Marcel przygotował 57 scenariuszy i syntetyczne dane w
  [PR #28](https://github.com/DawidHnat/Projekt_Zespolowy/pull/28).
  Dokumentacja przeszła przegląd Jakuba Czai i została scalona 26.10.2026.
  Wszystkie scenariusze pozostają NOT RUN do czasu ich wykonania.

## Co poszło źle

- Review i odbiory są wąskim gardłem: przed tym przeglądem kilka zielonych PR-ów
  czekało na zatwierdzenie. Jira nie miała żadnej ukończonej Story Sprintu 1.
- Autorstwo scalonych PR-ów było skupione na jednej osobie. Po scaleniu #28
  własne PR-y mają Jakub Czaja i Marcel; Dawid i Jakub Nazarewicz nadal muszą
  dostarczyć własne zmiany. Marcel i Nazarewicz potrzebują też review cudzych PR-ów.
- Gotowość infrastruktury nie oznacza gotowości floty. Pierwszy odczyt źródła
  i odbiór synchronizacji są osobną pracą w SCRUM-64/23; bez tych dowodów
  nie można odebrać całego celu sprintu ani udawać danych w aplikacji.
- Wiele elementów rozpoczęto przed pełnym domknięciem wcześniejszych.
  Testy autora, plan QA i właściwy odbiór nie zawsze miały osobne dowody.

## Działania z właścicielami

Poniższe propozycje są już powiązane z pracą w Jirze. Zespół potwierdzi je na
spotkaniu; nie są deklaracją wykonania.

| Działanie | Właściciel | Zgłoszenie | Kiedy i jak sprawdzimy |
| --- | --- | --- | --- |
| Codziennie przeglądać kolejkę PR, uzgodnić pierwszą odpowiedź do 24 h w dniach dostępności i doprowadzać rozpoczętą Story do pełnego DoD przed otwieraniem kolejnej. Prowadzić tabelę rzeczywistych autorów i recenzentów. | Jakub Czaja (PO), wykonanie: cały zespół | [SCRUM-65](https://fleet-flow.atlassian.net/browse/SCRUM-65), 1 SP roboczo, zaplanowane w Sprincie 2 | Uzgodnienie na Planningu S2; w połowie S2 liczba PR bez pierwszego review ponad 24 h i liczba w pełni odebranych Story; ocena na retro S2. |
| Doprowadzić źródło danych na VPS do pierwszego poprawnego odczytu, potem przeprowadzić niezależny odbiór synchronizacji, listy i mapy. | Dawid Hnat — konfiguracja, Marcel Głowacki — QA | [SCRUM-64](https://fleet-flow.atlassian.net/browse/SCRUM-64) i [SCRUM-23](https://fleet-flow.atlassian.net/browse/SCRUM-23) | Przed końcowym odbiorem celu Sprintu 1: odpowiedź floty 200, prawdziwe czasy aktualności, raport QA z SHA i bez danych klienta w publicznych dowodach. Żywe API wymaga osobnego uzgodnienia. |

Uruchomienie Sprintu 2, termin spotkania i feedback pozostają do odnotowania
po ich faktycznym wykonaniu. [Scenariusz Review](../SPRINT_1_REVIEW.md).
