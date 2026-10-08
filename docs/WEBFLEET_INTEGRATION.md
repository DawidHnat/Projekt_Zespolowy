# WEBFLEET.connect — wynik wstępnego sprawdzenia SCRUM-14

## Potwierdzony zakres

8 października 2026 zweryfikowano autoryzację na lokalnych danych `.env` oraz
odczyt `showObjectReportExtern`. Odpowiedź zawiera obiekty i wymagane pola
snapshotu floty. Nie publikujemy odpowiedzi, identyfikatorów, liczebności floty
ani lokalizacji klientów. Dostęp do historii, tras i raportów pozostaje do
sprawdzenia; cały spike nie jest jeszcze ukończony.

Źródło: [oficjalny przewodnik WEBFLEET.connect 1.74.0](https://media.webfleet.com/fl_attachment/media/doc/documentations/webfleet.connect-doc-1.74.0.pdf),
sekcje „Making HTTP requests”, „General parameters” i „Objects”.

## Transport i dostęp

- Endpoint: `https://csv.webfleet.com/extern`, format JSON, UTF-8, ISO 8601.
- HTTP Basic Auth: login i hasło użytkownika w nagłówku `Authorization`.
- `account` i `apikey` są osobnymi parametrami. Starsza metoda podawania loginu
  i hasła w URL została wycofana; nie używać starych przykładów integracji.
- Adapter dopuszcza tylko odczyt listy obiektów. Żadnych poleceń do pojazdów,
  zmian kierowców, zleceń, zapisów ani kolejek `pop`.
- `columnfilter` ogranicza odpowiedź; adapter dodatkowo odrzuca pola spoza listy.
  Nie pobieramy nazwisk ani telefonów kierowców.
- Sekrety wyłącznie na backendzie. Żadne `VITE_WEBFLEET_*`, logowanie danych
  klienta ani pełnych URL żądań.

## Snapshot obiektu: jednostki i braki

| Pole dostawcy | Model wewnętrzny / decyzja |
| --- | --- |
| `objectuid` | Niezmienny identyfikator; wymagany. Klucz synchronizacji powinien uwzględniać także konto źródła. |
| `objectno` | Numer obiektu, może się zmieniać; nie używać jako zastępstwa UID. |
| `latitude_mdeg`, `longitude_mdeg` | Mikrostopnie WGS84, podzielić przez 1 000 000. Zakres ±90 / ±180. Zero jest poprawną wartością. |
| `odometer` | Dla tej operacji jednostka to 100 metrów: podzielić przez 10, otrzymując km. Nie przenosić tej reguły automatycznie na inne operacje. |
| `ignition` | `0` = zapłon wyłączony, `1` = włączony; brak lub inne wartości = nieznany. |
| `standstill` | `0` = ruch, `1` = postój. Brak informacji nie oznacza postoju. |
| `status` | Jakość GPS: A = aktualny fix, V = możliwa niedokładność, L = ostatni dobry fix, 0 = brak. To nie status jazdy. |
| `pos_time` | Czas ostatniej pozycji; przy `useISO8601=true` normalizujemy do UTC. Bez strefy czasu wartość pozostaje nieznana. |
| `msgtime` | Czas ostatniej wiadomości; nie zastępuje automatycznie czasu pozycji. |
| `speed` | Nie zawsze obecne. Diagnostyka liczy pokrycie; parser jednostek i kontrakt prędkości wymagają osobnego potwierdzenia w SCRUM-36. |

`showObjectReportExtern` zwraca obiekty różnych typów, nie tylko pojazdy. Dlatego
diagnostyka mówi o obiektach. Zanim API listy nazwie je pojazdami, należy połączyć
je po `objectuid` z `showVehicleReportExtern` i sprawdzić dostęp do tej operacji.
`ObjectSnapshot` to model adaptera, nie gotowy kontrakt REST.

Brakujące wartości są `None`, a nie fikcyjnymi zerami. Mapa musi sprawdzić obie
współrzędne, jakość i wiek pozycji. Niedostępny lub stary pomiar nie może sugerować
aktualnej pozycji. Interfejs powinien wyświetlać czas ostatniego pomiaru.

## Kolejne sprawdzenia i zadania

| Obszar | Dokumentacja / stan | Następny krok |
| --- | --- | --- |
| Dane pojazdu i rejestracja | `showVehicleReportExtern`; niesprawdzone na koncie | SCRUM-14: weryfikacja uprawnień i dostępnych pól |
| Przejazdy | `showTripReportExtern`, limit 1 żądanie/min, zalecenie replikacji nie częściej niż co 15 min | SCRUM-14: krótki zakres czasu; sprawdzić `tripid`, jednostki i kompletność |
| Postoje | `showStandStills`, limit 6 żądań/min | SCRUM-14: potwierdzić pola i uprawnienia |
| Geometria tras | `showTracks`; dostęp i ograniczenia pozostają niezweryfikowane | SCRUM-14: wybrany obiekt i mały zakres czasu; wynik bez danych klientów w Git |
| Synchronizacja | Snapshot ma limit 6 żądań/min | SCRUM-15: wspólny limiter, idempotentny upsert, czas i jakość pomiaru, błędy źródła |
| Model i API | Nie utożsamiać obiektu z pojazdem | SCRUM-36: uzgodnienie kontraktu, jednostek i braków; potem SCRUM-19 |
| Backend aplikacji | Adapter nie uruchamia serwera FastAPI ani bazy | SCRUM-39: lokalny serwer, PostgreSQL, migracje, health i CI |
| Dostęp użytkowników | Obecny frontend działa bez logowania i bez prawdziwych danych | SCRUM-16 przed udostępnieniem danych klientów w aplikacji |

Warunki ukończenia SCRUM-14 wymagają jeszcze sprawdzenia historii, postojów i
geometrii oraz uzgodnienia ograniczeń z PO i niezależnego review. Fikcyjne dane
w testach służą weryfikacji adaptera; nie dodajemy demonstracyjnych pojazdów do UI.

## Poczta

Skrzynka `kontakt@fleet-flow.pl` ma status aktywny w OVH. Konfiguracja SMTP jest
gotowa do sprawdzenia lokalnym poleceniem; odmowa logowania wymaga poprawienia
hasła skrzynki lub zakończenia pierwszego logowania. Nie jest to wdrożony reset
haseł. Instrukcja diagnostyki znajduje się w [backend/README.md](../backend/README.md).

Parametry SMTP: [oficjalna dokumentacja OVH Zimbra](https://docs.ovhcloud.com/pl/guides/web-cloud/email-and-collaborative-solutions/zimbra/mail-apps).
