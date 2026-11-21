# SCRUM-49 · Profil i bezpieczeństwo konta

Profil jest dostępny przez własną nazwę w menu oraz pod adresem `#profile`.
Pokazuje imię, nazwisko, login, aktualny e-mail i rolę. Dla starszych kont
bez osobnych pól imienia i nazwiska wyświetla zapisaną nazwę konta.
Rolą i statusem konta zarządza administrator w sekcji Użytkownicy.
[Scenariusze administracji kontami](SCRUM-48.md).

## Scenariusze odbioru

Użyj syntetycznych kont w środowisku testowym, dwóch niezależnych profili
przeglądarki i skrzynki wskazanej do testów doręczenia.

1. Wejdź do Profilu przez menu i przez `#profile`. Wygaśnięcie sesji prowadzi
   do logowania. Sprawdź klawiaturę, szerokość 390 px, motyw jasny i ciemny
   oraz style przezroczysty i klasyczny.
2. Zmień hasło. Potwierdź aktualne hasło, wpisz nowe od 12 do 1024 znaków
   i powtórz je zgodnie. Błędne aktualne hasło i nieprawidłowe nowe hasło dają
   czytelny błąd. Po odpowiedzi API pola hasła są puste. Po udanej zmianie
   bieżąca przeglądarka ma nową sesję, pozostałe kończą się z 401, stare linki
   resetu tracą ważność i działa logowanie nowym hasłem. Szósta próba zmiany
   na jedno konto w ciągu 15 minut daje 429.
3. Wybierz „Zmień adres e-mail”, wpisz nowy adres i aktualne hasło, a następnie
   wybierz „Wyślij link potwierdzający”. Podczas wysyłki przycisk jest
   nieaktywny. Po wysyłce pojawia się komunikat z adresem docelowym.
   Profil i logowanie nadal korzystają z dotychczasowego adresu.
4. Otwórz link w drugim profilu przeglądarki. Zaloguj się dotychczasowym
   loginem lub adresem i wybierz „Potwierdź zmianę adresu”. Po sukcesie Profil
   pokazuje nowy adres, a link znika z paska adresu. Możesz się zalogować nowym
   adresem. Sesja potwierdzająca pozostaje aktywna dzięki nowemu cookie,
   a pozostałe sesje i stare linki do odzyskiwania konta tracą ważność.
5. Sprawdź wygasły link, ponowne użycie linku oraz próbę potwierdzenia z innego
   konta. Wszystkie zgłaszają błąd i zachowują dotychczasowy adres. Link jest
   ważny przez 20 minut. Jeżeli inne konto używa adresu jako e-maila lub loginu,
   API zwraca 409 przy potwierdzeniu. Zmiana hasła unieważnia oczekujący link.
6. Sprawdź brak konfiguracji poczty i odrzucenie wiadomości. Formularz zmiany
   e-maila pokazuje czytelny błąd i zachowuje dotychczasowy adres. Po nieudanym
   ponowieniu poprzedni ważny link nadal działa. Powiadomienie o zmianie hasła
   jest wysyłane po skonfigurowaniu SMTP. Awaria tego powiadomienia zachowuje
   zmienione hasło.
7. „Wyloguj wszystkie urządzenia” wyświetla potwierdzenie. Anulowanie zachowuje
   sesje, a potwierdzenie wylogowuje także bieżącą przeglądarkę. Inne konta
   mają nadal dostęp. W tym samym profilu przeglądarki druga karta usuwa
   prywatny widok i szkice bez oczekiwania na odpytywanie API. Po zmianie hasła
   lub e-maila karta korzysta z odświeżonej wspólnej sesji.

## Weryfikacja techniczna

- Uruchom `npm test` i `npm run build` w `frontend/` oraz `ruff check .`,
  `ruff format --check .` i `pytest` w `backend/`. Testy integracyjne
  wymagają odizolowanego PostgreSQL 17 z bazą o nazwie zaczynającej się
  od `fleet_flow_test`. CI uruchamia Playwright na desktopie i mobile
  z atrapą poczty.
- Migracja `0013_email_confirmation` wymaga `0012_account_administration`.
  Test równoczesnego potwierdzenia weryfikuje, że jeden link daje jedną zmianę
  i że ten sam adres może zostać przypisany jednemu kontu.
- Doręczenie wiadomości na uzgodnioną skrzynkę oraz niezależny przegląd PR
  i odbiór QA są wymagane przed zakończeniem zadania.
