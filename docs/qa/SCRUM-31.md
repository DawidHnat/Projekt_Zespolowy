# SCRUM-31 — reguły dziennego dystansu i alerty

Zakres: backend tworzenia, edycji i wyłączania reguł oraz jeden alert na regułę,
pojazd i polski dzień pomiaru. Próg dotyczy dziennego dystansu zgodnie ze
Story SCRUM-7. Formularz/lista we frontendzie (SCRUM-32) oraz odbiór zespołu
w SCRUM-33 pozostają osobno; ta instrukcja nie potwierdza odbioru przez Marcela.

## Przypadki automatyczne

`backend/tests/test_distance_alerts.py` używa wyłącznie danych syntetycznych:

- Utworzenie reguły, edycja progu/pojazdu, wyłączenie i ponowne włączenie;
  dodatni próg z dokładnością 0,1 km, odrzucenie zer, wartości ujemnych,
  nieskończoności, pustego PATCH i pól spoza kontraktu.
- Reguła obejmująca jeden pojazd lub całą flotę, bez pojazdów nieaktywnych
  i innych kont źródła; zapisy tylko dla admin/editor i z poprawnym Origin.
- Próg 10 km: licznik 100 000 km nie generuje alertu; przyrost dokładnie
  10 km także nie; 10,1 km daje jeden alert, zachowany po zmianie reguły.
- Wykrycie kolejnego dnia, zimowe/letnie granice północy i zmiany DST;
  równe odczyty i ponowne przeliczenia nie tworzą duplikatów.
- Brak pomiaru/czasu/licznika, cofnięcie licznika, odczyt przyszły, odstęp
  większy niż 15 minut i odcinek przez północ nie dopisują fikcyjnych kilometrów.
  Kolejny poprawny odcinek po resecie zaczyna nową obserwację.
- Stan dystansu i alertów utrzymuje się między sesjami bazy; zaznaczenie
  przeczytania jest idempotentne i prywatne per użytkownik, także dla viewer.
- Stabilna paginacja i filtr odczytu. PostgreSQL: równoległe przeliczenie
  daje jeden alert; wspólny worker tworzy alert dopiero po przyroście licznika.
  Test migracji sprawdza upgrade/check/downgrade/upgrade/check.

Kontrole lokalne w `backend/`: `ruff check .`, `ruff format --check .`, `pytest`.
Wynik 11 października 2026: Ruff i formatowanie poprawne, **100 passed,
4 skipped** (testy PostgreSQL bez lokalnej testowej bazy). Jedno istniejące
ostrzeżenie dotyczy deprecjacji klienta HTTPX w Starlette.
Bez `TEST_DATABASE_URL` cztery testy PostgreSQL są pomijane; ich odbiór wymaga
zielonego CI na PostgreSQL 17 dla Pythona 3.12 i 3.13. Testy odrzucają bazę,
której nazwa nie zaczyna się od `fleet_flow_test`. Nie używaj lokalnej bazy
klienta ani jej URL do testów migracji.

## Sprawdzenie API przez QA

1. Na własnej testowej bazie wykonaj `alembic upgrade head`, utwórz konto
   testowe przez `app.manage` i zaloguj się. Nie publikuj danych klientów.
2. W `/docs` wywołaj `POST /api/v1/analytics/rules` z progiem i opcjonalnym
   UUID pojazdu, następnie GET i PATCH. Zapisy wymagają dozwolonego Origin;
   w lokalnym Swaggerze dodaj jego adres do testowego `CORS_ORIGINS`.
3. Dwa kolejne poprawne odczyty w tym samym dniu ustalają zaobserwowany
   dystans. Przyrost większy niż próg daje alert w `/analytics/alerts`.
   Powtórzenie odczytu i PATCH reguły w tym samym dniu nie duplikują zdarzenia.
4. Wyłącz regułę; kolejny dzień nie powinien tworzyć nowego alertu dla niej.
   Sprawdź odczyt alertu z dwóch kont — zmiana jednego nie wpływa na drugie.
5. Zapisz wynik odbioru i ewentualne uwagi w SCRUM-31/33 z linkiem do PR/CI.

`coverage: "partial"` jest celowe. Obecny worker obserwuje przyrosty od
uruchomienia i nie odtwarza dnia wstecz. Brakujący dystans nie jest zerem;
alert dowodzi przekroczenia już zaobserwowanej dolnej granicy. Historia
przejazdów i pełne zestawienia wymagają SCRUM-24/29. Implementacja nie wysyła
e-maili/SMS, nie pobiera kierowców i nie zmienia konfiguracji VPS.
