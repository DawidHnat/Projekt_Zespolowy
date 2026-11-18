# WEBFLEET.connect — ustalenia SCRUM-14

## Potwierdzony zakres

8 października 2026 zweryfikowano autoryzację na lokalnych danych `.env` oraz
odczyt `showObjectReportExtern` oraz `showVehicleReportExtern`. Identyfikatory
obu raportów pasują do siebie. Dla jednego pojazdu i dzisiejszego okresu
potwierdzono niepuste odpowiedzi `showTripReportExtern`, `showStandStills`
i `showTracks`. Nie publikujemy odpowiedzi, identyfikatorów, liczebności floty
ani lokalizacji klientów. 18.11.2026, na wyraźne polecenie PO, wykonano także
[kontrolne porównanie jednostki snapshotu](qa/SCRUM-14-speed-unit.md).
Jeden niezerowy pomiar o zgodnych czasach GPS i wiadomości, jakości `A`,
tym samym UID i czasie w `showTracks` potwierdził km/h bez przeliczania.
Zakres i ograniczenia tej empirycznej weryfikacji opisuje powiązany dokument.

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
| `speed` | km/h bez przelicznika, potwierdzone kontrolnym porównaniem 18.11.2026. Adapter przyjmuje liczbę lub tekst liczbowy 0–300; brak/niepoprawna wartość to `None`. API zwraca ją wyłącznie dla świeżego, poprawnego pomiaru GPS i działającego źródła; w pozostałych przypadkach `speed_kmh: null`. |

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

## Wnioski, decyzje PO i status Spike'a SCRUM-14

Rozpoznanie techniczne WEBFLEET.connect i diagnostyki SMTP w ramach SCRUM-14
potwierdza techniczną wykonalność integracji. Decyzje projektowe, granice RODO i mapowanie pól
zostały uzgodnione. Empiryczne potwierdzenie jednostki prędkości snapshotu
uzupełniono 18.11.2026; wynik autora nadal wymaga niezależnego review i odbioru QA.

Podsumowanie warunków ukończenia:
1. **Autoryzacja i transport:** Zweryfikowano działanie HTTPS, formatu JSON, nagłówka
   HTTP Basic Auth i `apikey` oraz odrzucanie żądań modyfikujących pojazdy.
   Adapter i diagnostyka zostały wdrożone w PR #7.
2. **Jednostka prędkości:** W oficjalnym przewodniku 1.74.0 pole `speed` w wyniku
   `showObjectReportExtern` jest opisane jako string bez wskazania jednostki (w przeciwieństwie
   do operacji `showTracks`, gdzie km/h jest podane wprost). Kontrolne porównanie
   tego samego zdarzenia na używanym koncie 18.11.2026 potwierdziło km/h bez
   przeliczenia. Nowa decyzja PO uruchamia przekazywanie potwierdzonej prędkości
   do API w SCRUM-22; braki i nieaktualne/niepotwierdzone odczyty pozostają `null`.
3. **Adres pozycji a ręczna kartoteka pojazdu:**
   - **Adres pozycji:** Oficjalna tabela wyniku `showObjectReportExtern` udostępnia pola
     `postext` oraz `postext_short` zawierające geokodowany adres ostatniej pozycji. Pole to jest
     związane z bieżącym pomiarem (`Measurement.position_address` w SCRUM-51); w przypadku braku
     tekstu adresu (np. poza obszarem geokodowania lub przy braku pozycji) API zwraca jawne `null`.
    - **Możliwości raportów dostawcy:** oficjalna tabela `showVehicleReportExtern`
      (przewodnik 1.74.0) opisuje `identnumber` jako VIN przy odpowiednim urządzeniu
      ([strona 95 PDF](https://media.webfleet.com/fl_attachment/media/doc/documentations/webfleet.connect-doc-1.74.0.pdf#page=95))
      oraz opcjonalne `manufacturedyear`
      ([strona 97 PDF](https://media.webfleet.com/fl_attachment/media/doc/documentations/webfleet.connect-doc-1.74.0.pdf#page=97)).
      Marka i model nie zostały potwierdzone jako pola tego raportu. Dostępność pól po stronie
      dostawcy nie była weryfikowana na żywym koncie.
    - **Aktualny zakres Fleet-Flow:** adapter pobiera `showVehicleReportExtern`, ale
      `VEHICLE_COLUMNS` nie obejmuje `identnumber` ani `manufacturedyear`, więc VIN i rok nie są
      obecnie importowane. Niepobieranie pola przez
      nasz kod nie oznacza, że dostawca go nie udostępnia. Zgodnie z decyzją PO pola `make`,
      `model`, `year`, `vin` są ręczną kartoteką pojazdu w Fleet-Flow (`Vehicle` w SCRUM-51 /
      UI w SCRUM-25), zarządzaną lokalnie, a ręczne zmiany mają pierwszeństwo i nie są
      nadpisywane przez synchronizację. Import VIN/roku jest poza zakresem tego PR.
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

Wnioski ze Spike'a SCRUM-14 stanowią podstawę implementacji zadań SCRUM-15, SCRUM-24
oraz SCRUM-51. Uzupełnione potwierdzenie jednostki `speed` oraz implementacja
jej przekazywania w SCRUM-22 zostają przekazane do review i QA. Nie jest to
deklaracja zamknięcia całego spike'a ani potwierdzenie wdrożenia.

## Poczta

Skrzynka `kontakt@fleet-flow.pl` ma status aktywny w OVH. Konfiguracja SMTP jest
gotowa do sprawdzenia lokalnym poleceniem; odmowa logowania wymaga poprawienia
hasła skrzynki lub zakończenia pierwszego logowania. Nie jest to wdrożony reset
haseł. Instrukcja diagnostyki znajduje się w [backend/README.md](../backend/README.md).

Parametry SMTP: [oficjalna dokumentacja OVH Zimbra](https://docs.ovhcloud.com/pl/guides/web-cloud/email-and-collaborative-solutions/zimbra/mail-apps).
