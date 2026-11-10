# Review Sprintu 1 — pokaz na podstawie historyjek

Jira: [SCRUM-3](https://fleet-flow.atlassian.net/browse/SCRUM-3).
Dokument zawiera potwierdzenie Review oraz przygotowany wcześniej scenariusz
pokazu. Protokół spotkania i techniczny odbiór Story mają osobne dowody.

## Przegląd — 06.11.2026

Jakub Czaja (PO) potwierdził 06.11, że przegląd odbył się tego dnia,
uczestniczył cały zespół i przejrzano pokazane funkcje Fleet-Flow.
Uczestnicy: Jakub Czaja, Dawid Hnat, Jakub Nazarewicz i Marcel Głowacki.
Ogólny feedback przekazany przez PO: pokazane funkcje oceniono pozytywnie.
Nie przekazano szczegółowych uwag ani listy wyników poszczególnych scenariuszy.

Funkcje przyrostu wiążemy z historyjkami Sprintu 1: logowanie i ograniczenie
dostępu (SCRUM-16), lista i mapa floty (SCRUM-5), synchronizacja i aktualność
danych (SCRUM-15). Nie jest to osobne potwierdzenie testu żywego WEBFLEET,
dostawy SMTP ani pełnego Definition of Done dla każdej z tych historyjek.

PO nie podał SHA pokazywanej wersji. Osobne sprawdzenie wdrożenia 06.11
wykazało `cec4555` zgodne z `origin/main` i gotowość API `ok`; nie przypisujemy
automatycznie tego SHA do wcześniejszego pokazu. Pełne wyniki QA i wymagane
przeglądy implementacji pozostają w zgłoszeniach odpowiednich Story.

## Kontekst scenariusza przygotowanego 4.11.2026

Odczyt Jiry 4.11: aktywny **FF Sprint 1 - flota i mapa**, 24.10–7.11,
trzy Story produktu: SCRUM-16, SCRUM-15 i SCRUM-5. Żadna nie miała wtedy Done.
Statusy w poniższej tabeli opisują ten odczyt, nie aktualny stan oddania.

Cel: zalogowany kierownik floty widzi na wspólnym VPS listę i mapę pojazdów
z synchronizacją WEBFLEET oraz jawną aktualnością danych.

## Przed pokazem

1. Poczekać na udane wdrożenie ostatniego `main`; wykonać dokładne porównanie
   SHA z [instrukcji oddania](SPRINT_REVIEW_SUBMISSION.md).
2. Otworzyć [aplikację HTTPS](https://fleet-flow.pl/).
   Health `200` potwierdza usługę i bazę, nie spełnienie kryteriów Story.
3. Marcel zapisuje odbiór kryteriów w Jirze wraz z SHA i dowodami. Każda
   prezentowana jako ukończona Story musi spełniać całe
   [Definition of Done](../DEFINITION_OF_DONE.md).
4. Uzgodnić konto i dane do demonstracji. Nie pokazywać haseł, tokenów ani
   danych klienta na publicznych zrzutach. Nie zmieniać hasła wspólnego konta
   QA podczas pokazu. Brak danych źródła pozostaje jawną blokadą.

## Pokaz: potrzeba → czynność → korzyść

| Story | Co pokazujemy użytkownikowi | Dowód odbioru / obecna luka |
| --- | --- | --- |
| [SCRUM-16](https://fleet-flow.atlassian.net/browse/SCRUM-16): logowanie i ograniczenie dostępu | Bez sesji widać logowanie. Użytkownik loguje się, otwiera swój widok, wylogowuje; ponowny dostęp wymaga sesji. Błędne dane dają neutralny komunikat. Korzyść: dane floty są dostępne tylko uprawnionym. | Obecnie Testowanie. Potrzebny zapis pełnego odbioru SCRUM-56 i pozostałych kryteriów, nie sam udany login. |
| [SCRUM-5](https://fleet-flow.atlassian.net/browse/SCRUM-5): lista i mapa | Kierownik znajduje pojazd po nazwie/rejestracji, stosuje filtr, przechodzi na mapę z zachowanym wyborem i otwiera szczegóły. Korzyść: szybkie odnalezienie pojazdu i jego położenia. | Obecnie W toku. Potrzebne dane, brakujący zakres SCRUM-51 i odbiór SCRUM-23. Nie podstawiać syntetycznej floty do produktu. |
| [SCRUM-15](https://fleet-flow.atlassian.net/browse/SCRUM-15): synchronizacja i aktualność | Widać czas pomiaru oraz czas ostatniej udanej synchronizacji. Przy awarii istniejące dane pozostają oznaczone jako nieaktualne; zimny cache daje jawny komunikat. Korzyść: użytkownik zna wiarygodność danych. | Obecnie W trakcie weryfikacji. SCRUM-64 uruchamia źródło na VPS; SCRUM-22/23 obejmują odświeżanie i odbiór. Test awarii wykonujemy w izolacji, bez wyłączania żywego źródła podczas pokazu. |

Nie prezentujemy kodu, liczby plików czy zielonych testów jako wartości
zastępującej zachowanie użytkownika. Nieukończony fragment można omówić
jako postęp lub blokadę, ale nie nazywać ukończoną Story.

## Dowody odbioru po spotkaniu

Data, uczestnicy i ogólny feedback są potwierdzeni powyżej. Do pełnego odbioru
pozostaje powiązanie wybranej Story z jej raportem QA, wymaganym niezależnym
review, testowanym SHA i pozostałymi warunkami DoD. Nie dopisujemy szczegółowych
wyników ani decyzji o priorytetach, których uczestnicy nie przekazali.

Po Review zespół uzupełnia [retrospektywę](retro/sprint-1.md) o rzeczywiste
ustalenia i porządkuje niedokończone prace. Podział pracy i decyzje na Planning
są zapisane w części „Działania z właścicielami”.

W Jirze jest aktywny **FF Sprint 2 - historia i auta** (4–18.11.2026).
Jego cel obejmuje historię tras, podstawową ewidencję, ręczną kartotekę
kierowców i pełne dane pojazdu. Działanie z retrospektywy należy do sprintu.
[SCRUM-65](https://fleet-flow.atlassian.net/browse/SCRUM-65)

Zakończenie Sprintu 1 w Jirze jest zablokowane przez otwarte podzadania
SCRUM-1 i SCRUM-66. Oba sprinty są aktywne.
[Backlog Jira](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog)
