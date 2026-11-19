# Zakres przeglądarek — decyzja PO 19.11.2026

Wykonawca zapisu: **agent Codex na polecenie Jakuba Czai**. Data decyzji:
19.11.2026; kontekst kodu: `cb634da0ece8cd93424bfc16a5185cf817a0cbb1`.
Dowód: bezpośrednia odpowiedź PO w bieżącej rozmowie. Jest to decyzja zakresu,
bez wykonania testu i bez podpisywania niezależnego QA.

PO zakwestionował wymaganie Safari przy braku dostępu Marcela i polecił
rozwiązać to inaczej albo pominąć. Dla obecnego projektu przyjmujemy:

| Środowisko | Wymagany odbiór |
| --- | --- |
| Desktop | Główna przeglądarka używana przez zespół: Chrome albo Edge; zapisać dokładną wersję. Dwa niezależne konteksty mogą działać w tym samym silniku. |
| Mały ekran | Profil 390 px / emulacja telefonu, układ, klawiatura i obsługiwane gesty; raport rozróżnia emulację od fizycznego telefonu. |
| Safari/macOS | Poza obowiązkowym zakresem obecnego odbioru; **nie wykonano**, brak deklaracji kompatybilności ani PASS. |

Zmiana dotyczy literalnego wymagania Safari w **SCRUM-21 AC4,
SCRUM-23 i SCRUM-40**, zgodnie z decyzją PO. Zachowujemy historyczne opisy
i wyniki z datami; nowy zapis określa bieżący zakres. Nie oznacza zamknięcia
innych kryteriów tych zadań, rzeczywistej mapy lub nowych pól źródła.

**Dwa konta syntetyczne pozostają potrzebne dla SCRUM-91 AC4.** Sprawdzają
dwóch użytkowników tej samej firmy, w tym naprawiony błąd przeniesienia
preferencji A→B (SCRUM-144/#99); nie wymagają dwóch firm ani dwóch API.
Testy E2E mają już osobne `e2e-editor`, `e2e-editor-two` i `e2e-viewer`.
Ich konta i dane powstają tylko w opt-in bazie `fleet_flow_test_e2e`
na localhost, nigdy w produkcie. Autor testów nie staje się niezależnym QA.

Następny krok **Marcela**: użyć uzgodnionego izolowanego środowiska, zapisać
wykonane brakujące AC, datę, SHA, środowisko, dowód i PASS/FAIL/BLOCKED.
**Jakub Czaja** organizuje dostęp; **Dawid Hnat** potwierdza środowisko
operatora tam, gdzie kryterium dotyczy wdrożenia. Nie tworzymy kont na VPS
ani nie dodajemy sztucznej floty przez samą zmianę tego dokumentu.
