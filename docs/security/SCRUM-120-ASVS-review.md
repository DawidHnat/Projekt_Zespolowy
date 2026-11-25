# SCRUM-120 — przegląd OWASP ASVS 5.0.0 L2

## Zakres i zasady

Przyrost dokumentacyjny wydzielono jako
[SCRUM-179](https://fleet-flow.atlassian.net/browse/SCRUM-179)
zgodnie z zasadą
[SCRUM-151](https://fleet-flow.atlassian.net/browse/SCRUM-151).

Scalenie tego przyrostu nie kończy SCRUM-120.
Pełne retesty, decyzje dotyczące ryzyka i niezależny
odbiór ASVS L2 pozostają w zakresie SCRUM-120.

Źródło wymagań:
[OWASP ASVS 5.0.0](https://github.com/OWASP/ASVS/tree/v5.0.0/5.0/en).


Przegląd auth/session/access/data Fleet-Flow.
Dokument uzupełnia częściową macierz SCRUM-101.
ASVS L2 obejmuje właściwe wymagania L1 i L2.

Stan: CODE REVIEW / DO POTWIERDZENIA.
Nie jest to certyfikacja ASVS L2.
Nie wykonano nowych testów bezpieczeństwa.

Wersja kodu do przeglądu: 06bae19e6717870b63c184a8c14a5c3d3b4b7525
Środowisko: repozytorium GitHub / kod źródłowy.
Testy na tej wersji: NOT RUN.

## Macierz ustaleń

Wersja źródeł: `06bae19e6717870b63c184a8c14a5c3d3b4b7525`.
Rodzaj dowodu: **przegląd kodu**, nie uruchomienie testu.
Linki wskazują pliki na dokładnym SHA. Nazwy symboli
w opisach identyfikują kontrolowane fragmenty.

Każdy BLOCKED oznacza brak wymaganej decyzji, kompletnego
zakresu lub dowodu testowego. FAIL z przeglądu kodu
nie jest automatycznie dowodem skutecznego ataku.

| ASVS v5.0.0 | Obszar | Dowód i uzasadnienie | Stan |
| --- | --- | --- | --- |
| v5.0.0-6.4.3 | Reset hasła | [confirm_reset](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/reset.py); [test_password_reset.py](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/tests/test_password_reset.py). Kod unieważnia tokeny i sesje; brak osobnego retestu QA na wskazanym SHA. | BLOCKED — test NOT RUN |
| v5.0.0-7.1.1 | Polityka sesji | [Settings.session_hours](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/core/settings.py) = 12 godzin domyślnie. To ustawienie kodu, nie zatwierdzona polityka ani dowód limitu bezczynności. | BLOCKED — decyzja PO |
| v5.0.0-7.1.2 | Sesje równoległe | [issue_session](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/service.py); brak zatwierdzonej reguły liczby sesji i testu współbieżności. | BLOCKED — polityka |
| v5.0.0-7.3.1 | Limit bezczynności | [current_user](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/service.py) sprawdza expires_at; odrębny idle timeout nie jest potwierdzony. | BLOCKED — brak dowodu |
| v5.0.0-7.3.2 | Limit absolutny | [issue_session/current_user](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/service.py): expires_at jest zapisywane i sprawdzane. Brak osobnego retestu wygaśnięcia na SHA. | BLOCKED — test NOT RUN |
| v5.0.0-7.4.1 | Logout i odwołanie | [logout](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/router.py); [logout_all](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/profile.py); istnieje usuwanie sesji, ale brak zapisanego niezależnego wyniku 401 po logout na SHA. | BLOCKED — test NOT RUN |
| v5.0.0-7.4.3 | Sesje po zmianie/resetowaniu hasła | [change_password](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/profile.py) oraz [confirm_reset](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/reset.py) wywołują revoke_sessions; potrzebny retest starych sesji po zmianie i resecie. | BLOCKED — test NOT RUN |
| v5.0.0-8.1.1 | Polityka ról | [auth/policies.py](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/policies.py); admin/editor/viewer są obsługiwani, ale kompletna macierz decyzji dla endpointów nie jest odebrana. | BLOCKED — zakres |
| v5.0.0-8.2.1 | Kontrola autoryzacji | [update_vehicle_card](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/fleet/router.py); [write_preference](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/preferences/router.py); wymagany test dostępu do istniejącego syntetycznego obiektu. | BLOCKED — QA |
| v5.0.0-8.2.2 | IDOR i izolacja | [fleet/router.py](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/fleet/router.py); [AccountPreference/user.id](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/preferences/router.py); brak pełnego testu dwóch syntetycznych kont i obcych zasobów. | BLOCKED — QA |
| v5.0.0-8.3.1 | Autoryzacja backendu | [editor/current_user](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/service.py); [test_scrum101_roles.py](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/tests/test_scrum101_roles.py); testy nieistniejącego UUID nie dowodzą odmowy na istniejącym obiekcie. | BLOCKED — QA |
| v5.0.0-3.3.1 | Cookie Secure i prefiks nazwy | [COOKIE_NAME/issue_session](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/service.py); `COOKIE_NAME = fleet_flow_session` nie ma prefiksu `__Host-` ani `__Secure-`, wymaganego przez ASVS 3.3.1. Atrybut Secure zależy od konfiguracji; weryfikacja Set-Cookie na docelowym HTTPS: BLOCKED. | FAIL — przegląd kodu; Secure HTTPS BLOCKED |
| v5.0.0-3.3.2 | SameSite | [issue_session](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/service.py): samesite=strict w kodzie; brak testu nagłówka na wdrożeniu. | BLOCKED — HTTPS |
| v5.0.0-3.3.3 | Cookie i prefiks hosta | [COOKIE_NAME](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/service.py) = fleet_flow_session, bez prefiksu __Host-; do triage z PO. | FAIL — przegląd kodu |
| v5.0.0-3.3.4 | HttpOnly | [issue_session](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/service.py): httponly=True; brak dowodu Set-Cookie na wdrożeniu. | BLOCKED — HTTPS |
| v5.0.0-3.4.2 | CORS | [create_app/CORSMiddleware](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/main.py): allow_origins=settings.origins; test preflight i nagłówków nieudokumentowany. | BLOCKED — test NOT RUN |
| v5.0.0-3.5.1 | Origin/CSRF | [check_origin](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/auth/service.py); [write_preference](https://github.com/DawidHnat/Projekt_Zespolowy/blob/06bae19e6717870b63c184a8c14a5c3d3b4b7525/backend/app/modules/preferences/router.py): Depends(check_origin) na zapisie. Ocena zastosowania: aplikacja korzysta z cookies i weryfikuje Origin; brak pełnego testu żądań z obcym/brakującym Origin. | BLOCKED — test NOT RUN |

Oceny odnoszą się tylko do wymienionych kontroli.
Origin/CSRF `3.5.1` i CORS `3.4.2` mają osobne wiersze;
zastosowanie `3.5.2` wymaga osobnej oceny mechanizmu
z niezależnym reviewerem według oficjalnej ASVS 5.0.0.
Pełnego pokrycia L1+L2 nie potwierdzono.

### Historia usterek i retesty

| Jira | Powiązany obszar | Stan bieżący i wymagany retest |
| --- | --- | --- |
| [SCRUM-144](https://fleet-flow.atlassian.net/browse/SCRUM-144) | 8.2.2 — izolacja kont i danych | Jira: Gotowe. Historycznie układ A przenosił się na B. Niezależny retest QA A→B na aktualnym SHA i syntetycznych kontach: NOT RUN; nie przypisywać PASS. |
| [SCRUM-145](https://fleet-flow.atlassian.net/browse/SCRUM-145) | 3.5.1 — Origin/CSRF | Jira: Gotowe. Aktualny kod write_preference zawiera check_origin; retest braku i obcego Origin + brak zmiany wersji: NOT RUN. |
| [SCRUM-146](https://fleet-flow.atlassian.net/browse/SCRUM-146) | 2.2.1/2.2.2 — walidacja danych | Jira: Gotowe. Obecna _bounded_number rozdziela int i float; retest skrajnych liczb i HTTP 422 bez zapisu: NOT RUN. |

Pozostałe obszary wymagają triage:
- 7.1.1–7.3.1: polityka czasu bezczynności i sesji — decyzja PO;
- 3.3.1–3.3.4: prefiks cookie i rzeczywisty HTTPS Set-Cookie — triage PO/security reviewer;
- 8.1.1–8.3.1: pełna autoryzacja i IDOR — zakres testów do uzgodnienia z QA;
- 3.4.2 i 3.5.1: osobne próby CORS/preflight oraz Origin/CSRF;
- 6.4.3 i 7.4.3: reset hasła i unieważnianie poprzednich sesji.

Brak osobnych zgłoszeń dla części luk oznacza otwarty
triage, a nie potwierdzoną naprawę lub akceptację ryzyka.

### Ewidencja QA i decyzji

- Data przeglądu kodu: 2026-11-24 (dowód w SCRUM-120).
- SHA kodu: `06bae19e6717870b63c184a8c14a5c3d3b4b7525`.
- Środowisko: GitHub, statyczny odczyt kodu źródłowego.
- Przegląd: agent ChatGPT na polecenie Marcela;
  nie jest to niezależny odbiór człowieka.
- Dowód: [komentarze SCRUM-120](https://fleet-flow.atlassian.net/browse/SCRUM-120).
- Ręczne QA zabezpieczeń na tym SHA: **NOT RUN**.
- CI dokumentacyjnego PR #169: osobny dowód automatyczny,
  nie zastępuje retestów auth/role/CSRF.
- Wynik odbioru: **BLOCKED** do wykonania testów,
  uzupełnienia macierzy i niezależnego review.
- Osoba zatwierdzająca ryzyka wysokie/krytyczne: PO;
  decyzja i uzasadnienie muszą trafić do Jira.
- Nie scalać częściowego PR pod kluczem SCRUM-120,
  jeśli miałoby to automatycznie zamknąć całe zadanie;
  wydzielony przyrost wymaga nowego klucza i decyzji PO.

## Wyniki CI — f2ac17f (25.11.2026)

- PR: https://github.com/DawidHnat/Projekt_Zespolowy/pull/169
- Head PR: `f2ac17f1aa8d287faa9b7498d8f6c03cee7850ff`.
- Kod bazowy analizowany w macierzy: `06bae19e6717870b63c184a8c14a5c3d3b4b7525`.
- Dowód: https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/45684810547
- Required CI: **SUCCESS**.
- Backend Python 3.13: **317 PASS, 1 SKIP**.
- Backend Python 3.12: **317 PASS, 1 SKIP**.
- Playwright desktop/mobile: **174 PASS, 4 SKIP**.
- Środowisko: GitHub Actions, ubuntu-latest, PostgreSQL 17,
  izolowane bazy `fleet_flow_test` i `fleet_flow_test_e2e`.
- Dane: syntetyczne, bez produkcyjnych integracji.
- Rodzaj dowodu: automatyczna regresja CI.

Dodatkowy dowód historyczny:
- PR #169, head `dc495d924354f824f7727cf110bc5ba04b5662ce`.
- Required CI: **SUCCESS**.
- [Przebieg CI](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/45687535665).
- Wynik dotyczy wskazanego historycznego SHA, nie nowego PR.

### Pokrycie i ograniczenia

Automatyczny zestaw obejmuje m.in.:
- `test_auth.py`: Origin, cookie, logout i wygaśnięcie sesji;
- `test_profile.py`: zmianę hasła, odwoływanie sesji
  oraz odmowę operacji z obcym Origin;
- `test_password_reset.py`: jednorazowość resetu hasła
  i odwoływanie poprzednich sesji;
- `test_scrum101_roles.py`: kontrolę ról przy edycji pojazdu.

Zielone CI potwierdza przebieg istniejących testów.
Nie potwierdza kompletnego pokrycia ASVS L2.

Nadal **BLOCKED / NOT RUN** jako niezależne QA:
- admin/editor/viewer na istniejącym syntetycznym pojeździe;
- izolacja dwóch kont i IDOR;
- przekrojowy Origin/CSRF oraz CORS/preflight;
- atrybuty Set-Cookie na docelowym HTTPS;
- udokumentowane retesty SCRUM-144, 145 i 146
  z expected/actual, SHA i środowiskiem.

Wyniki automatyczne nie są podpisem niezależnego
manualnego QA. Decyzja PO o ryzykach, pełnym zakresie
SCRUM-120 i ewentualnym wydzieleniu przyrostu
pozostaje otwarta. Nie scalać PR pod kluczem SCRUM-120,
jeżeli spowodowałoby to przedwczesne zamknięcie zadania.

## Testy do wykonania

- [ ] Logowanie: poprawne i niepoprawne dane.
- [ ] Logout: token odwołany zwraca 401.
- [ ] Expiry: wygasła sesja zwraca 401.
- [ ] Reset hasła: jednorazowość i odwołanie sesji.
- [ ] Role: admin/editor/viewer na istniejącym obiekcie.
- [ ] IDOR: izolacja danych dwóch syntetycznych kont.
- [ ] Origin/CSRF: brakujący i obcy Origin.
- [ ] CORS: osobny test allowlisty i preflight.
- [ ] Cookie: rzeczywiste atrybuty Set-Cookie.
- [ ] Walidacja: 401/403/409/422 i brak 500.
- [ ] Retesty zgłoszeń SCRUM-144, 145 i 146.

Każdy wynik testu wymaga: daty, wykonawcy,
scenariusza, SHA, środowiska i dowodu.

## Decyzje i blokady

1. PO/security reviewer: polityka idle timeout.
2. PO/security reviewer: bezpieczny prefiks cookie.
3. PO: zasady i limit równoległych sesji.
4. Reviewer: kompletność zakresu L1/L2 i wyjątków.
5. QA: retesty na syntetycznych danych i konkretnym SHA.
6. CI i niezależny review przed merge.

Otwarte FAIL i BLOCKED nie oznaczają PASS.
Nie używać rzeczywistych kont, danych floty,
produkcyjnego WEBFLEET ani SMTP do tych prób.
