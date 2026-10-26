# SCRUM-49 — profil i bezpieczeństwo konta, pierwszy przyrost

Zakres tego PR: odczyt własnego profilu, zmiana hasła z ponownym uwierzytelnieniem,
rotacja sesji, wylogowanie wszystkich urządzeń i opcjonalna notyfikacja SMTP.
Story nie jest w całości ukończona: potwierdzanie nowego e-maila, test dostawy
na uzgodniony adres, niezależne review oraz odbiór QA pozostają do wykonania.
Nie ma edycji roli/statusu ani administracji cudzym kontem. W danych profilu
imię i nazwisko są istniejącym polem `display_name`; brak e-maila pokazuje
„Nie ustawiono”. Story pozostaje poza Sprintem 1.

## Scenariusze Marcela

Użyj osobnych kont i syntetycznych danych w środowisku testowym. Zmiana hasła
wspólnego `qa-team` dotyczyłaby wszystkich testerów — wykonuj ją wyłącznie po
uzgodnieniu z zespołem. Ten przyrost nie zmienia hasła `qa-team` na VPS.

1. Zaloguj się i kliknij własną nazwę pod menu. Profil pokazuje tylko dane
   bieżącego konta, również przy bezpośrednim wejściu na `#profile`. Brak sesji
   prowadzi do logowania. E-mail/rola/status nie są polami edytowalnymi.
2. Otwórz dwie niezależne sesje (np. Safari i drugi profil przeglądarki).
   Zmień hasło w pierwszej: wymagane aktualne hasło, nowe 12–1024 znaki i
   zgodne powtórzenie. Po sukcesie hasła w formularzu są puste, pierwsza sesja
   działa z nowym cookie, druga dostaje 401 i wraca do logowania. Stare hasło
   nie loguje; nowe loguje. Stare linki resetu nie działają.
3. Błędne obecne hasło daje czytelny błąd i zachowuje sesję. Niezgodne powtórzenie,
   za krótkie, zbyt długie i identyczne hasło są odrzucane. Hasła nie są
   przycinane ani zapisywane w localStorage. Po odpowiedzi API formularz
   usuwa wpisane hasła. Szósta próba na konto w 15 min daje 429.
4. „Wyloguj wszystkie urządzenia” pokazuje potwierdzenie. „Anuluj” zachowuje
   sesje. Potwierdzenie wylogowuje także bieżące urządzenie. Sesje innych kont
   pozostają aktywne. Ponowne logowanie działa.
5. Brak sieci/błąd API nie pokazuje fałszywego sukcesu. Można ponowić odczyt
   profilu lub operację; wygaśnięcie sesji usuwa prywatny widok. Sprawdź klawiaturę,
   Safari, 390 px, jasny/ciemny oraz szkło/klasyczny. Dane floty nie są wymagane
   do korzystania z profilu.
6. Testy z atrapą poczty potwierdzają adresata i brak sekretów w notyfikacji.
   Brak e-maila lub konfiguracji SMTP pomija notyfikację; awaria wysyłki nie
   cofa hasła i nie ujawnia błędów transportu. Faktyczne doręczenie jest
   osobnym odbiorem na zatwierdzony adres, poza CI.

## Weryfikacja autora

- `frontend/`: `npm test`, `npm run build`.
- `backend/`: `ruff check .`, `ruff format --check .`, `pytest` z
  `TEST_DATABASE_URL` do izolowanego PostgreSQL 17. Test migracji czyści bazę;
  jej nazwa musi zaczynać się od `fleet_flow_test`.
- Test równoczesnych zmian hasła: z dwóch żądań używających starej sesji jedno
  wygrywa, drugie dostaje 401 po ponownym sprawdzeniu sesji pod blokadą User.
- Browser: profil, responsywność i wylogowanie wszystkich sesji na osobnym
  syntetycznym koncie. Formularz zmiany hasła ma automatyczne testy walidacji
  i API; ręczny odbiór całej ścieżki przez QA pozostaje wymagany.
