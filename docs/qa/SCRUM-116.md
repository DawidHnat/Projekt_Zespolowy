# SCRUM-116 — odbiór i obsługa alarmów Fleet-Flow

[Karta odbioru](https://fleet-flow.atlassian.net/browse/SCRUM-116) · [Zakres metryk](https://fleet-flow.atlassian.net/browse/SCRUM-114)

## Próba w izolacji

Użyj syntetycznej instancji i odbiornika testowego zapisującego wiadomości lokalnie. Zapisz SHA aplikacji, konfigurację monitora, środowisko, UTC i parametry próby. Ustal techniczne wartości na potrzeby przyspieszonej próby oraz tolerancję harmonogramu odczytu.

| Próba | Bodziec | Oczekiwany ślad |
| --- | --- | --- |
| Wykrycie | Wstrzymaj dopływ świeżych danych synchronizacji przy dostępnym monitorze. | Jedno otwarcie po przekroczeniu ustalonego dla próby czasu. |
| Doręczenie | Sprawdź zapis odbiornika po wykryciu. | Jeden komunikat, spójny identyfikator incydentu, czas i stan. Bez GPS, danych kont i sekretów. |
| Deduplikacja | Utrzymaj usterkę przez kolejne cykle, w tym dwukrotnie podaj ten sam stan. | Ten sam incydent pozostaje otwarty bez kolejnych otwarć i duplikatów powiadomienia w oknie deduplikacji. |
| Recovery | Przywróć świeży odczyt i odczekaj wymagane zdrowe cykle. | Jedno zamknięcie z identyfikatorem otwartego incydentu. Następna niezależna awaria otwiera nowy incydent. |
| Brak danych monitora | Na działającej aplikacji odetnij syntetyczne źródło telemetryczne monitora. | Osobny incydent braku telemetrii. Powrót próbek zamyka go po odzyskaniu sygnału. |

## Postępowanie operatora

1. Sprawdź czas ostatniego odczytu i zakres alarmu. Porównaj gotowość API, stan bazy i workera oraz świeżość synchronizacji.
2. Zapisz czas wykrycia, identyfikator i dotknięty komponent. Jeżeli zniknęły wszystkie próbki, sprawdź najpierw trasę zbierania metryk.
3. Po przywróceniu działania potwierdź odczyt świeżej próbki i zamknięcie tego samego incydentu. Przy dalszym problemie przekaż operatorowi zanonimizowany ślad i link do zadania.
4. W protokole zapisz czas bodźca, wykrycia, odbioru i zamknięcia, rzeczywistą liczbę wiadomości oraz PASS/FAIL/BLOCKED dla każdego wiersza.

Aktywacja czeka na zatwierdzenie narzędzia, kanału, odbiorców, kosztu i progów przez operatora i PO. Próbę rzeczywistego kanału wykonuje się po odrębnej decyzji. Połączenie testowe z SMTP potwierdza gotowość połączenia. Dowodem doręczenia jest zapis wiadomości u odbiorcy.
