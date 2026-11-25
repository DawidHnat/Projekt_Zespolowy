## Zadanie

Jira: <!-- rzeczywisty klucz, np. SCRUM-123 -->

## Zmiana

<!-- Co zmieniono i dlaczego? -->

## Sprawdzenie

<!-- Jak sprawdzono zmianę? Dla samej struktury: lista katalogów i puste pliki. -->

Ręczne sprawdzenie autora (opcjonalne) <!-- jeśli wykonano, wpisz co sprawdzono, w jakim środowisku i z jakim wynikiem -->

Odbiór przed merge (jeśli wymagają go kryteria zadania) <!-- osoba, SHA, środowisko, scenariusze i wynik -->

QA sprintu lub odbiór wdrożenia (jeśli dotyczy) <!-- link do istniejącej karty QA -->

- [ ] PR kończy cały zakres zadania wskazanego kluczem w gałęzi; częściowy przyrost ma własne zadanie.
- [ ] Drugi developer sprawdził zakres zmiany i wyniki wymaganych kontroli.
- [ ] Diff nie zawiera sekretów ani `.env`.
- [ ] Zmiana jest gotowa do przeglądu drugiej osoby.

Po aktualnym Approved, zielonym wymaganym CI i merge do `main` zadanie
implementacyjne jest **Gotowe**. Osobne QA/regresja zachowuje własny status.

## Security / SCRUM-101 (jeśli dotyczy)

- [ ] Sprawdzono wpływ zmiany na auth, sesje, role, Origin/CSRF, izolację danych i walidację.
- [ ] Jeśli zmiana dotyczy tych obszarów: identyfikatory ASVS v5.0.0, wynik PASS/FAIL/BLOCKED lub N/A z uzasadnieniem, SHA i środowisko zapisano w PR/Jira.
- [ ] Security regression (w tym negatywne przypadki i błędy 401/403/422) wykonano albo jawnie uzasadniono N/A.
- [ ] Zmiany schematu mają sprawdzone migracje i dowód restore/rollback albo jawne N/A.
- [ ] Niezależny reviewer sprawdził skuteczność kontroli oraz brak sekretów i danych klientów; QA zachowuje odrębną rolę.


## SCRUM-121 — evidence gate bezpieczeństwa

Wypełnij dla zmian objętych kontrolami bezpieczeństwa.
Dla pozostałych wpisz N/A wraz z uzasadnieniem.
Brak zatwierdzonej kontroli lub dowodu oznacza BLOCKED.
Szablon nie stanowi pełnego odbioru ASVS L2 ani
nie zamyka zależności SCRUM-120.

**SHA testowanej wersji:**

**Środowisko i wersja wdrożenia:**

**Zakres i identyfikatory ASVS v5.0.0:**

**Dowody:** <!-- link do CI, testów lub Jira -->

| ID ASVS / scenariusz | Wynik | Typ dowodu | Dowód i SHA | Data, wykonawca | N/A: uzasadnienie i akceptujący |
| --- | --- | --- | --- | --- | --- |
| <!-- ID --> | <!-- PASS/FAIL/BLOCKED/N/A --> | <!-- przegląd kodu / test / NOT RUN --> | <!-- link, SHA --> | <!-- data, osoba --> | <!-- powód N/A, imię i rola akceptującego, link do decyzji Jira --> |

### Security checks

- [ ] Sprawdzono odpowiednie scenariusze auth,
      sesji, ról, IDOR i izolacji danych.
- [ ] Origin/CSRF zweryfikowano osobno od CORS
      (allowlista, nagłówki i preflight).
- [ ] Uwzględniono stosowne przypadki negatywne:
      401, 403, 409 i 422.
- [ ] Zweryfikowano cookie i timeouty sesji
      albo wyjaśniono N/A.
- [ ] PASS testu jest potwierdzony na podanym SHA;
      brak dowodu oznaczono BLOCKED/NOT RUN.
- [ ] Ujawniono otwarte FAIL/BLOCKED oraz decyzje
      o ryzyku i powiązane zgłoszenia.
- [ ] Diff nie zawiera sekretów ani danych klientów.
- [ ] Niezależny reviewer sprawdził dowody
      i zakres zastosowanych kontroli.

### Migracje i odtwarzanie

**Migracja (ID, środowisko, data, wykonawca) / N/A z uzasadnieniem:**

**Plan powrotu do poprzedniej wersji (kroki, warunki uruchomienia, właściciel) / N/A z uzasadnieniem:**

**Wpływ migracji i rollbacku na istniejące dane (utrata, nieodwracalność, zgodność schematu) / N/A z uzasadnieniem:**

**Wynik próby restore/rollback (link, SHA, data, wykonawca) / BLOCKED / N/A z uzasadnieniem:**

**Ograniczenia rollbacku, ryzyko, właściciel decyzji i link do zatwierdzenia PO w Jira, jeśli wymagane:**

### Odbiór

**Niezależny reviewer:**

**Wymagane CI i link do przebiegu:**

**QA przed merge, jeśli wymagane:**

**Osobne QA sprintu / wdrożenia, jeśli dotyczy:**

Nie deklarujemy pełnej zgodności ASVS L2 na podstawie
wybranych kontroli ani samego zaznaczenia checklisty.
