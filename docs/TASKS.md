# Podział pracy w Jirze

Backlog: https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog

Przypisania uzupełniono 7 października 2026; aktualizacja z 8 października obejmuje
przejęcie SCRUM-14 i SCRUM-36 przez Jakuba oraz zależne PR-y implementacji.
Aktualne statusy i przypisania należy sprawdzać w Jirze.
Liczba zadań nie jest miarą nakładu; kolejność i dostępność ustalamy wspólnie.

| Osoba | Obszar | Zadania |
| --- | --- | --- |
| Jakub Czaja | PO, struktura, kontrakt API, logowanie, lista floty, opis przejazdu i reguły alertów | SCRUM-1–5, SCRUM-7, SCRUM-11, SCRUM-13, SCRUM-14, SCRUM-16, SCRUM-20, SCRUM-26, SCRUM-31, SCRUM-34, SCRUM-36, SCRUM-38, SCRUM-41, SCRUM-43, SCRUM-44 |
| Dawid Hnat | Infrastruktura, WEBFLEET, backend i dane | SCRUM-12, SCRUM-15, SCRUM-18, SCRUM-19, SCRUM-22, SCRUM-24, SCRUM-29, SCRUM-39 |
| Jakub Nazarewicz | Mapa, historia i widoki analityki | SCRUM-6, SCRUM-21, SCRUM-25, SCRUM-27, SCRUM-30, SCRUM-32, SCRUM-35, SCRUM-42 |
| Marcel Głowacki | Plan QA, testy funkcji i regresja | SCRUM-17, SCRUM-23, SCRUM-28, SCRUM-33, SCRUM-37, SCRUM-40 |

## Przyrost gotowy do przeglądu

Jakub Czaja przygotował poniższe implementacje. Dawid i Jakub Nazarewicz
sprawdzają kod w swoich obszarach, a Marcel wykonuje odbiór funkcjonalny.
PR-y zależą od siebie: sprawdzamy je od najstarszej bazy, zgodnie z CONTRIBUTING.
Zielone CI nie zastępuje review i QA; zadania nie są jeszcze ukończone.

| Zadanie | Przygotowany zakres | PR | Następny krok |
| --- | --- | --- | --- |
| SCRUM-38 | Dashboard, wygląd i edycja układu | [#6](https://github.com/DawidHnat/Projekt_Zespolowy/pull/6) | Review frontendu, QA SCRUM-40 |
| SCRUM-14 | Diagnostyka WEBFLEET i SMTP, rozpoznanie raportów | [#7](https://github.com/DawidHnat/Projekt_Zespolowy/pull/7), draft | Potwierdzenie jednostki prędkości snapshotu; do tego czasu API zwraca null |
| SCRUM-36 | Model danych i kontrakt API | [#8](https://github.com/DawidHnat/Projekt_Zespolowy/pull/8) | Review Dawida i Jakuba Nazarewicza |
| SCRUM-39 | FastAPI, PostgreSQL, migracje, health i CI | [#9](https://github.com/DawidHnat/Projekt_Zespolowy/pull/9) | Review Dawida, QA backendu |
| SCRUM-16 | Logowanie i sesje chroniące dane floty | [#10](https://github.com/DawidHnat/Projekt_Zespolowy/pull/10), draft | Review oraz HTTPS na VPS w zadaniu infrastruktury; QA SCRUM-17 |
| SCRUM-15 | Cache pojazdów i pomiarów, upsert, limit i obsługa awarii | [#11](https://github.com/DawidHnat/Projekt_Zespolowy/pull/11), draft | Review Dawida i kolejny przyrost synchronizacji historii |
| SCRUM-19 | Chroniona lista, szczegóły, GeoJSON i wskaźniki | [#12](https://github.com/DawidHnat/Projekt_Zespolowy/pull/12) | Review Dawida, QA SCRUM-23 |
| SCRUM-20 | Frontend logowania i lista z rzeczywistego API | [#13](https://github.com/DawidHnat/Projekt_Zespolowy/pull/13) | Review Jakuba Nazarewicza, QA SCRUM-23; zależy też od #6 |
| SCRUM-21 | Mapbox, klastry, wybór pojazdu i wspólne filtry | [#14](https://github.com/DawidHnat/Projekt_Zespolowy/pull/14) | Review Jakuba Nazarewicza, QA SCRUM-23 |
| SCRUM-44 | Opcjonalny reset hasła przez SMTP, podzadanie SCRUM-16 | [#15](https://github.com/DawidHnat/Projekt_Zespolowy/pull/15), draft | Review Dawida i QA Marcela; adres konta oraz test faktycznej dostawy później |

Kierowcy są wprowadzani ręcznie w SCRUM-42. Integracja nie pobiera ich z
WEBFLEET i nie nadpisuje lokalnych przypisań. SMTP ma sprawdzone logowanie;
przy diagnostyce nie wysyłamy wiadomości. Adres e-mail konta aplikacji jest
opcjonalny i może pozostać pusty podczas pracy nad pierwszą wersją.

W SCRUM-25 przygotowano częściowy przyrost UI: panel pojazdu na mapie z
czterema zakładkami oraz wybór dnia w Ostatnich przejazdach i Podróżach.
PO wybrał na tym etapie wygląd i zakładki. Historia z API, wybór przejazdu
i geometria trasy pozostają dalszą pracą w SCRUM-24/25; nie oznacza to
ukończenia całego zadania. Kierowcy nadal będą wprowadzani ręcznie.

## Dalsze prace

- Dawid: review backendu oraz SCRUM-12 — VPS, HTTPS i dostęp SSH zespołu.
- Jakub Nazarewicz: review listy/mapy, potem historia i ręczne zarządzanie kierowcami.
- Marcel: SCRUM-17 (logowanie, wygaśnięcie sesji, reset), SCRUM-23 (lista i mapa),
  SCRUM-40 (wygląd i układ); scenariusze oraz dane syntetyczne w SCRUM-37.
- Jakub: odbiór produktu, ustalenie kolejnego przyrostu i SCRUM-34 — przyjęcie zasad.

Serwis (SCRUM-41), kierowcy (SCRUM-42) i karty paliwowe (SCRUM-43) pozostają
w backlogu. Nie rozszerzają automatycznie zakresu aktualnego sprintu.

Można już uruchomić lokalnie bazę, API oraz frontend i rozwijać moduły według
kontraktu z SCRUM-36. Nie trzeba czekać na VPS. Przy zmianie właściciela
aktualizujemy pole osoby i opis w Jirze.
Zasady gałęzi, PR i przeglądu są w [CONTRIBUTING](../CONTRIBUTING.md).
