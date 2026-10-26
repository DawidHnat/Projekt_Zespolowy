# Zasady pracy Scrum — SCRUM-34

Aktualizacja: 26.10.2026. Właściciel: Jakub Czaja. Dokument porządkuje
bieżący przepływ pracy i zastępuje nieaktualny opis SCRUM-34 z 5 października.
Źródłem bieżących statusów i składu sprintów jest
[Jira](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog).

## Cel i odpowiedzialność

Kierownik floty ma otrzymać listę i mapę pojazdów, historię z celami/opisami
oraz analitykę i alerty. Kierowcy są wprowadzani ręcznie; synchronizacja
WEBFLEET nie tworzy ani nie nadpisuje ich kartoteki. Niepełne dane mają jawny
stan braku lub nieaktualności.

| Osoba | Odpowiedzialność |
| --- | --- |
| Jakub Czaja | PO/lider i developer: cel produktu, kolejność backlogu, kryteria, decyzje o zakresie |
| Dawid Hnat | Developer i infrastruktura: backend, adapter, synchronizacja, VPS i wdrożenia |
| Jakub Nazarewicz | Developer: mapa, widoki floty, historia i porównania |
| Marcel Głowacki | QA i developer: plan, scenariusze, niezależny odbiór i regresja |

Repozytorium i kontrakt wymieniają całą czwórkę. Dodatkowa odpowiedzialność
Scrum Mastera nie została potwierdzona; wcześniejsza propozycja dotycząca
Dawida nie jest ustaleniem zespołu. Godziny dostępności, kanały Discord/Messenger
i czas odpowiedzi są w [TEAM_CONTRACT.md](../TEAM_CONTRACT.md).
Nie zmieniamy kontraktu przez samą aktualizację tego dokumentu.

## Sprinty i punkty

Stan odczytany w Jirze 26.10.2026:

| Sprint | Cel i zakres Story | SP | Etap |
| --- | --- | --- | --- |
| 1 — flota i mapa | Logowanie SCRUM-16, synchronizacja SCRUM-15, lista/mapa SCRUM-5; wsparcie szkieletu, VPS i QA | 5 + 8 + 8 = 21 | Aktywny, 24.10–7.11.2026, godz. 18:33 Europe/Warsaw; 9 zgłoszeń głównych |
| 2 — historia | Historia SCRUM-6, cel/opis i suma okresu SCRUM-62, ręczni kierowcy SCRUM-42; przekrojowe QA SCRUM-63 | 8 + 5 + 8 = 21 | Planowany, bez dat; 4 zgłoszenia główne |
| 3 — analityka | Porównania SCRUM-61, alerty SCRUM-7; regresja SCRUM-17 i infrastruktura SCRUM-18 | 5 + 8 = 13 | Planowany, bez dat; 4 zgłoszenia główne |

Daty nie są dowodem przeprowadzenia Planningu, Review ani retrospektywy.
Na Planningu potwierdzamy rzeczywistą dostępność, zakres i wyceny; nie zakładamy
velocity na podstawie samej liczby kart. Osiem głównych Story MVP to
16, 15, 5, 6, 62, 61, 7 i 42. Stare wyceny 13 SP historyjek 6/7 zastąpił
ich podział na mniejsze rezultaty.

SP oznaczają względną złożoność. Punkty podzadań uzupełnione 24–25.10 są
roboczymi szacunkami, nie godzinami ani pozostałym czasem. Nie sumujemy punktów
rodzica i dzieci do wyniku sprintu; Story nie otrzymuje części punktów za
częściowe wykonanie. Gotowe podzadanie zachowuje swój wynik, a niedokończony
zakres Story jest ponownie planowany.

## Przepływ w Jirze

| Status | Kategoria Jira | Kiedy ustawić | Wymagany rezultat |
| --- | --- | --- | --- |
| Do zrobienia | Do zrobienia | Zakres czeka na rozpoczęcie | Właściciel, kryteria i zależności |
| W toku | W toku | Właściciel rozpoczął pracę | Gałąź zadania, następny krok i opisana blokada, jeśli występuje |
| W trakcie weryfikacji | W toku | Rezultat jest gotowy do niezależnego review | PR lub dokument, aktualny commit i sposób sprawdzenia |
| Testowanie | W toku | Przyrost po review można niezależnie sprawdzić | Osoba QA, scenariusze, wersja i środowisko; bez domyślnego PASS |
| Gotowe | Gotowe | Spełniono wszystkie kryteria i DoD | Wynik odbioru, scalony PR i wymagane dowody |

