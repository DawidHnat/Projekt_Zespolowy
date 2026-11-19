# SCRUM-150 — odświeżanie i bieżący stan floty

[Zadanie](https://fleet-flow.atlassian.net/browse/SCRUM-150) realizuje polecenie
PO z 18.11.2026. Korzysta z poprawki km/h SCRUM-22 / PR #115. Nie zastępuje
analityki okresów i porównań pojazdów SCRUM-30.

## Zachowanie do odbioru

1. Przycisk przy prawej stronie mapy oraz w podglądzie auta sprawdza źródło
   przez backend. Jedna próba obejmuje wspólną flotę, więc nie ma osobnych
   wywołań WEBFLEET dla każdego auta.
2. Podczas odczytu oba przyciski pokazują postęp. Kolejna próba jest dostępna
   według backendu: domyślnie po 60 s. Odliczanie jest widoczne również po
   wejściu z innej karty lub przeładowaniu. Limit obejmuje automatycznego workera.
3. Kliknięcie/Enter podczas oczekiwania wyświetla subtelny opis; nie wykonuje
   kolejnego POST. Nawet POST wysłany z pominięciem UI nie omija globalnej blokady
   i cooldownu w PostgreSQL. Backoff dostawcy wydłuża odliczanie.
4. Po odpowiedzi odświeżają się mapa, lista, szczegóły i podsumowanie. Zachowane
   są filtr, wybór i niezapisana edycja przejazdu. Samo pobranie nie zmienia
   czasu GPS; wynik „Sprawdzono najnowsze dane” nie wymusza pomiaru w urządzeniu.
5. Brak sieci, nieznana dostępność, wyłączone źródło oraz błąd mają jawny stan.
   Przycisk nie włącza synchronizacji i nie zmienia konfiguracji VPS.
6. Wykorzystanie pokazuje rzeczywiste liczniki i udział w ruchu z podsumowania
   całej floty. Przykład wyłącznie testowy: 1 w ruchu, 1 na postoju, 1 pozostały
   oznacza 33%, nawet gdy filtr listy pokazuje jedno auto.
7. Pozostałe obejmują starsze i brakujące statusy. Brak odpowiedzi API to kreski,
   pusta flota to 0 pojazdów bez procentu, a same niepotwierdzone statusy to „—”,
   nie fałszywe 0%. Błąd odczytu zachowuje dostępny wynik z opisem ostatnich danych.
8. Kontrolki mieszczą się na 1440, 390 i 320 px; klawiatura zachowuje fokus,
   sekundy nie są ogłaszane co sekundę czytnikowi, ograniczenie ruchu działa.

## Walidacja autora — 18.11.2026

- Backend: `ruff check .`, `ruff format --check .` PASS, `pytest` 212/212 PASS
  z izolowanym PostgreSQL. Nowe testy obejmują auth/Origin, wyłączone źródło,
  zimny cache, dwie sesje użytkownika, konkurencyjne żądania, wspólny limit
  z workerem, Retry-After dostawcy, zachowanie cache i bezpieczne błędy.
- Frontend: `npm test` 61/61 PASS, `npm run build` PASS. Dodane trwałe testy
  Playwright: współdzielone odliczanie/reload, zachowanie filtrów/wyboru oraz
  rzeczywiste/brakujące/błędne/niepotwierdzone/puste podsumowanie; 4/4 PASS
  na projektach desktop i mobile z syntetycznymi odpowiedziami nowych endpointów.
- Dodatkowo Chromium na zbudowanej aplikacji z rzeczywistym lokalnym FastAPI,
  izolowanym PostgreSQL i syntetycznym klientem źródła: desktop 1440 × 1000
  jasny, mobile 390 × 844 ciemny, 320 × 844 jasny. Przypadki 1–7 PASS, w tym
  mapa i podgląd, zmiana współrzędnych/prędkości, drugi użytkownik, wspólny
  cooldown, odliczanie, blokada przedwczesnego POST, filtr i wybór, niezapisany
  formularz, offline, backoff/błąd, odzyskanie danych oraz pusty cache floty.
  Zrzuty obejrzane; brak poziomego przewijania całej strony.

Testy nie używały żywego WEBFLEET, SMTP, sekretów ani danych klientów.
Żądania zewnętrzne przeglądarki były blokowane; mapa dostawcy nie była testowana.
Konfiguracji VPS i cyklicznych interwałów nie zmieniano.
Walidacja autora nie zastępuje niezależnego review i odbioru QA przed Done.
