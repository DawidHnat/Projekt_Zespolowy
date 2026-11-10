# SCRUM-20 — lista pojazdów i wspólne filtry

Uzupełnienie implementacji z PR #13, na aktualnym `main`, 09.11.2026.
Lista, galeria i mapa nadal korzystają z jednego `FleetProvider` oraz API.

## Poprawione zachowanie

- Zmiana wyszukiwania, statusu, strony lub limitu ukrywa wyniki poprzedniego
  zapytania. Dotyczy to także oczekiwania na debounce i błędu nowego żądania.
- Błąd odświeżania tych samych kryteriów zachowuje pasujące dane i pokazuje
  ostrzeżenie z czasem ostatniego poprawnego odczytu.
- Mapa dzieli wyszukiwanie i status z listą, ale obejmuje wszystkie strony.
  Przy błędzie nowej strony lista pozwala wrócić do poprzedniej strony.
- „Wyczyść filtry” usuwa wyszukiwanie i status, wraca na stronę 1 i usuwa
  wybór pojazdu. Działa również z klawiatury. Kontrolki zawijają się bez
  zwężania opisu statusu do kilku liter.
- Ładowanie i błąd mają osobne komunikaty; nie udają pustej floty.
- Brak sieci przy wejściu do widoku lub zmianie filtrów kończy stan ładowania
  czytelnym komunikatem. Pasujący cache pozostaje dostępny z ostrzeżeniem;
  nowe filtry nie pokazują starych wyników. Powrót sieci wznawia pobieranie.
- Po wyczyszczeniu filtrów fokus wraca do wyszukiwarki, również po Enter.

## Walidacja autora

- `npm test`: 50/50 PASS; `npm run build`: PASS.
- Pełna regresja Playwright: 38/38 PASS na komputerze i małym ekranie.
- Powtórna weryfikacja wieczorna: przed poprawką trzy scenariusze na komputerze
  wykazały zgubiony fokus i niekończące się ładowanie przy braku sieci.
  Te same scenariusze po poprawce przechodzą; sprawdzono też ostrzeżenie
  z zachowanym cache, brak żądań offline i automatyczny powrót połączenia.
- Przypadki SCRUM-20 w `frontend/e2e/critical-flow.spec.ts`: opóźniony/błędny
  filtr i ponowienie, błąd strony i powrót, wspólne filtry/wybór/reset,
  zachowanie cache przy błędzie odświeżania bez zmiany kryteriów, zmianę
  filtrów offline oraz montowanie widoku, gdy przeglądarka już zgłasza brak sieci.
- Chromium: 1440 × 1000 i 390 × 844. Jasny i ciemny motyw, reset klawiszem
  Enter, nazwa/rejestracja, brak prędkości, przebieg w km oraz czas polski.
  Zrzuty generują testy w `frontend/test-results/`.

Testy używają lokalnego API, PostgreSQL `fleet_flow_test_e2e` i syntetycznych
rekordów wyłącznie w odizolowanym środowisku E2E. Wywołania poza localhost
są blokowane. Sprawdzono listę obok mapy i fallback bez tokenu Mapbox;
renderowanie mapy z żywym dostawcą nie jest objęte tym sprawdzeniem.

## Niezależny odbiór

Review: Jakub Nazarewicz. QA: Marcel Głowacki, zgodnie z zadaniem Jira.
Wynik autora nie zastępuje tych odbiorów. Przed zamknięciem SCRUM-20:

1. Wyszukaj nazwę i rejestrację; zmień status. Sprawdź puste wyniki.
2. Przejdź z galerii na mapę. Filtry i wybrany pojazd muszą być wspólne.
3. Przy wolnym lub błędnym API zmień filtr/stronę. Poprzednie pojazdy nie
   mogą występować jako wyniki nowych kryteriów. Sprawdź Ponów i powrót strony.
4. Wywołaj błąd odświeżania bez zmiany filtrów. Pasujący cache pozostaje
   widoczny z jawnym ostrzeżeniem i czasem odczytu.
5. Wyczyść filtry klawiaturą, także w małym widoku i ciemnym motywie.
   Sprawdź pomiary 0, brak pomiaru, jednostki i czas Europe/Warsaw.
6. Wyłącz sieć i zmień filtr, a następnie otwórz widok ponownie offline.
   Zamiast ciągłego ładowania ma być komunikat; po przywróceniu sieci
   dane mają pobrać się automatycznie.

Powiązanie gałęzi i PR jest zapisane w Jira. Automatyczne tworzenie gałęzi
w Jira pozostaje osobną, wyłączoną konfiguracją oczekującą na autoryzację
właściciela repozytorium; ta zmiana nie deklaruje jej uruchomienia.
