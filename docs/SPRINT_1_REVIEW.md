# Review Sprintu 1 — pokaz na podstawie historyjek

Jira: [SCRUM-3](https://fleet-flow.atlassian.net/browse/SCRUM-3).
To plan demonstracji i karta odbioru; nie potwierdza, że Review już się odbyło.
Odczyt Jiry 26.10.2026: aktywny **FF Sprint 1 - flota i mapa**, 24.10–7.11,
trzy Story produktu: SCRUM-16, SCRUM-15 i SCRUM-5. Żadna nie ma jeszcze Done.

Cel: zalogowany kierownik floty widzi na wspólnym VPS listę i mapę pojazdów
z synchronizacją WEBFLEET oraz jawną aktualnością danych.

## Przed pokazem

1. Poczekać na udane wdrożenie ostatniego `main`; wykonać dokładne porównanie
   SHA z [instrukcji oddania](SPRINT_REVIEW_SUBMISSION.md).
2. Otworzyć [aplikację HTTPS](https://vps-9171bf52.vps.ovh.net/).
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

## Zapis po rzeczywistym spotkaniu

PO dopisuje do SCRUM-3: datę, uczestników, pokazane Story i ich SHA, powiązany
raport QA, feedback oraz decyzje o priorytetach. Obecnie brak potwierdzonego
terminu i feedbacku — nie zostały wpisane jako wykonane.

Po Review zespół uzupełnia [retrospektywę](retro/sprint-1.md), porządkuje
nieukończone Story bez częściowych punktów i planuje Sprint 2. Aktualna propozycja:

- **Nazwa:** FF Sprint 2 - historia.
- **Cel:** historia pojazdu, trwały cel/opis i suma okresu oraz ręczna kartoteka
  kierowców; SCRUM-6, SCRUM-62, SCRUM-42 i przekrojowy odbiór SCRUM-63.
- **Usprawnienie:** SCRUM-65 — codzienne review i kompletne odbiory DoD.
- **Stan:** planowany. Daty, pojemność, przeniesienie niedokończonych prac
  i uruchomienie wymagają rzeczywistego Planningu. Nie uruchamiamy równoległego
  sprintu tylko po to, by uzyskać zrzut.
