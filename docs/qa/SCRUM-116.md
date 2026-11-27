# SCRUM-116 — odbiór i obsługa alarmów Fleet-Flow

[Karta odbioru](https://fleet-flow.atlassian.net/browse/SCRUM-116) · [Zakres metryk](https://fleet-flow.atlassian.net/browse/SCRUM-114)

## Próba w izolacji

Użyj syntetycznej instancji i odbiornika testowego zapisującego wiadomości lokalnie. Zapisz SHA aplikacji, konfigurację monitora, środowisko, UTC i parametry próby. Ustal techniczne wartości na potrzeby przyspieszonej próby oraz tolerancję harmonogramu odczytu.

Źródło metryk po [#174](https://github.com/DawidHnat/Projekt_Zespolowy/pull/174) to wewnętrzny endpoint syntetycznej instancji `GET /api/v1/observability/metrics?format=prometheus`. Referencja implementacji: `45d05756a576b572c09c6e3cea2600c88aa1c9d5`. Przed próbą zapisz wdrożony SHA, wersję lub digest obrazu monitora, rewizję konfiguracji i nazwę targetu. Wersja monitora czeka na wybór operatora. Do czasu przypięcia wersji i weryfikacji targetu próba ma wynik **BLOCKED**.

| Próba | Bodziec | Oczekiwany ślad |
| --- | --- | --- |
| Wykrycie | Wstrzymaj dopływ świeżych danych synchronizacji przy dostępnym monitorze. | Jedno otwarcie po przekroczeniu ustalonego dla próby czasu. |
| Doręczenie | Sprawdź zapis odbiornika po wykryciu. | Jeden komunikat, spójny identyfikator incydentu, czas i stan. Bez GPS, danych kont i sekretów. |
| Deduplikacja | Utrzymaj usterkę przez kolejne cykle, w tym dwukrotnie podaj ten sam stan. | Ten sam incydent pozostaje otwarty bez kolejnych otwarć i duplikatów powiadomienia w oknie deduplikacji. |
| Recovery | Przywróć świeży odczyt i odczekaj wymagane zdrowe cykle. | Jedno zamknięcie z identyfikatorem otwartego incydentu. Następna niezależna awaria otwiera nowy incydent. |
| Brak danych monitora | Na izolowanej instancji przerwij wyłącznie trasę od monitora do endpointu metryk, np. zwracając 503 w testowym proxy kolektora. Niezależnie potwierdź HTTP 200 z readiness i działanie aplikacji. Przywróć trasę, a następnie potwierdź świeży scrape. | W historii incydentów monitora potwierdź jedno otwarcie i jedno zamknięcie z tym samym identyfikatorem. Porównaj czasy z logiem scrape i zapisem lokalnego odbiornika. Oczekiwany jest osobny incydent braku telemetrii. |

## Postępowanie operatora

1. Sprawdź czas ostatniego odczytu i zakres alarmu. Porównaj gotowość API, stan bazy i workera oraz świeżość synchronizacji.
2. Zapisz czas wykrycia, identyfikator i dotknięty komponent. Jeżeli zniknęły wszystkie próbki, sprawdź najpierw trasę zbierania metryk.
3. Po przywróceniu działania potwierdź odczyt świeżej próbki i zamknięcie tego samego incydentu. Przy dalszym problemie przekaż operatorowi zanonimizowany ślad i link do zadania.
4. W protokole zapisz czas bodźca, wykrycia, odbioru i zamknięcia, rzeczywistą liczbę wiadomości oraz PASS/FAIL/BLOCKED dla każdego wiersza.

Aktywacja czeka na zatwierdzenie narzędzia, kanału, odbiorców, kosztu i progów przez operatora i PO. Próbę rzeczywistego kanału wykonuje się po odrębnej decyzji. Połączenie testowe z SMTP potwierdza gotowość połączenia. Dowodem doręczenia jest zapis wiadomości u odbiorcy.
