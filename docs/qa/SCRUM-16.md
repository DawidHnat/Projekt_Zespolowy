# SCRUM-16 / SCRUM-56 — pakiet końcowego odbioru logowania

**Stan: przygotowane do niezależnego QA i review developera. Nie jest pełnym Done.**

Zadania: [SCRUM-16](https://fleet-flow.atlassian.net/browse/SCRUM-16),
[SCRUM-56](https://fleet-flow.atlassian.net/browse/SCRUM-56).
Wykonawca poniższych sprawdzeń: agent na polecenie Jakuba Czai.
Nie przypisujemy ich Marcelowi ani drugiemu developerowi.

## Wersja i warunki

- Odbiór techniczny: 06.11.2026 23:41 CET; kod przypięty do `5b5fcebebb8bcf980a555ccdd4a4b66425c35ed5`.
- Produkcja: https://fleet-flow.pl/; HTTP po IP potwierdził `5b5fceb`,
  zgodne z pobranym `origin/main`; `/api/health/ready` zwróciło `ok`.
- Istniejące konto zespołu QA, rola viewer; dane dostępowe poza Git.
  Nie zmieniono hasła, kont ani danych floty. Utworzone przez test sesje wylogowano.
- Chromium w przeglądarce aplikacji: 1440 × 1000 i viewport 390 × 844.
- Nie uruchamiano synchronizacji, testów żywego WEBFLEET ani SMTP.
  Testy używają normalnych endpointów logowania, własnych sesji i odmów dostępu.
- Kod auth i jego testy nie różnią się od wcześniejszego retestu `4ce144e`;
  wyników starej wersji nie przepisano jako nowych testów bieżącej wersji.

## Wykonane sprawdzenia

| Sprawdzenie bieżącej wersji | Wynik i dowód |
| --- | --- |
| HTTPS / API logowania i odmowy dostępu | 18/18 PASS; lista poniżej. |
| UI logowania i sesji | 9/9 PASS; lista poniżej. |
| Frontend lokalnie | `npm test`: 50/50 PASS, bez pominięć; `npm run build`: PASS. |
| Backend lokalnie | Ruff check i format: PASS, 46 plików. Lokalny pełny PostgreSQL nie został uruchomiony — Docker był wyłączony. Dodatkowy lokalny pytest bez PostgreSQL przerwano; nie jest raportowany jako pełny PASS. |
| Backend w CI z PostgreSQL 17 | 131/131 PASS bez pominięć na Pythonie 3.12 i 3.13, Ruff i format PASS. |
| E2E w CI | 26/26 PASS. |
| Wdrożenie testowanej wersji | Required CI i Deploy development server: SUCCESS. |

[CI i wdrożenie dokładnie tego SHA](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/42302297975).
Obecne ostrzeżenie o wielkości paczki Mapbox nie zatrzymuje budowy.

### HTTPS — wykonano 18 kontroli

1. `/auth/me` bez sesji: 401.
2. `/fleet/vehicles` bez sesji: 401.
3. `/fleet/map` bez sesji: 401.
4. Próba zapisu adnotacji bez sesji: 401; użyto nieistniejącego syntetycznego UUID.
5. Login z obcym Origin: 403.
6. Niepoprawne hasło: 401.
7. Nieistniejący login: taki sam neutralny błąd jak dla złego hasła.
8. Poprawne logowanie przez docelowy HTTPS: 200.
9. Konto testowe zachowało rolę viewer.
10. Cookie sesji: Secure, HttpOnly, SameSite=Strict.
11. Aktywna sesja `/auth/me`: 200.
12. Kolejne żądanie w tej sesji: 200.
13. Logout z obcym Origin: 403.
14. Odrzucony logout nie unieważnił prawidłowej sesji.
15. Prawidłowy logout: 200.
16. Ponowne użycie unieważnionego cookie do `/auth/me`: 401.
17. Ponowne użycie tego cookie do API floty: 401.
18. Ponowne logowanie: 200; na końcu wylogowano sesję testową.

### UI — wykonano 9 sprawdzeń

- Błędne hasło daje ogólny komunikat „Niepoprawny login lub hasło.”.
- Poprawne dane otwierają Pulpit na komputerze.
- Odświeżenie strony zachowuje sesję.
- Wylogowanie przywraca formularz logowania na komputerze.
- Poprawne dane otwierają Pulpit w viewporcie telefonu.
- Menu telefonu umożliwia wylogowanie; wraca formularz logowania.
- Odświeżenie po logout nadal wymaga zalogowania.
- Formularz na szerokości 390 px nie rozpycha strony: scrollWidth=clientWidth=390.
- Dwie karty współdzielą sesję; po logout w pierwszej odświeżenie drugiej
  pokazuje login i usuwa Pulpit. Nie deklarujemy natychmiastowego usunięcia cache bez żądania.

## Kryteria historyjki i pozostały odbiór

| Kryterium SCRUM-16 | Zebrany dowód | Co potwierdza QA |
| --- | --- | --- |
| AC1: bez sesji brak odczytu/zapisu UI i API | HTTPS 1–4, 16–17; UI po logout i reload. | Powtórzyć wejście bez sesji i brak dostępu po logout. |
| AC2: aktywne konto otwiera Pulpit, błędy są neutralne | HTTPS 6–9; UI złe i dobre dane na obu szerokościach. | Potwierdzić ten sam wynik na uzgodnionym koncie QA. |
| AC3: logout unieważnia sesję, wygaśnięcie żąda logowania | HTTPS 13–18; UI logout/reload; bieżący test backendu `test_expired_and_disabled_accounts` i E2E invalidated session są zielone. | FF-QA-030 potwierdzono po odświeżeniu drugiej karty. Dokończyć FF-QA-031: UI z krótką sesją w izolacji, przy następnym żądaniu. Nie oznaczamy tego jako ręczny test wygaśnięcia sesji produkcyjnej. |
| AC4: HTTPS, Secure/HttpOnly, hash haseł i brak sekretów w Git | HTTPS 8/10; `test_login_opaque_session_and_logout` sprawdza Argon2id i hash tokenu; backend/CI PASS. | Developer przegląda przypięty kod auth i konfigurację cookies; dane dostępowe pozostają poza Git. |

Odwołania do planu QA: FF-QA-011 oraz FF-QA-028–034
w [TEST_CASES.md](TEST_CASES.md). Reset i dostawa SMTP pozostają osobno
w SCRUM-44; nie blokują węższego zakresu przyjętego w opisie SCRUM-16.

## Czynności dla Marcela — końcowa próba i zapis

1. Uzgodnić wersję: jeśli main/produkcja zmieniły SHA, zapisać nowe SHA i ocenić,
   czy zmiana dotyczy auth; nie podpisywać innego wydania bez sprawdzenia.
2. Na koncie QA powtórzyć: wejście bez sesji, błędny login, poprawny login,
   odświeżenie, logout i odmowę API po logout.
3. W dwóch kartach tej samej sesji wykonać logout w pierwszej, a w drugiej
   wywołać odczyt/odświeżenie. Stara zawartość może pozostawać do następnego
   żądania; zapisać, czy po 401 UI przechodzi do logowania i usuwa dane.
4. Wygaśnięcie testować w izolowanym środowisku z syntetycznym kontem i krótką
   sesją albo kontrolowanym wygaśnięciem wyłącznie testowej sesji.
   Nie zmieniać zegara serwera ani wspólnych sesji na produkcji.
5. W SCRUM-56 zapisać: wykonawca, data, SHA, środowisko/przeglądarka,
   ID przypadków, oczekiwany/rzeczywisty wynik i PASS/FAIL/BLOCKED.
   Błąd oznacza zgłoszenie i retest; nie samo przestawienie statusu.

## Czynności dla developera i bramka Done

**Otwarty warunek:** [PR #10](https://github.com/DawidHnat/Projekt_Zespolowy/pull/10) jest scalony, lecz w odczycie
06.11.2026 nie miał niezależnego Approved. Ten raport nie dopisuje go wstecz.
Dawid lub inny developer ma przejrzeć obecną implementację na przypiętym SHA
oraz zapisać, co rzeczywiście sprawdził. Samo Approved dokumentacji nie jest
automatycznie przeglądem kodu auth ani naprawą historycznego braku w #10.

Do przeglądu kodu na testowanej wersji:

- [backend auth router](https://github.com/DawidHnat/Projekt_Zespolowy/blob/5b5fcebebb8bcf980a555ccdd4a4b66425c35ed5/backend/app/modules/auth/router.py),
  [service](https://github.com/DawidHnat/Projekt_Zespolowy/blob/5b5fcebebb8bcf980a555ccdd4a4b66425c35ed5/backend/app/modules/auth/service.py),
  [models](https://github.com/DawidHnat/Projekt_Zespolowy/blob/5b5fcebebb8bcf980a555ccdd4a4b66425c35ed5/backend/app/modules/auth/models.py).
- [AuthGate](https://github.com/DawidHnat/Projekt_Zespolowy/blob/5b5fcebebb8bcf980a555ccdd4a4b66425c35ed5/frontend/src/features/auth/AuthGate.tsx),
  [AuthProvider](https://github.com/DawidHnat/Projekt_Zespolowy/blob/5b5fcebebb8bcf980a555ccdd4a4b66425c35ed5/frontend/src/features/auth/AuthProvider.tsx),
  [klient API](https://github.com/DawidHnat/Projekt_Zespolowy/blob/5b5fcebebb8bcf980a555ccdd4a4b66425c35ed5/frontend/src/shared/api/client.ts).
- [Testy auth](https://github.com/DawidHnat/Projekt_Zespolowy/blob/5b5fcebebb8bcf980a555ccdd4a4b66425c35ed5/backend/tests/test_auth.py).

Przed pełnym Done należy odnieść dowody do całego
[DEFINITION_OF_DONE.md](../../DEFINITION_OF_DONE.md): niezależny odbiór,
review implementacji, aktualne CI/wersja, dokumentacja i odpowiedni dowód
odtworzenia dla zmian schematu/wdrożenia. CI sprawdza pełny cykl migracji
upgrade/check/downgrade/upgrade; nie opisujemy go jako odtworzenia produkcyjnego backupu.

Status rodzica Gotowe był wcześniej ustawiony administracyjnie. Publikacja
tego pakietu nie zmienia tego w techniczne potwierdzenie wszystkich warunków.

Do wpisania po faktycznym sprawdzeniu:

- QA: wykonawca, data, SHA, przypadki i wynik — **oczekuje**.
- Developer: zakres review implementacji, wynik i odnośnik — **oczekuje**.
- PO: akceptacja całej Story na podstawie kompletnych dowodów — **oczekuje**.
