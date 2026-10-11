# Podział pracy w Jirze

Backlog: https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog

Stan dokumentacji: 9 października 2026. PR-y #5–18 scalono do `main` po
przeglądzie kodu i sprawdzeniu CI, zachowując autorów commitów. Nowe gałęzie
zadań tworzymy z aktualnego `main`. Aktualne statusy i przypisania sprawdzamy
w Jirze; scalenie częściowego przyrostu nie oznacza ukończenia całej Story.

## Scalona podstawa

| Zadanie | Scalony zakres | PR | Pozostała praca |
| --- | --- | --- | --- |
| SCRUM-12 | Konta SSH OVH i instrukcje zespołu | [#5](https://github.com/DawidHnat/Projekt_Zespolowy/pull/5) | Klucze i własne testy trzech pozostałych osób |
| SCRUM-38 | Pulpit, wygląd i edycja układu | [#6](https://github.com/DawidHnat/Projekt_Zespolowy/pull/6) | QA SCRUM-40 |
| SCRUM-14 | Adapter i diagnostyka WEBFLEET/SMTP | [#7](https://github.com/DawidHnat/Projekt_Zespolowy/pull/7) | Potwierdzenie jednostek i pól; prędkość do tego czasu pozostaje null |
| SCRUM-36 | Model danych i kontrakt API | [#8](https://github.com/DawidHnat/Projekt_Zespolowy/pull/8) | Uzgadnianie kontraktu kolejnych pól w zadaniach |
| SCRUM-39 | FastAPI, PostgreSQL, migracje, health i CI | [#9](https://github.com/DawidHnat/Projekt_Zespolowy/pull/9) | Sprawdzenie uruchomienia na komputerach zespołu |
| SCRUM-16 | Logowanie i sesje | [#10](https://github.com/DawidHnat/Projekt_Zespolowy/pull/10) | QA SCRUM-56; HTTPS na VPS w SCRUM-18 |
| SCRUM-15 | Cache pojazdów i pomiarów, upsert, limit i obsługa awarii | [#11](https://github.com/DawidHnat/Projekt_Zespolowy/pull/11) | QA synchronizacji; historia w SCRUM-24 |
| SCRUM-19 | Chroniona lista, szczegóły, GeoJSON i wskaźniki | [#12](https://github.com/DawidHnat/Projekt_Zespolowy/pull/12) | QA SCRUM-23 |
| SCRUM-20 | Frontend logowania i lista z API | [#13](https://github.com/DawidHnat/Projekt_Zespolowy/pull/13) | QA SCRUM-23 |
| SCRUM-21 | Mapbox, wybór pojazdu i wspólne filtry | [#14](https://github.com/DawidHnat/Projekt_Zespolowy/pull/14) | QA SCRUM-23 |
| SCRUM-44 | Opcjonalny reset hasła przez SMTP | [#15](https://github.com/DawidHnat/Projekt_Zespolowy/pull/15) | QA SCRUM-56; uzgodniony odbiorca i test faktycznej dostawy później |
| SCRUM-45 | Zdjęcia, kafelki pojazdów, znaczniki bez grupowania i Ustawienia | [#16](https://github.com/DawidHnat/Projekt_Zespolowy/pull/16) | QA zdjęć, motywów i mapy |
| SCRUM-46 | Zbiorowa edycja rozmiarów i wspólna paginacja list | [#17](https://github.com/DawidHnat/Projekt_Zespolowy/pull/17) | QA układu, zaznaczania i stronicowania |
| SCRUM-25 | Mały podgląd pojazdu, zakładki szczegółów i wybór dnia | [#18](https://github.com/DawidHnat/Projekt_Zespolowy/pull/18) | Ręczna kartoteka, treść zakładek, historia SCRUM-24 i QA SCRUM-28 |

Kierowcy są wprowadzani ręcznie. Integracja nie pobiera ich z WEBFLEET
i nie nadpisuje lokalnych przypisań. Adres e-mail konta aplikacji jest opcjonalny;
diagnostyka SMTP nie wysyła wiadomości. Historia przejazdów i geometria trasy
nie są jeszcze pobierane; przygotowane widoki mają pusty stan.

## Następne przyrosty

SCRUM-31 (Jakub Czaja) dodaje backend reguł **dziennego dystansu**, trwałe
alerty i odczyt per użytkownik. Dystans z odebranych pomiarów ma jawne niepełne
pokrycie; nie jest wartością licznika. Szczegóły i przypadki odbioru:
[QA SCRUM-31](qa/SCRUM-31.md). Frontend SCRUM-32 i odbiór Marcel/SCRUM-33
pozostają osobnymi zadaniami; samo dodanie API ich nie zamyka.

| Osoba | Obszar najbliższej pracy |
| --- | --- |
| Jakub Czaja | Odbiór produktu i zakres kolejnego przyrostu; SCRUM-57 — terminy i dokumenty pojazdu |
| Dawid Hnat | SCRUM-14 — mapowanie źródła; SCRUM-51 — API ręcznej kartoteki; SCRUM-58 — API terminów i załączników; SCRUM-24 — historia; SCRUM-12/18 — SSH i HTTPS |
| Jakub Nazarewicz | SCRUM-25 — formularz kartoteki i szczegóły; SCRUM-59 — UI terminów i załączników; dalsze widoki historii i ręcznych kierowców |
| Marcel Głowacki | SCRUM-23 — lista/mapa; SCRUM-28 — kartoteka; SCRUM-40 — wygląd/układ; SCRUM-56 — logowanie/reset; SCRUM-60 — terminy i dokumenty |

SCRUM-51/25 obejmują markę, model, rok produkcji, VIN, typ pojazdu i przebieg.
Kartoteka jest zarządzana ręcznie; potwierdzone pola WEBFLEET mogą pomóc w
początkowym uzupełnieniu pustych wartości, ale synchronizacja nie nadpisuje
wpisów użytkownika. Przebieg z pomiaru ma osobne źródło i czas odczytu.

SCRUM-57 oraz podzadania 58/59/60 obejmują datę następnego przeglądu,
ważność polisy i prywatne załączniki. Szczegółowe kryteria, typy plików i limity
są zapisane w Jirze. Daty i dokumenty nie pochodzą z WEBFLEET.

Serwis, ręczni kierowcy i karty paliwowe pozostają dalszymi modułami.
Backlog nie rozszerza automatycznie zakresu sprintu. Każda osoba wybiera
przypisane zadanie z uzgodnionym zakresem i rozwija je na osobnej gałęzi.

Instrukcja uruchomienia: [GETTING_STARTED](GETTING_STARTED.md).
Zasady gałęzi, PR, przeglądu i odbioru: [CONTRIBUTING](../CONTRIBUTING.md).
