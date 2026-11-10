# SCRUM-46 — edycja zbiorowa i paginacja

Weryfikacja 10.11.2026. Podstawa jest scalona w PR #17. Ten przyrost dodaje
regresję przeglądarkową i dowody odbioru; nie zmienia logiki produktu.
Gałąź oparto na PR #71 (SCRUM-45), ponieważ wspólny narożnik wymaga opisanej
tam poprawki zachowania szerokości na telefonie. Najpierw należy odebrać
i scalić #71, następnie przestawić bazę tego PR na `main` i sprawdzić CI.

## Sprawdzone kryteria

1. Zaznaczenie checkboxem z klawiatury i kliknięciem karty działa. Wybór
   dwóch pojazdów z różnych stron pozostaje po zmianie strony i filtra.
2. Wspólny suwak szerokości wyrównuje szerokości, zachowując różne wysokości
   500 i 600 px. Preset Duże wyrównuje oba wymiary. Niezaznaczony pojazd
   widoczny pod aktywnym filtrem pozostaje bez zmian.
3. Wszystkie pojazdy obejmuje również karty poza stroną i filtrem.
   Anuluj przywraca poprzednie rozmiary. Po zapisie nowy, wcześniej
   niezaładowany pojazd otrzymuje zapisany rozmiar domyślny całej floty.
4. Migracja v1 zachowuje indywidualne wymiary. Zapis v2 i odświeżenie
   zachowują nowe rozmiary oraz wcześniej dodane lokalne zdjęcie.
5. Limity 10/25/50/100 działają, zmiana limitu wraca na stronę 1, zakres
   nie przekracza liczby wyników. Pusty wynik ma 0–0 i nieaktywne strzałki.
6. Galeria, tabela i lista przy mapie dzielą limit. Preferencja jest lokalna
   dla konta: drugie konto ma własny limit, powrót właściciela go przywraca.
   Żądania danych mapy nie otrzymują parametrów `page` ani `page_size`.

## Walidacja autora i granice sprawdzenia

- `npm test`: 50/50 PASS; typecheck/build PASS.
- Nowy zestaw SCRUM-46: 6/6 PASS (3 scenariusze × desktop/mobile).
- Pełna regresja z bazą SCRUM-45: 42/42 PASS.
- Testy logowania korzystają z lokalnego backendu i osobnej bazy E2E.
  Flota 26/27 pojazdów to kontrolowane odpowiedzi API przechwytywane tylko
  w kontekście testowej przeglądarki; żadne rekordy demonstracyjne nie są
  dodawane do produktu ani rzeczywistej bazy. Połączenia zewnętrzne są blokowane.
- Sprawdzono zachowanie interfejsu dla wielu stron i pełne, niepaginowane
  żądania mapy. Nie jest to test backendowej paginacji na 26 rekordach ani
  renderowania wszystkich znaczników przez żywy Mapbox. Kontrolowane
  odpowiedzi odpowiadają typom obecnego API.
- Modele testują migrację, granice rozmiarów, niemutowanie zapisu i poprawne
  zakresy paginacji. Zrzuty dialogu mieszanych wymiarów i galerii są w
  `frontend/test-results/`.

Nie znaleziono dodatkowej usterki produktu w tym zakresie. Pierwsza próba
testu oczekiwała licznika mapy w konfiguracji bez tokenu; założenie testu
poprawiono, nie zmieniając zachowania produktu.

## Niezależny odbiór przed Gotowe

Review: Jakub Nazarewicz. QA: Marcel Głowacki / SCRUM-23.

1. Wybierz pojazdy na różnych stronach, zmień filtr i wyrównaj szerokość.
   Różne wysokości oraz niezaznaczone pojazdy muszą pozostać bez zmian.
2. Sprawdź presety, suwaki, klawiaturę i narożnik. Dla narożnika obowiązuje
   także odbiór SCRUM-45, w tym fizyczny dotyk i zwężony ekran.
3. Przy aktywnym filtrze wybierz Wszystkie pojazdy, zmień rozmiar, wyczyść
   filtr i sprawdź inne strony. Sprawdź osobno Anuluj, Zapisz i odświeżenie.
4. Zmień limit na dalszej stronie w galerii, tabeli i liście przy mapie.
   Strona ma wrócić do 1, a mapa zachować wszystkie pasujące GPS, bez
   ograniczenia do strony listy. Potwierdź to na docelowym backendzie i Mapbox.
5. Sprawdź istniejące wymiary i zdjęcia po migracji oraz oddzielenie kont.

Przed zamknięciem wymagane są review i QA, zielone CI, scalenie w kolejności
zależności i sprawdzenie wdrożonej wersji. Wynik autora nie zastępuje odbioru.
