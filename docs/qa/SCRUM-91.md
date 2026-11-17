# SCRUM-91 — procedura niezależnego QA

Story jest odbierana dopiero po niezależnym review developera i potwierdzeniu
wszystkich kryteriów przez Marcela Głowackiego na dokładnym wdrożonym SHA.
Jakub Nazarewicz jest autorem, nie reviewerem własnej zmiany. Dawid Hnat lub
Jakub Czaja wykonuje review. Ten dokument opisuje powtarzalny test; sam w sobie
nie jest wynikiem QA.

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

### E. Świadoma migracja `localStorage`

1. W świeżym, odizolowanym profilu przygotuj istniejące ustawienia lokalne
   przed logowaniem. Przy koncie bez preferencji sprawdź prompt migracji;
   backend przed wyborem ma nadal zwracać wersję `0` i `value: null`.
2. Wykonaj jawnie każdą decyzję w osobnym przebiegu: **Przenieś z tej
   przeglądarki** oraz **Użyj domyślnych konta**. Sprawdź zapis i nową wersję.
3. Dla konta z nowszą wartością w backendzie przygotuj różną wartość lokalną.
   Prompt nie może zastąpić wartości konta ani pokazać ustawień poprzedniego
   użytkownika. Samo odświeżenie i automatyczny polling nie są zgodą na import.

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
  compare-and-swap, Origin i granice wymiarów;
* `frontend/e2e/critical-flow.spec.ts` — dwa konteksty, konflikt, przełączenie
  konta, migracja i zapis;
* `frontend/tests/dashboard-preferences.test.mjs` oraz
  `frontend/tests/bulk-layout-pagination.test.mjs` — model układu i rozmiarów.

## Migracja bazy i wymagany dowód

`backend/migrations/versions/0006_account_preferences.py` tworzy tabelę
`account_preferences`, klucz per użytkownik/moduł, ograniczenia wersji i nazw
modułów. Test przejścia migracji nie jest operacyjnym dowodem odtworzenia.
Dawid Hnat ma dołączyć bezpieczny wynik próby restore/rollback z izolowanej
kopii przed uznaniem warunku DoD za PASS. W tym przekazaniu takiej próby nie
wykonano.
