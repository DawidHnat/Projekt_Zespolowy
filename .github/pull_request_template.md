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

## Obowiązkowe bramy przed merge — bez N/A

Szablon służy do zapisania dowodu; nie egzekwuje ochrony gałęzi.
Reviewer sprawdza rzeczywiste Checks i aktualne ustawienia ochrony `main`.
Jeżeli autor nie ma uprawnień do odczytu ustawień, wynik jest BLOCKED
do potwierdzenia przez właściciela repozytorium.

**Head SHA PR i testowany merge SHA (jeśli inny):**

**Środowisko, link do przebiegu i data:**

**Odczyt ochrony main (data, osoba, link/dowód, wymagane konteksty):**

Wypełnij każdy wiersz osobnym wynikiem oraz linkiem do odpowiedniego
jobu lub dowodu na aktualnym SHA. Nazwy poniżej odpowiadają workflow
CI; dla rozdzielonych profili zapisz oba wyniki zamiast jednego.
Sprawdź także dodatkowe wymagane konteksty, jeżeli wynikają z ustawień
ochrony. Nie deklaruj ich aktywności na podstawie samego szablonu.

| Obowiązkowa kontrola | Wynik | Dowód (link do jobu/ustawień/review i SHA) |
| --- | --- | --- |
| Required CI (agregator) | <!-- PASS/FAIL/BLOCKED --> | |
| Lint | | |
| Backend (3.13) | | |
| Backend (3.12) | | |
| Frontend build | | |
| Backend image | | |
| Dependency security | | |
| Source security | | |
| Secret security | | |
| Markdown links | | |
| Critical browser flows — desktop i mobile (wspólny job lub osobne profile) | | |
| Aktualne niezależne review i kontrola diffu pod kątem sekretów/danych klientów | | |

- [ ] Wszystkie obowiązkowe joby zakończyły się success; FAIL, skipped
      lub brak dowodu blokują merge. N/A nie zastępuje obowiązkowego checka.
- [ ] Odczyt ochrony main potwierdza wymagane konteksty i egzekwowanie
      PR oraz niezależnego zatwierdzenia; rozbieżności zapisano w Jira.
- [ ] Reviewer zweryfikował aktualny SHA, zakres zmiany i wyniki.

## SCRUM-101 / SCRUM-121 — kontrole bezpieczeństwa zależne od zakresu

Dla każdej pozycji określ, czy dotyczy zmiany. N/A oznacza wyłącznie
kontrolę, która rzeczywiście nie dotyczy zakresu PR; wymaga uzasadnienia
i akceptacji osoby uprawnionej. Brak testu lub dowodu nie jest N/A.
Szablon nie stanowi pełnego odbioru ASVS L2 ani nie zamyka SCRUM-120.

**Zakres i identyfikatory ASVS v5.0.0:**

**SHA testowanej wersji, środowisko i wersja wdrożenia:**

| Scenariusz / ID ASVS | Zastosowanie | Wynik | Typ dowodu | Dowód i SHA | Data, wykonawca | N/A: uzasadnienie i akceptujący |
| --- | --- | --- | --- | --- | --- | --- |
| Auth, sesje, reset i odwołanie | <!-- dotyczy/N/A --> | <!-- PASS/FAIL/BLOCKED/N/A --> | <!-- przegląd kodu/test/NOT RUN --> | | | |
| Role, IDOR, izolacja danych | | | | | | |
| Origin/CSRF | | | | | | |
| CORS, allowlista i preflight | | | | | | |
| Walidacja, negatywne 401/403/409/422 | | | | | | |
| Cookie (Secure, HttpOnly, SameSite, prefiks) i timeout sesji | | | | | | |
| Inne właściwe kontrole ASVS | | | | | | |

Dopisz konkretne identyfikatory ASVS do właściwych scenariuszy.
Ujawnij otwarte FAIL/BLOCKED, powiązane zgłoszenia i decyzje o ryzyku.
Niezależny reviewer potwierdza adekwatność testów i wyjątków; brak
dowodu pozostaje BLOCKED. N/A nie znosi obowiązkowego CI.

### Migracje i odtwarzanie

**Migracja (ID, środowisko, data, wykonawca) / N/A z uzasadnieniem:**

**Wynik migracji (PASS/FAIL/BLOCKED/N/A, link do dowodu, SHA, data, wykonawca; N/A wymaga uzasadnienia):**

**Plan powrotu do poprzedniej wersji (kroki, warunki uruchomienia, właściciel) / N/A z uzasadnieniem:**

**Wpływ migracji i rollbacku na istniejące dane (utrata, nieodwracalność, zgodność schematu) / N/A z uzasadnieniem:**

**Wynik próby restore/rollback (link, SHA, data, wykonawca) / BLOCKED / N/A z uzasadnieniem:**

**Ograniczenia rollbacku, ryzyko, właściciel decyzji i link do zatwierdzenia PO w Jira, jeśli wymagane:**

### Odbiór

**Niezależny reviewer:**

**Wymagane CI:** <!-- odnieś się do tabeli obowiązkowych bram powyżej -->

**QA przed merge, jeśli wymagane:**

**Osobne QA sprintu / wdrożenia, jeśli dotyczy:**

Nie deklarujemy pełnej zgodności ASVS L2 na podstawie
wybranych kontroli ani samego zaznaczenia checklisty.
