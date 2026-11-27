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

Stan pełnego odbioru ASVS L2: **BLOCKED**.

- Przegląd kodu: `cd321eb2a34151d88d556753c2269b01fd6524a9`, GitHub, 27.11.2026. Niezależny przegląd statyczny wykonał Dawid Hnat. [Uwagi Dawida](https://fleet-flow.atlassian.net/browse/SCRUM-120?focusedCommentId=10554).
- Wykonane próby QA: `17ea095772e442c42f77745621defc572573a71e`, 27.11.2026. Wyniki i środowiska są podane w sekcji ewidencji QA. Próby nie były powtarzane na SHA przeglądu kodu.

## Macierz ustaleń

Wersja źródeł: `cd321eb2a34151d88d556753c2269b01fd6524a9`.
Rodzaj dowodu: **przegląd kodu**, nie uruchomienie testu.
Linki wskazują pliki na dokładnym SHA. Nazwy symboli
w opisach identyfikują kontrolowane fragmenty.

BLOCKED wskazuje brak decyzji, kompletnego zakresu lub dowodu testowego dla danej kontroli. FAIL z przeglądu kodu
nie jest automatycznie dowodem skutecznego ataku.

| ASVS v5.0.0 | Obszar | Dowód i uzasadnienie | Stan |
| --- | --- | --- | --- |
| v5.0.0-6.4.3 | Reset hasła | [confirm_reset](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/reset.py); [test_password_reset.py](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/tests/test_password_reset.py). Kod unieważnia tokeny i sesje; brak osobnego retestu QA na wskazanym SHA. | BLOCKED — test NOT RUN |
| v5.0.0-7.1.1 | Polityka sesji | [Settings.session_hours](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/core/settings.py) = 12 godzin domyślnie. To ustawienie kodu, nie zatwierdzona polityka ani dowód limitu bezczynności. | BLOCKED — decyzja PO |
| v5.0.0-7.1.2 | Sesje równoległe | [issue_session](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/service.py); brak zatwierdzonej reguły liczby sesji i testu współbieżności. | BLOCKED — polityka |
| v5.0.0-7.3.1 | Limit bezczynności | [current_user](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/service.py) sprawdza expires_at; odrębny idle timeout nie jest potwierdzony. | BLOCKED — brak dowodu |
| v5.0.0-7.3.2 | Limit absolutny | [issue_session/current_user](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/service.py): expires_at jest zapisywane i sprawdzane. Brak osobnego retestu wygaśnięcia na SHA. | BLOCKED — test NOT RUN |
| v5.0.0-7.4.1 | Logout i odwołanie | [logout](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/router.py); [logout_all](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/profile.py); istnieje usuwanie sesji, ale brak zapisanego niezależnego wyniku 401 po logout na SHA. | BLOCKED — test NOT RUN |
| v5.0.0-7.4.3 | Sesje po zmianie/resetowaniu hasła | [change_password](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/profile.py) oraz [confirm_reset](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/reset.py) wywołują revoke_sessions; potrzebny retest starych sesji po zmianie i resecie. | BLOCKED — test NOT RUN |
| v5.0.0-8.1.1 | Polityka ról | [auth/policies.py](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/policies.py); admin/editor/viewer są obsługiwani, ale kompletna macierz decyzji dla endpointów nie jest odebrana. | BLOCKED — zakres |
| v5.0.0-8.2.1 | Kontrola autoryzacji | [update_vehicle_card](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/fleet/router.py); [write_preference](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/preferences/router.py); wymagany test dostępu do istniejącego syntetycznego obiektu. | BLOCKED — QA |
| v5.0.0-8.2.2 | IDOR i izolacja | [fleet/router.py](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/fleet/router.py); [AccountPreference/user.id](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/preferences/router.py); brak pełnego testu dwóch syntetycznych kont i obcych zasobów. | BLOCKED — QA |
| v5.0.0-8.3.1 | Autoryzacja backendu | [editor/current_user](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/service.py); [test_scrum101_roles.py](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/tests/test_scrum101_roles.py); testy nieistniejącego UUID nie dowodzą odmowy na istniejącym obiekcie. | BLOCKED — QA |
| v5.0.0-3.3.1 | Cookie Secure i prefiks nazwy | [COOKIE_NAME/issue_session](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/service.py); `COOKIE_NAME = fleet_flow_session` nie ma prefiksu `__Host-` ani `__Secure-`, wymaganego przez ASVS 3.3.1. Atrybut Secure zależy od konfiguracji; weryfikacja Set-Cookie na docelowym HTTPS: BLOCKED. | FAIL — przegląd kodu; Secure HTTPS BLOCKED |
| v5.0.0-3.3.2 | SameSite | [issue_session](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/service.py): samesite=strict w kodzie; brak testu nagłówka na wdrożeniu. | BLOCKED — HTTPS |
| v5.0.0-3.3.3 | Cookie i prefiks hosta | [COOKIE_NAME](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/service.py) = fleet_flow_session, bez prefiksu __Host-; do triage z PO. | FAIL — przegląd kodu |
| v5.0.0-3.3.4 | HttpOnly | [issue_session](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/service.py): httponly=True; brak dowodu Set-Cookie na wdrożeniu. | BLOCKED — HTTPS |
| v5.0.0-3.4.2 | CORS | [create_app/CORSMiddleware](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/main.py): allow_origins=settings.origins; preflight na `17ea095` PASS w middleware. | BLOCKED — docelowy HTTPS |
| v5.0.0-3.5.1 | Origin/CSRF | [check_origin](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/service.py); [write_preference](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/preferences/router.py): Depends(check_origin) na zapisie. Ocena zastosowania: aplikacja korzysta z cookies i weryfikuje Origin; retest preferencji na `17ea095` PASS, pozostałe operacje wymagają potwierdzenia. | BLOCKED — test NOT RUN |

Oceny odnoszą się tylko do wymienionych kontroli.
Origin/CSRF `3.5.1` i CORS `3.4.2` mają osobne wiersze;
zastosowanie `3.5.2` wymaga osobnej oceny mechanizmu
z niezależnym reviewerem według oficjalnej ASVS 5.0.0.
Pełnego pokrycia L1+L2 nie potwierdzono.

### Ochrona danych

[OWASP ASVS 5.0.0, V14](https://github.com/OWASP/ASVS/blob/v5.0.0/5.0/en/0x23-V14-Data-Protection.md).

| ASVS v5.0.0 | Obszar | Dowód i uzasadnienie | Stan |
| --- | --- | --- | --- |
| v5.0.0-14.1.1 | Klasyfikacja danych | [Model danych](../DATA_MODEL.md) identyfikuje m.in. dane kierowców, pojazdów i przejazdów. Do klasyfikacji trzeba włączyć też dane kont i sesji, preferencje oraz kopie i logi zawierające dane chronione. Brak kompletnego wykazu poziomów ochrony i właścicieli klas. | BLOCKED — inwentaryzacja i zatwierdzenie klas |
| v5.0.0-14.1.2 | Wymagania dla klas danych | Dla każdej klasy potrzebna jest udokumentowana polityka poufności, szyfrowania i integralności, retencji, logowania, dostępu do logów oraz ochrony bazy i kopii. Model danych opisuje własność, a [SCRUM-113](https://fleet-flow.atlassian.net/browse/SCRUM-113) śledzi ustalenia dotyczące użycia danych. Brak spójnej macierzy wymagań według klas. | BLOCKED — wymagania i decyzja PO |
| v5.0.0-14.2.1 | Ochrona danych w żądaniach | Potrzebny przekrojowy przegląd adresów URL i logów pod kątem klas danych oraz test, że sekrety sesji pozostają w nagłówkach lub treści żądania. | BLOCKED — zakres i dowód |
| v5.0.0-14.2.4 | Wdrożenie ochrony według klasy | [Serwis sesji](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/auth/service.py) zapisuje skrót tokenu, a [preferencje](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cd321eb2a34151d88d556753c2269b01fd6524a9/backend/app/modules/preferences/router.py) wiążą operacje z kontem. To dowody wybranych mechanizmów. Do odbioru pozostaje powiązanie każdej klasy z ochroną w kodzie, na wdrożeniu, w logach, bazie i kopiach oraz dowód retencji. | BLOCKED — wymagania 14.1.1/14.1.2 i testy |

### Historia usterek i retesty

| Jira | Powiązany obszar | Stan bieżący i wymagany retest |
| --- | --- | --- |
| [SCRUM-144](https://fleet-flow.atlassian.net/browse/SCRUM-144) | 8.2.2 — izolacja kont i danych | PASS E2E desktop/mobile na `17ea095`: konto B zachowało własny lub domyślny układ. Dowód niżej. |
| [SCRUM-145](https://fleet-flow.atlassian.net/browse/SCRUM-145) | 3.5.1 — Origin/CSRF | PASS na `17ea095`: obcy lub brakujący Origin daje 403 bez zmiany danych, dozwolony Origin zapisuje. Dowód niżej. |
| [SCRUM-146](https://fleet-flow.atlassian.net/browse/SCRUM-146) | 2.2.1/2.2.2 — walidacja danych | PASS na `17ea095`: skrajne wymiary dają 422 bez zapisu. Dowód niżej. |

Pozostałe obszary wymagają triage:
- 7.1.1–7.3.1: polityka czasu bezczynności i sesji — decyzja PO;
- 3.3.1–3.3.4: prefiks cookie i rzeczywisty HTTPS Set-Cookie — triage PO/security reviewer;
- 8.1.1–8.3.1: pełna autoryzacja i IDOR — zakres testów do uzgodnienia z QA;
- 3.4.2 i 3.5.1: osobne próby CORS/preflight oraz Origin/CSRF;
- 6.4.3 i 7.4.3: reset hasła i unieważnianie poprzednich sesji.

Brak osobnych zgłoszeń dla części luk oznacza otwarty
triage, a nie potwierdzoną naprawę lub akceptację ryzyka.

### Ewidencja QA i decyzji

Wykonanie 27.11.2026 na `17ea095772e442c42f77745621defc572573a71e`. Dane syntetyczne. Wyniki poniżej odzwierciedlają sprawdzone przypadki.

| Kontrola | Wykonawca i środowisko | Oczekiwany i faktyczny wynik | Dowód |
| --- | --- | --- | --- |
| 8.1.1, 8.2.1, 8.3.1 — role | Marcel Głowacki, Windows, izolowany PostgreSQL i Chromium | Viewer odczytuje kartę, zapis jest niedostępny. PASS dla sprawdzonych operacji. | [QA backendu](https://fleet-flow.atlassian.net/browse/SCRUM-120?focusedCommentId=10541), [odbiór viewer](https://fleet-flow.atlassian.net/browse/SCRUM-54?focusedCommentId=10552) |
| 8.2.2 — SCRUM-144 | Runner GitHub Actions, Chromium desktop/mobile i izolowany PostgreSQL | Po zmianie konta preferencje A nie przechodzą na B. PASS. | [E2E](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/46011237932/job/140547129111) |
| 3.5.1 i 2.2.1/2.2.2 — SCRUM-145/146 | Marcel Głowacki, Windows, lokalne testy backendu | Oczekiwano 403 bez mutacji dla obcego/brakującego Origin oraz 422 bez zapisu dla skrajnych wymiarów. PASS. | [30/30 lokalnie](https://fleet-flow.atlassian.net/browse/SCRUM-120?focusedCommentId=10541) |
| 3.4.2 — CORS | Codex dla Marcela, Windows, skonfigurowany middleware ASGI | Dozwolony origin 200 z nagłówkiem zezwalającym, obcy 400 bez tego nagłówka. Faktycznie zgodnie z oczekiwaniem, 2/2 PASS. | [Preflight](https://fleet-flow.atlassian.net/browse/SCRUM-120?focusedCommentId=10549) |
| 3.3.1–3.3.4 — cookie | Dawid Hnat, statyczny przegląd SHA źródeł podanego na początku dokumentu | Wymagany dowód docelowego HTTPS. Brak prefiksu pozostaje FAIL w kodzie dla 3.3.1/3.3.3. Atrybuty na docelowym HTTPS pozostają BLOCKED. | [Przegląd Dawida](https://fleet-flow.atlassian.net/browse/SCRUM-120?focusedCommentId=10554) |

Pełna macierz endpointów, izolacja wszystkich właściwych zasobów, dowód nagłówka na wdrożeniu oraz kontrole ochrony danych pozostają otwarte. Decyzje o ryzyku zapisuje PO. Przyrost dokumentacyjny wymaga odrębnego klucza przed scaleniem, jeśli scalenie pod SCRUM-120 zamknęłoby pełny zakres.

## Historyczne wyniki CI — f2ac17f (25.11.2026)

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
- przekrojowy Origin/CSRF oraz CORS na docelowym HTTPS;
- atrybuty Set-Cookie na docelowym HTTPS;
- retesty SCRUM-144–146 na docelowym wdrożeniu, jeżeli wymagane w odbiorze. Próby automatyczne i lokalne są zapisane powyżej.

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
- [x] CORS: lokalny test allowlisty i preflight na middleware.
- [ ] CORS: potwierdzenie na docelowym HTTPS.
- [ ] Cookie: rzeczywiste atrybuty Set-Cookie.
- [ ] Walidacja: 401/403/409/422 i brak 500.
- [x] Retesty SCRUM-144, 145 i 146 w udokumentowanym zakresie CI i lokalnego backendu.

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