26.10 poprawiono kategorię istniejącego statusu **Testowanie** z Do zrobienia
na W toku. Nazwa, położenie kolumny, punkty i statusy konkretnych zgłoszeń
pozostają zachowane. Po odświeżeniu backlog Sprintu 1 pokazuje 0/21 SP
Do zrobienia, 21/21 W toku i 0/21 Gotowe. Nie oznacza to ukończenia żadnej Story.

W widoku **Grupa → Subtask** dzieci są widoczne we własnych kolumnach z punktami.
Bez grupowania rozwijamy dzieci na karcie rodzica. Rodzic może pozostać W toku,
gdy gotowy fragment ma już odbiór QA — jak SCRUM-5 z otwartym SCRUM-51.
Nie przenosimy całej Story do Gotowe po scaleniu jednego fragmentu.

Developer pracuje według [CONTRIBUTING](../CONTRIBUTING.md): jedna gałąź i PR
na zadanie, review innej osoby oraz wymagane CI. QA zapisuje scenariusz,
oczekiwany i faktyczny rezultat, PASS/FAIL/BLOCKED, datę, środowisko i SHA.
FAIL ma powiązane zgłoszenie z krokami odtworzenia i retestem po poprawce.
Jeżeli projekt nie udostępnia typu Błąd, stosujemy Zadanie z etykietą `bug`.
BLOCKED wskazuje przyczynę, potrzebną pomoc i termin kolejnej aktualizacji.

## Warunki rozpoczęcia i ukończenia

Przed rozpoczęciem właściciel zna użytkownika i cel, kryteria, zakres,
uprawnienia, źródło danych, zależności i sposób odbioru. Brak niezbędnego
interfejsu staje się jawną zależnością, a nie ukrytą atrapą w produkcie.

Obowiązuje [DEFINITION_OF_DONE.md](../DEFINITION_OF_DONE.md). Zawiera sprawdzalne
warunki review, CI, testów, wdrożenia HTTPS i zgodności SHA z `origin/main`.
Wynik CI nie zastępuje niezależnego QA, a dokumentacja konfiguracji nie jest
dowodem jej działania. Nie zastępujemy DoD drugim, skróconym zestawem reguł.
Testy używają danych syntetycznych; żywe WEBFLEET i wysyłka SMTP wymagają
osobnego uzgodnienia. Sekrety i `.env` pozostają poza Git.

## Rytm pracy i zapisy spotkań

Poniższe czasy są wcześniejszą propozycją z SCRUM-34, do potwierdzenia przez
zespół. Nie utworzono wydarzeń ani nie zapisano fikcyjnej obecności.

| Spotkanie | Propozycja | Co zapisać |
| --- | --- | --- |
| Planning | Do 60 min na początku sprintu | Datę, dostępność, cel, zakres, wyceny, zależności i pierwsze kroki |
| Daily | Do 15 min w dniach wspólnej pracy | Postęp do celu, najbliższy plan i blokady |
| Refinement | 30–45 min raz w tygodniu | Doprecyzowane kryteria, zależności i estymaty |
| Review | Do 45 min na koniec sprintu | Wersję na VPS, pokazane kryteria, wyniki QA, feedback i zmiany backlogu |
| Retrospektywa | Do 30 min po Review | Jedno–dwa usprawnienia z właścicielem i datą sprawdzenia |

Terminy i dostępność sprintową ustalamy w SCRUM-1/4 na podstawie kontraktu.
Priorytety konsultujemy w SCRUM-2. Review i retrospektywę zapisujemy w SCRUM-3
po ich przeprowadzeniu. Dostęp prowadzącego pozostaje odroczony decyzją PO
do uzyskania jego danych; nie przedstawiamy go jako potwierdzonego.

## Odbiór SCRUM-34

- Opis zadania i dokument wskazują aktualny zakres sprintów oraz osiem Story MVP.
- Przepływ rozróżnia review i QA, a Testowanie ma kategorię W toku.
- DoD jest podlinkowane jako obowiązujące źródło; wiadomo, co stanowi dowód odbioru.
- Role, komunikacja i dostępność odwołują się do README/kontraktu; propozycje
  spotkań i Scrum Mastera są jawnie oznaczone jako niepotwierdzone.
- Dokument przechodzi niezależny przegląd w PR. Przyjęcie rytmu pracy przez
  zespół oraz potwierdzenie Scrum Mastera pozostają decyzjami ludzi.
