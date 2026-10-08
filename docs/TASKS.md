# Podział pracy w Jirze

Backlog: https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog

Przypisania uzupełniono 7 października 2026; aktualizacja z 8 października obejmuje
przejęcie SCRUM-14 przez Jakuba do sprawdzenia integracji oraz nowe zadania.
Aktualne statusy i przypisania należy sprawdzać w Jirze.
Liczba zadań nie jest miarą nakładu; kolejność i dostępność ustalamy wspólnie.

| Osoba | Obszar | Zadania |
| --- | --- | --- |
| Jakub Czaja | PO, struktura, logowanie, lista floty, opis przejazdu i reguły alertów | SCRUM-1–5, SCRUM-7, SCRUM-11, SCRUM-13, SCRUM-14, SCRUM-16, SCRUM-20, SCRUM-26, SCRUM-31, SCRUM-34, SCRUM-38, SCRUM-41, SCRUM-43 |
| Dawid Hnat | Infrastruktura, WEBFLEET, backend i dane | SCRUM-12, SCRUM-15, SCRUM-18, SCRUM-19, SCRUM-22, SCRUM-24, SCRUM-29, SCRUM-36, SCRUM-39 |
| Jakub Nazarewicz | Mapa, historia i widoki analityki | SCRUM-6, SCRUM-21, SCRUM-25, SCRUM-27, SCRUM-30, SCRUM-32, SCRUM-35, SCRUM-42 |
| Marcel Głowacki | Plan QA, testy funkcji i regresja | SCRUM-17, SCRUM-23, SCRUM-28, SCRUM-33, SCRUM-37, SCRUM-40 |

## Pierwsze prace

- Jakub Czaja: frontend SCRUM-38 czeka na review w PR #6; SCRUM-14 jest w toku
  po sprawdzeniu snapshotu WEBFLEET. SCRUM-34 obejmuje przyjęcie zasad przez zespół.

- Jakub Nazarewicz: [SCRUM-35](https://fleet-flow.atlassian.net/browse/SCRUM-35)
  — szkice trzech widoków i przepływy użytkownika do uzgodnienia z PO.
- Dawid Hnat: [SCRUM-36](https://fleet-flow.atlassian.net/browse/SCRUM-36)
  — projekt modelu danych i API; SCRUM-39 obejmuje FastAPI, bazę i migracje,
  SCRUM-15 synchronizację po zakończeniu spike,
  a SCRUM-12 obejmuje konfigurację zakupionego VPS i test SSH czterech osób.
- Marcel Głowacki: [SCRUM-37](https://fleet-flow.atlassian.net/browse/SCRUM-37)
  — plan testów i dane syntetyczne z ręcznie policzonymi oczekiwaniami;
  SCRUM-40 obejmuje odbiór szablonu i personalizacji z PR #6.

Serwis (SCRUM-41), kierowcy (SCRUM-42) i karty paliwowe (SCRUM-43) pozostają
w backlogu. Nie rozszerzają automatycznie zakresu aktualnego sprintu.

Można już uruchomić frontend i rozwijać jego moduły lokalnie. Podłączenie
danych wymaga wspólnego kontraktu API z SCRUM-36; nie trzeba czekać z pracą
nad UI na VPS. Przy zmianie właściciela aktualizujemy pole osoby i opis w Jirze.
Zasady gałęzi, PR i przeglądu są w [CONTRIBUTING](../CONTRIBUTING.md).
