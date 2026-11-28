# SCRUM-17 — scenariusz demonstracji i regresji MVP

[Karta odbioru](https://fleet-flow.atlassian.net/browse/SCRUM-17)

Przed sesją zapisz datę, wykonawcę, SHA wdrożenia, URL środowiska testowego i link do zielonego CI tego SHA. Przygotuj dwa konta o różnych uprawnieniach i dwa syntetyczne pojazdy. Jeden ma świeżą pozycję i przejazd 12,345 km bez celu, drugi starszą pozycję i okres z niepełnym pokryciem. Ustal próg alertu i przygotuj dystanse po obu jego stronach.

| Próba | Kroki | Oczekiwany wynik | Środowisko i SHA próby |
| --- | --- | --- | --- |
| Logowanie i mapa | Otwórz prywatny widok przed logowaniem, zaloguj się jako editor, wybierz pojazd na liście i mapie. | Przed logowaniem widok prywatny jest niedostępny. Lista i mapa wskazują ten sam pojazd, czas aktualizacji jest czytelny. | Syntetyczne QA z aktywną Historią i Ewidencją; URL i pełny SHA do potwierdzenia przed próbą |
| Historia i ewidencja | Wybierz okres, otwórz przejazd, zapisz cel i opis, odśwież widok. | Adnotacja pozostaje zapisana, suma 12,345 km nie zmienia się, braki celu spadają z 1 do 0. | Syntetyczne QA z aktywną Historią i Ewidencją; URL i pełny SHA do potwierdzenia przed próbą |
| Analityka i alert | Porównaj dwa pojazdy i sprawdź dystanse po obu stronach zapisanego progu. | Jednostki, zakres okresu i brak pokrycia są widoczne. Alert odpowiada regule i aktualizuje się po przeliczeniu. | Syntetyczne QA z aktywną Historią i Ewidencją; URL i pełny SHA do potwierdzenia przed próbą |
| Brak danych i awaria źródła | Wybierz pusty okres. Na odrębnej próbie zatrzymaj syntetyczne źródło. | Całkowicie pusty okres pokazuje pustą listę po udanym odczycie. Przy niepełnych danych w zapisanych wierszach sprawdź oznaczenie „Brak danych” i licznik „Brak dystansu”. Awaria odczytu pokazuje „Nie można pobrać ewidencji.” i „Ponów odczyt”. Ostatnia pozycja jest oznaczona jako nieaktualna, jeśli nadal jest pokazywana. | Syntetyczne QA z aktywną Historią i Ewidencją; URL i pełny SHA do potwierdzenia przed próbą |
| Uprawnienia | Spróbuj edycji jako viewer, następnie wyloguj się i wróć do chronionego widoku. | Zapis zostaje odrzucony, a po wylogowaniu prywatne dane są niedostępne. | Syntetyczne QA z aktywną Historią i Ewidencją; URL i pełny SHA do potwierdzenia przed próbą |

Dla każdej próby zapisz rzeczywisty wynik, PASS/FAIL/BLOCKED i dowód. Powiąż błędy blokujące z Jira i ponów próbę po poprawce. Oznacz sesję jako demonstracyjną. Brak potwierdzonego SHA albo wdrożonej zależności oznacza **BLOCKED** dla danej próby. Wpisz brakującą zależność. Osobno zapisz stan odbioru prawdziwej integracji. Wyniki modułowe można uzupełnić z [planu QA](TEST_PLAN.md), ze wskazaniem SHA każdego dowodu.

**Decyzja PO (akceptacja, warunki lub odmowa; data i osoba):** do uzupełnienia po demonstracji.
