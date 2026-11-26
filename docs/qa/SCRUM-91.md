# SCRUM-91 — procedura niezależnego QA

Story jest odbierana dopiero po niezależnym review developera i potwierdzeniu
wszystkich kryteriów przez Marcela Głowackiego na dokładnym wdrożonym SHA.
Jakub Nazarewicz jest autorem, nie reviewerem własnej zmiany. Dawid Hnat lub
Jakub Czaja wykonuje review. Ten dokument opisuje powtarzalny test; sam w sobie
nie jest wynikiem QA.

## Uznany dowód restore — aktualizacja 19.11.2026

Dawid Hnat ocenił próbę autora z 18.11 jako operator **PASS** dla DoD 16/91:
[SCRUM-141/10324](https://fleet-flow.atlassian.net/browse/SCRUM-141?focusedCommentId=10324)
i [10345](https://fleet-flow.atlassian.net/browse/SCRUM-141?focusedCommentId=10345).
Nie powtarzamy jej jako niewykonanej i nie wymagamy odłożonego off-site 84.
Końcowy niezależny QA poniższych AC nadal ma własny zakres i SHA.

## Warunki i dowody wydania

1. Użyj wyłącznie kont testowych zatwierdzonych dla środowiska. Nie zapisuj
   haseł, tokenów, nazw kont ani danych floty w Jira, zrzutach ekranu lub raporcie.
   Nie twórz syntetycznych rekordów na wspólnym serwerze. Gdy nie ma
   zatwierdzonych kont bez danych klientów, wykonaj procedurę w odizolowanym
   środowisku testowym i zgłoś brak dostępu jako BLOCKED.
2. Przed testem zanotuj pełny SHA `origin/main`, link do udanego CI tego SHA
   oraz czas. Otwórz [środowisko HTTPS](https://fleet-flow.pl/) i sprawdź
   `/api/health/ready` (HTTP 200). Strona wersji pod
   `http://57.129.179.53/` musi pokazywać siedmioznakowy SHA zgodny z pełnym
   SHA `origin/main`. Nie odbieraj wersji PR ani nie scalonego kodu.
3. Zapisz osobno wykonawcę, datę, przeglądarkę/urządzenie, dokładny SHA,
   oczekiwany i faktyczny wynik, status PASS/FAIL/BLOCKED oraz bezpieczny link
   do dowodu. Wynik automatyczny lub test autora nie jest niezależnym QA.

## Przypadki ręczne

### A. To samo konto w dwóch niezależnych kontekstach

1. Zaloguj się do tego samego zatwierdzonego konta w dwóch profilach
   przeglądarki lub na dwóch urządzeniach. Nie kopiuj ciasteczek sesji.
2. W kontekście 1 zmień układ Pulpitu dla desktopu i wąskiego widoku, rozmiar
   kafelka, a następnie użyj Zapisz. W kontekście 2 odśwież widok i sprawdź,
   że zapisane ustawienia wróciły.
3. W Pojazdach zmień rozmiar jednej karty oraz wspólny rozmiar, sortowanie,
   tekst i status filtra oraz limit 10/25/50/100. Sprawdź odtworzenie w drugim
   kontekście i po wylogowaniu/zalogowaniu.
4. Pozostaw niezapisany szkic w kontekście 2. Zapisz inną zmianę w kontekście
   1. Szkic kontekstu 2 ma pozostać otwarty i niezmieniony przez odświeżenie
   stanu z serwera.

### B. Zapis, anulowanie, reset i awaria

1. Zmień układ bez zapisywania i wybierz **Anuluj**. Po odświeżeniu API i UI
   wartość ma pozostać niezmieniona.
2. Przywróć ustawienia domyślne, anuluj i sprawdź ponownie, że serwer nie
   zmienił wersji ani wartości. Następnie wykonaj reset ponownie i zapisz;
   sprawdź domyślną wartość po ponownym odczycie.
3. Przy aktywnej edycji włącz tryb Offline w DevTools, zmień układ i zapisz.
   Oczekiwany jest widoczny komunikat błędu, otwarty edytor i zachowany szkic,
   bez komunikatu o sukcesie. Po przywróceniu sieci odczytaj preferencje i
   potwierdź, że nieudana próba nie zmieniła wartości ani wersji. Zapisz
   faktyczny status żądania z panelu Network, nie tokeny ani nagłówki sesji.

### C. Konflikt wersji

1. W dwóch kontekstach tego samego konta odczytaj tę samą wersję.
2. Zapisz zmianę w kontekście 1. Spróbuj zapisać nieaktualny szkic w kontekście
   2. Oczekiwany jest konflikt `VERSION_CONFLICT` i czytelna decyzja.
3. Wykonaj osobno **Wczytaj wersję z konta** i **Zapisz moje zmiany**.
   Pierwsza decyzja ma zachować wersję serwera; druga ma jawnie zapisać szkic
   na podstawie aktualnej wersji. W obu przypadkach potwierdź nową wartość
   odczytem API.

### D. Izolacja drugiego konta

1. Zapisz rozpoznawalny, niesekretny układ konta A. Wyloguj się w tej samej
   przeglądarce i zaloguj na zatwierdzone konto B bez zapisanych preferencji.
2. B ma widzieć własne ustawienia domyślne lub własny zapis; nie może zobaczyć
   ani zapisać układu A. Sprawdź to dla Pulpitu i Pojazdów oraz przez odczyt
   API zalogowanego B.
3. Zapisz zmianę B, wróć do niezależnego kontekstu A i sprawdź, że wartość A
   pozostała niezmieniona. Nie zapisuj tożsamości kont w raporcie.

### E. Jawny import starych ustawień — aktualizacja SCRUM-148

1. W świeżym, odizolowanym profilu przygotuj stare ustawienia localStorage
   przed logowaniem. Zwykłe logowanie ma pokazać ustawienia konta lub domyślne,
   bez komunikatu ani blokady importu. API przed importem nadal zwraca wersję
   `0` i `value: null`.
2. Przejdź do **Ustawienia → Układ i moduły** i jawnie wybierz import. Sprawdź,
   że zapis używa wersji `0`, obejmuje pola możliwe do migracji i odtwarza się
   po odświeżeniu. Import Pojazdów jest osobną akcją w tym samym widoku.
3. Dla konta z nowszą wartością w backendzie przygotuj różne stare ustawienia.
   Nie pokazuj importu i nie zastępuj wartości konta. Samo odświeżenie ani
   automatyczny zapis kolejnej zmiany nie może importować starego kandydata.
4. Sprawdź pierwsze logowanie A, kiedy odczyt ustawień zwraca błąd albo zostaje
   przerwany przez wylogowanie. Bez przeładowania strony zaloguj B: B ma
   ustawienia domyślne, bez kandydata A. Po powrocie na A import może być
   dostępny wyłącznie w Ustawieniach.
5. Zapisz własne tło jako WebP, sprawdź chronione odczytanie przez
   `/api/v1/preferences/background/{id}` w drugim kontekście tego samego konta,
   brak dostępu drugiego konta oraz usunięcie. Zdjęcia pojazdów nadal są
   lokalne i nie są objęte tym API.

## API i istniejące testy

Zalogowany klient odczytuje i zapisuje moduły:

* `GET /api/v1/preferences/dashboard` i `PUT /api/v1/preferences/dashboard`;
* `GET /api/v1/preferences/vehicles` i `PUT /api/v1/preferences/vehicles`.

Odpowiedź zawiera `module`, `version`, `value` i `updated_at`. PUT wymaga
dozwolonego nagłówka `Origin` oraz JSON `{ "version": n, "value": ... }`.
Nieaktualna wersja zwraca HTTP 409 z `VERSION_CONFLICT`; błędne wartości
zwracają 422. Raportuj status i niesekretny kod błędu, nigdy ciasteczka,
tokeny lub pełne nagłówki.

Regresje automatyczne:

* `backend/tests/test_account_preferences.py` — izolacja kont/modułów,
  compare-and-swap, Origin, tapeta konta i granice wymiarów;
* `frontend/e2e/account-preferences.spec.ts` i
  `frontend/e2e/critical-flow.spec.ts` — dwa konteksty, konflikt, przełączenie
  konta, jawny import i zapis;
* `frontend/tests/dashboard-preferences.test.mjs` oraz
  `frontend/tests/bulk-layout-pagination.test.mjs` — model układu i rozmiarów.

## Migracja bazy i wymagany dowód

`backend/migrations/versions/0006_account_preferences.py` tworzy tabelę
`account_preferences`, klucz per użytkownik/moduł, ograniczenia wersji i nazw
modułów. Test przejścia migracji nie jest operacyjnym dowodem odtworzenia.
Dawid Hnat sprawdza dowód restore/rollback z izolowanej kopii przed uznaniem
warunku DoD za PASS. [Lokalna próba z 18.11.2026](SCRUM-91-restore-20261118.md)
wykonana przez agenta na polecenie Jakuba Czai odzyskała obie preferencje,
także po downgrade/upgrade. Nie jest to odbiór operatora ani dowód kopii VPS.
