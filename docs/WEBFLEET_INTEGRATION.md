# WEBFLEET.connect — wynik wstępnego sprawdzenia SCRUM-14

## Potwierdzony zakres

8 października 2026 zweryfikowano autoryzację na lokalnych danych `.env` oraz
odczyt `showObjectReportExtern` oraz `showVehicleReportExtern`. Identyfikatory
obu raportów pasują do siebie. Dla jednego pojazdu i dzisiejszego okresu
potwierdzono niepuste odpowiedzi `showTripReportExtern`, `showStandStills`
i `showTracks`. Nie publikujemy odpowiedzi, identyfikatorów, liczebności floty
ani lokalizacji klientów. Jednostka numerycznej prędkości snapshotu nie została
potwierdzona dokładnie tym samym pomiarem historii; nie należy jej zgadywać.

Źródło: [oficjalny przewodnik WEBFLEET.connect 1.74.0](https://media.webfleet.com/fl_attachment/media/doc/documentations/webfleet.connect-doc-1.74.0.pdf),
sekcje „Making HTTP requests”, „General parameters” i „Objects”.

## Transport i dostęp

- Endpoint: `https://csv.webfleet.com/extern`, format JSON, UTF-8, ISO 8601.
- HTTP Basic Auth: login i hasło użytkownika w nagłówku `Authorization`.
- `account` i `apikey` są osobnymi parametrami. Starsza metoda podawania loginu
  i hasła w URL została wycofana; nie używać starych przykładów integracji.
- Adapter dopuszcza tylko wskazane raporty do odczytu. Żadnych poleceń do pojazdów,
  zmian kierowców, zleceń, zapisów ani kolejek `pop`.
- `columnfilter` ogranicza odpowiedź; adapter dodatkowo odrzuca pola spoza listy.
  Nie pobieramy nazwisk ani telefonów kierowców.
- **Kierowców wprowadzamy ręcznie w Fleet-Flow**, zgodnie z decyzją PO.
  Nie wywołujemy raportów kierowców. Przypisania kierowców i historię tych
  przypisań zapisujemy jako dane aplikacji; synchronizacja ich nie nadpisuje.
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
| `speed` | Wg WEBFLEET 1.74.0: prędkość w km/h (wartość całkowita, obecna tylko przy ruchu `standstill=0`). Zgodnie z decyzją PO aplikacja waliduje i zwraca `speed_kmh` w km/h, a przy postoju, braku lub niepewności pomiaru jawne `null`. |

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
| Dane pojazdu i rejestracja | `showVehicleReportExtern`; dostęp oraz UID potwierdzone | Rejestracja może być pusta; nie zastępować jej wymyśloną wartością |
| Przejazdy | `showTripReportExtern`, limit 1 żądanie/min, zalecenie replikacji nie częściej niż co 15 min; dostęp potwierdzony | Dystans w metrach, czas w sekundach; osobna synchronizacja historii |
| Postoje | `showStandStills`, limit 6 żądań/min; dostęp potwierdzony | Czas w sekundach, współrzędne w mikrostopniach |
| Geometria tras | `showTracks`, limit 10 żądań/min; zakres maksymalnie 2 dni; dostęp potwierdzony | Prędkość tej operacji jest w km/h; nie utożsamiać rekordów o różnych czasach |
| Synchronizacja | Snapshot ma limit 6 żądań/min | SCRUM-15: wspólny limiter, idempotentny upsert, czas i jakość pomiaru, błędy źródła |
| Model i API | Nie utożsamiać obiektu z pojazdem | SCRUM-36: uzgodnienie kontraktu, jednostek i braków; potem SCRUM-19 |
| Backend aplikacji | Adapter nie uruchamia serwera FastAPI ani bazy | SCRUM-39: lokalny serwer, PostgreSQL, migracje, health i CI |
| Dostęp użytkowników | Obecny frontend działa bez logowania i bez prawdziwych danych | SCRUM-16 przed udostępnieniem danych klientów w aplikacji |

## Wnioski, decyzje PO i zakończenie Spike'a SCRUM-14

Rozpoznanie techniczne WEBFLEET.connect i diagnostyki SMTP w ramach SCRUM-14
zostało ukończone i potwierdza pełną wykonalność integracji.

Podsumowanie warunków ukończenia:
1. **Autoryzacja i transport:** Zweryfikowano działanie HTTPS, formatu JSON, nagłówka
   HTTP Basic Auth i `apikey` oraz odrzucanie żądań modyfikujących pojazdy.
   Adapter i diagnostyka zostały wdrożone w PR #7.
2. **Jednostka prędkości:** Zgodnie z dokumentacją WEBFLEET 1.74.0 prędkość jest liczbą
   całkowitą w km/h przy ruchu (`standstill=0`). Zgodnie z decyzją PO API waliduje i
   zwraca `speed_kmh` w km/h, a przy postoju, braku lub niepewności pomiaru jawne `null`.
3. **Niedostępne metadane pojazdów (marka, model, rok, VIN, adres):** WEBFLEET nie
   zwraca tych pól w standardowym raporcie. Zgodnie z decyzją PO pola te stanowią
   ręczną kartotekę pojazdu w Fleet-Flow (SCRUM-51 / SCRUM-25).
4. **Kierowcy (RODO):** Potwierdzono ostatecznie, że kierowcy nie są pobierani z API;
   pozostają wyłącznie ręcznymi wpisami w aplikacji (SCRUM-42).
5. **Historia, postoje i geometria (SCRUM-24):** Potwierdzono operacje `showTripReportExtern`
   (metry/sekundy, limit 1/min), `showStandStills` (sekundy/mikrostopnie, limit 6/min) oraz
   `showTracks` (km/h, mikrostopnie, max 2 dni, limit 10/min).
6. **Limity i koordynacja (SCRUM-22 / SCRUM-15):** Potwierdzono limit 6 żądań/min dla
   snapshotu oraz minimum 10 s odstępu między akcjami. Obsłużono nagłówek `Retry-After: 60`
   i współdzielenie stanu za pomocą PostgreSQL advisory locks (`pg_try_advisory_lock`).
7. **Dane syntetyczne:** W testach (`test_sync.py`, `test_fleet_api.py`) oraz kontrakcie
   `contracts/api-design.json` przygotowano zestaw danych syntetycznych bez sekretów i
   prawdziwych pozycji GPS.

Spike SCRUM-14 spełnia wszystkie kryteria akceptacji i zostaje przekazany do formalnego
odbioru i przeglądu.

## Poczta

Skrzynka `kontakt@fleet-flow.pl` ma status aktywny w OVH. Konfiguracja SMTP jest
gotowa do sprawdzenia lokalnym poleceniem; odmowa logowania wymaga poprawienia
hasła skrzynki lub zakończenia pierwszego logowania. Nie jest to wdrożony reset
haseł. Instrukcja diagnostyki znajduje się w [backend/README.md](../backend/README.md).

Parametry SMTP: [oficjalna dokumentacja OVH Zimbra](https://docs.ovhcloud.com/pl/guides/web-cloud/email-and-collaborative-solutions/zimbra/mail-apps).
