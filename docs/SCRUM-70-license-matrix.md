# SCRUM-70 — macierz zgodności kategorii prawa jazdy z pojazdem

**Wersja reguł w kodzie:** `pl-ustawa-o-kierujacych-v1-pending-po`  
**Status zatwierdzenia biznesowego:** **Oczekuje na potwierdzenie Product Ownera (`po_confirmed = false`)** przed uznaniem reguł za docelową politykę produkcyjną.  
**Podstawa referencyjna:** Ustawa z dnia 5 stycznia 2011 r. o kierujących pojazdami (Dz.U. z 2024 r. poz. 1210, art. 6 — zakres uprawnień kategorii prawa jazdy na terytorium RP).

## 1. Zasady kluczowe (bez zgadywania i bez porządku alfabetycznego)

1. **Trzy jawne stany oceny:**
   - `compatible` (`Zgodne`) — kierowca posiada wpisane kategorie oraz pojazd ma kompletne wymagania (np. DMC w kg lub jawny wyjątek), a posiadane uprawnienia pokrywają wymaganą kategorię.
   - `incompatible` (`Niezgodne`) — zarówno kategorie kierowcy, jak i wymagania pojazdu są znane i potwierdzają brak uprawnień. **Blokuje nowe przypisanie kierowcy do pojazdu oraz wybór kierowcy w ewidencji przejazdów (`409 LICENSE_INCOMPATIBLE`), również przy bezpośrednim wywołaniu API.**
   - `unverified` (`Niezweryfikowane`) — brak wpisanych kategorii kierowcy, brak DMC pojazdu, brak liczby miejsc autobusu lub brak jawnej kategorii dla motocykla/czterokołowca. **Brak danych nigdy nie jest traktowany jako `compatible`.**
2. **Zakaz opierania się wyłącznie na etykiecie `"ciężarowy"` lub porządku alfabetycznym:**
   - W polskich dowodach rejestracyjnych lekkie auta dostawcze homologacji `N1` o `DMC <= 3500 kg` często posiadają wpis `"ciężarowy"`, lecz wymagają kategorii **`B`**, a nie `C`.
   - Dlatego rekord z `vehicle_type = "ciężarowy"` i `gross_weight_kg = null` zwraca jawny stan `unverified` (`missing_vehicle_dmc`), a po wpisaniu `gross_weight_kg = 3500` wymaga kategorii **`B`**.
   - Porównywanie napisów kategorii (np. `"C" > "B+E"` lub `"D" > "C"`) nie jest nigdy stosowane (`D` nie uprawnia do kierowania ciężarówką `C`).

## 2. Wyznaczanie wymaganej kategorii pojazdu (`vehicle_license_requirement`)

| Klasa / parametry pojazdu | Warunek w kartotece `vehicles` | Wymagana kategoria podstawowa | Z przyczepą ciężką (`tows_heavy_trailer = true`) | Gdy brakuje parametru |
| --- | --- | --- | --- | --- |
| Jawny wyjątek na karcie pojazdu | `required_category_override` ustawione (`AM`–`T`) | Wartość `required_category_override` | `+E` dla `B`/`C1`/`C`/`D1`/`D` | — |
| Ciągnik rolniczy / wolnobieżny | `vehicle_type` = `ciągnik` / `ciągnik rolniczy` / `tractor` | `T` | `T` | — |
| Motocykl / motorower / czterokołowiec | `vehicle_type` = `motocykl` / `motorower` / `skuter` / `quad` | Wymaga `required_category_override` (`AM`/`A1`/`A2`/`A`/`B1`) ze względu na zależność od kW i stosunku mocy do masy | — | `unverified` (`missing_vehicle_requirements`) |
| Autobus / przewóz powyżej 8 pasażerów | `vehicle_type = autobus` lub `passenger_seats > 8` | `9..16` miejsc pasażerskich -> `D1`; `> 16` miejsc -> `D` | `D1+E` / `D+E` | `unverified` (`missing_passenger_seats`) |
| Pojazd samochodowy do `3500 kg` DMC (osobowy, van, dostawczy, N1 ciężarowy) | `gross_weight_kg <= 3500` | `B` | `B+E` | `unverified` (`missing_vehicle_dmc`) |
| Pojazd samochodowy `3501–7500 kg` DMC | `3501 <= gross_weight_kg <= 7500` | `C1` | `C1+E` | `unverified` (`missing_vehicle_dmc`) |
| Pojazd samochodowy powyżej `7500 kg` DMC | `gross_weight_kg >= 7501` | `C` | `C+E` | `unverified` (`missing_vehicle_dmc`) |

## 3. Hierarchia zawierania się uprawnień (`IMPLIED_CATEGORIES`)

| Posiadana kategoria | Uprawnia w macierzy do kategorii |
| --- | --- |
| `AM` | `AM` |
| `A1` | `A1`, `AM` |
| `A2` | `A2`, `A1`, `AM` |
| `A` | `A`, `A2`, `A1`, `AM` |
| `B1` | `B1`, `AM` |
| `B` | `B`, `B1`, `AM` |
| `B+E` | `B+E`, `B`, `B1`, `AM`, `T` |
| `C1` | `C1` |
| `C1+E` | `C1+E`, `C1`, `B+E`, `T` |
| `C` | `C`, `C1` |
| `C+E` | `C+E`, `C`, `C1+E`, `C1`, `B+E`, `T` *(oraz `D+E` / `D1+E`, gdy kierowca posiada równocześnie `D` / `D1`)* |
| `D1` | `D1` |
| `D1+E` | `D1+E`, `D1`, `B+E`, `T` |
| `D` | `D`, `D1` |
| `D+E` | `D+E`, `D`, `D1+E`, `D1`, `B+E`, `T` |
| `T` | `T`, `AM` |

## 4. Zapisy historyczne i zmiana uprawnień

- Zakończone przypisania (`driver_assignments.active = false`) oraz zapisane przejazdy (`trips` / `trip_annotations`) **nigdy nie są kasowane ani przepisywane** po edycji kategorii kierowcy lub DMC pojazdu.
- Ponieważ system przechowuje bieżący zestaw kategorii kierowcy bez historycznych dat nadania poszczególnych kategorii, każde zakończone przypisanie zwraca jawne ostrzeżenie `historical_warning` informujące, że aktualny stan prawa jazdy nie dowodzi uprawnień w dawnej dacie.
- Aktywne przypisania wymagające weryfikacji (`incompatible` oraz `unverified`) są zliczane z podziałem na przyczyny (`category_mismatch`, `missing_driver_categories`, `missing_vehicle_dmc`, `missing_passenger_seats`, `missing_vehicle_requirements`) w kafelku **„Przypisania do sprawdzenia”** (`/api/v1/drivers/summary` i `/api/v1/drivers/search`).
