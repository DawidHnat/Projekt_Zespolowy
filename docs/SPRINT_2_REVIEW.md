# Review Sprintu 2 — scenariusz do wykonania

**Spotkanie i pełny odbiór Story jeszcze niepotwierdzone.** PO przekazał ten
stan 10.11.2026. Przygotowanie techniki: [SCRUM-127](https://fleet-flow.atlassian.net/browse/SCRUM-127).
Serwer: [Fleet-Flow](https://fleet-flow.pl/), wersja HTTP: <http://57.129.179.53/>.

## Przygotowanie

Jakub Czaja wybiera z zespołem co najmniej jedną **całą historyjkę Sprintu 2**,
której wszystkie kryteria można odebrać. Sam ukończony task infrastruktury
albo podzadanie nie potwierdza całej historyjki. Wpisuje klucz Story, zakres,
SHA wydania oraz dowody każdego warunku [DoD](../DEFINITION_OF_DONE.md).
Drugi developer zatwierdza aktualny kod, Dawid dopilnowuje wdrożenia,
a Marcel zapisuje niezależny odbiór kryteriów przed pokazem.

Obecny cel `FF Sprint 2 - podstawa i QA` to domknięcie istniejącego kodu
floty/UI, źródłowych pól, kartoteki, backupu i synchronizacji, z priorytetem
review/QA. Dashboard, personalizacja i zbiorowa edycja (SCRUM-38/45/46)
są przygotowanymi tematami pokazu; PR-y #70–72 wymagają jeszcze review,
scalenia we właściwej kolejności, wdrożenia i QA. Nie są gotową Story
wyłącznie dlatego, że ich testy przeszły.

## Pokaz na podstawie potrzeby użytkownika

| Potrzeba | Czynności i korzyść do pokazania | Sprawdza |
| --- | --- | --- |
| Kierownik szybko dostosowuje swój pulpit | Wybrać moduły, motyw, zmienić układ i rozmiar okna; sprawdzić zapamiętanie i mały ekran. Korzyść: potrzebne informacje pod ręką. Powiązać z odebranym zakresem SCRUM-38/40. | Marcel: kryteria i regresja; Jakub: potwierdzenie zakresu |
| Kierownik porządkuje widok pojazdów | Wybrać kafelki, zmienić ich rozmiar wspólnie, sprawdzić paginację i zachowanie po odświeżeniu. Powiązać z SCRUM-45/46. | Marcel: UI desktop/mobile i ograniczenia preferencji lokalnych |
| Zespół bezpiecznie wydaje zmiany | Pokazać wersję na serwerze, wynik testów, osobny lint i smoke z tym samym SHA; czerwony dowód lintu/testu blokuje drogę. To dowód bram jakości, nie zamiennik wartości Story. | Dawid: CI/deployment/ochrona; niezależny reviewer: PR |

Nie dodawać fikcyjnej floty do produktu. Przy braku danych użyć odebranego
pustego stanu i uczciwie zaznaczyć ograniczenie albo uzgodnić osobny bezpieczny
scenariusz demonstracji. Nie uruchamiać źródła WEBFLEET/SMTP na potrzeby pokazu.

## Co zapisać po spotkaniu

PO uzupełnia datę, uczestników, klucz całej odebranej Story, testowane SHA,
link do PR/review, wyniki QA, feedback i decyzje zakresu. Następnie zespół
uzupełnia [retro S2](retro/sprint-2.md) o rzeczywiste ustalenia i stan działań S1.
Dopiero potem rozlicza Sprint 2 i rozpoczyna Sprint 3; pozostałe prace
przenosi jawnie, bez automatycznego oznaczania Done.
