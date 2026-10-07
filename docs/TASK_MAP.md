# Zadania i odpowiedzialność

To mapa kodu do istniejącego [backlogu SCRUM](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog).
Zgłoszenia odczytano w przeglądarce 7 października 2026; nie zmieniono ich statusów.
Przykład `SCRUM-123` w instrukcjach należy zastąpić kluczem swojego zadania.
Ten fundament odpowiada [SCRUM-13: Szkielet React, FastAPI i PostgreSQL oraz CI](https://fleet-flow.atlassian.net/browse/SCRUM-13).

| Zadanie | Katalogi | Proponowany pierwszy zakres |
| --- | --- | --- |
| [SCRUM-5: Lista i mapa floty](https://fleet-flow.atlassian.net/browse/SCRUM-5) | `frontend/src/features/fleet`, `backend/app/modules/fleet` | Lista z API, filtry, status i wybór pojazdu; następnie rzeczywista mapa |
| [SCRUM-6: Szczegóły, historia pojazdu i ewidencja przebiegu](https://fleet-flow.atlassian.net/browse/SCRUM-6) | `frontend/src/features/trips`, `backend/app/modules/trips` | Historia z API, trwały zapis celu i opisu; następnie import tras |
| [SCRUM-7: Analityka i alerty](https://fleet-flow.atlassian.net/browse/SCRUM-7) | `frontend/src/features/analytics`, `backend/app/modules/analytics` | Zestawienie z bazy, okresy i zdefiniowane reguły alertów |
| [SCRUM-14: Spike WEBFLEET](https://fleet-flow.atlassian.net/browse/SCRUM-14) i [SCRUM-15: Integracja WEBFLEET](https://fleet-flow.atlassian.net/browse/SCRUM-15) | `backend/app/integrations/webfleet` | Zweryfikować importer pojazdów na koncie zespołu; dodać import historii |
| [SCRUM-13: Szkielet i CI](https://fleet-flow.atlassian.net/browse/SCRUM-13) | `contracts`, `frontend/src/shared/api`, `compose.yaml`, `.github` | Pydantic + OpenAPI + TypeScript, powtarzalny start, migracje, testy i review |
| [SCRUM-17: Regresja MVP](https://fleet-flow.atlassian.net/browse/SCRUM-17) | `backend/tests`, testy frontendu | Scenariusze akceptacyjne każdej Story; błędy API, brak danych, zapis i regresje |
| [SCRUM-18: Wdrożenie MVP](https://fleet-flow.atlassian.net/browse/SCRUM-18) | `infra`, późniejsza konfiguracja produkcyjna | Kopia bazy, wdrożenie i instrukcja odtworzenia |
| [SCRUM-34: Zasady Scrum i DoD](https://fleet-flow.atlassian.net/browse/SCRUM-34) | `CONTRIBUTING.md`, `docs/WORKFLOW.md`, `AGENTS.md` | Przyjęcie procesu przez zespół i rytm przeglądów |

W SCRUM-13 wymagane są lokalny start wszystkich trzech usług, migracje i health,
podstawowy kontrakt API, CI sprawdzający TypeScript, analizę kodu i istotne testy,
konfiguracja bez sekretów w Git oraz review przez innego developera i potwierdzenie QA.
Ten PR dostarcza fundament; review zespołu i QA pozostają osobnymi krokami.

## Role z kontraktu

| Osoba | Odpowiedzialność w procesie |
| --- | --- |
| Jakub Czaja / `jczaja51` | PO i developer: priorytet, kryteria akceptacji, decyzje produktu i review |
| Dawid Hnat / `DawidHnat` | Infrastruktura i developer: Compose, VPS, konfiguracja repo i automatyzacji |
| Jakub Nazarewicz / `jnazarewiczs` | Developer: implementacja funkcji i przegląd zmian drugiego developera |
| Marcel Głowacki / `mglowacki0` | QA: scenariusze, przypadki brzegowe, potwierdzenie kryteriów i regresje |

To wskazówki do planowania. Przydział konkretnej Story pozostaje w Jirze
i może być zmieniony zgodnie z kontraktem. Role nie blokują pracy innej osoby
w danym katalogu. CODEOWNERS wskazuje osoby do przeglądu wspólnych zmian.

## Jak rozdzielać pracę bez konfliktów

1. Jedna osoba bierze konkretne zadanie i przenosi je do realizacji w Jirze.
2. W Story uzgadniacie pola API i kryteria akceptacji przed niezależną pracą UI i API.
3. Każda osoba ma własną gałąź zadania. Nie wykonujecie codziennych pushów do `main`.
4. Zmiany wspólnego kontraktu, migracji, lockfile i routingu zgłaszacie w PR
   jako takie; druga osoba najpierw pobiera aktualny `main`.
5. Podział Story na mniejsze zadania jest lepszy niż jeden PR zmieniający
   jednocześnie wszystkie trzy funkcje.
6. Po scaleniu sprawdzacie kryteria Story i dopiero wtedy oznaczacie ją jako gotową.
   Sam zielony CI nie dowodzi ukończenia całej Story.

Codzienny przykład procesu jest w [CONTRIBUTING.md](../CONTRIBUTING.md).
