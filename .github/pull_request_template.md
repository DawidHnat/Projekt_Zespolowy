## Zadanie

Jira: <!-- rzeczywisty klucz, np. SCRUM-123 -->

## Zmiana

<!-- Co zmieniono i dlaczego? -->

## Sprawdzenie

<!-- Jak sprawdzono zmianę? Dla samej struktury: lista katalogów i puste pliki. -->

- [ ] Zakres odpowiada zadaniu.
- [ ] Diff nie zawiera sekretów ani `.env`.
- [ ] Zmiana jest gotowa do przeglądu drugiej osoby.

## Security / SCRUM-101 (jeśli dotyczy)

- [ ] Sprawdzono wpływ zmiany na auth, sesje, role, Origin/CSRF, izolację danych i walidację.
- [ ] Jeśli zmiana dotyczy tych obszarów: identyfikatory ASVS v5.0.0, wynik PASS/FAIL/BLOCKED lub N/A z uzasadnieniem, SHA i środowisko zapisano w PR/Jira.
- [ ] Security regression (w tym negatywne przypadki i błędy 401/403/422) wykonano albo jawnie uzasadniono N/A.
- [ ] Zmiany schematu mają sprawdzone migracje i dowód restore/rollback albo jawne N/A.
- [ ] Niezależny reviewer sprawdził skuteczność kontroli oraz brak sekretów i danych klientów; QA zachowuje odrębną rolę.