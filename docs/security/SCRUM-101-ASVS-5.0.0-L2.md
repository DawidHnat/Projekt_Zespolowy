# SCRUM-101 — wybrana macierz OWASP ASVS 5.0.0 L2 dla Fleet-Flow

**Stan dowodów:** 17.11.2026, przegląd repozytorium `main` na SHA `9dad2b2a953dfaa4cb03e1b30ce373025cadffa5` i wyników Jira z 17.11.2026. **Autor przeglądu dokumentacji i kodu:** agent na polecenie Marcela Głowackiego; **QA:** wyniki konkretnych prób Marcela wskazano niżej. To nie jest niezależne zatwierdzenie przez developera ani certyfikacja całego ASVS L2.

## Źródło, zakres i zasady interpretacji

- Standard przypięty **OWASP ASVS 5.0.0** (nie `latest`): https://github.com/OWASP/ASVS/tree/v5.0.0/5.0; oficjalne wymagania: https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/docs_en/OWASP_Application_Security_Verification_Standard_5.0.0_en.csv .
- Identyfikatory `v5.0.0-X.Y.Z` oznaczają *konkretną* pozycję z tego wydania. Kolumna L to minimalny poziom przypisany przez OWASP; uwzględniono pozycje L1 i L2, ponieważ L2 obejmuje również L1. To **wybór kontroli z zakresu** auth/session/access/data, nie pełna lista kontroli ASVS L2.
- **PASS (kod)** oznacza, że zaobserwowano mechanizm w kodzie, **PASS (test)** — odnotowano udany test na opisanym środowisku. Nie należy utożsamiać ich z formalnym pełnym odbiorem. **FAIL** — uzasadniona rozbieżność z kontrolą albo zgłoszona reprodukcja; **BLOCKED** — brak dostatecznego dowodu; **N/A** wyłącznie po uzasadnieniu i decyzji reviewera/PO.
- Kontekst implementacji: `backend/app/modules/auth/{router,service,models}.py`, `backend/app/modules/preferences/router.py`, `backend/tests/test_auth.py`, `frontend/e2e/critical-flow.spec.ts`, `DEFINITION_OF_DONE.md`. Weryfikacja kodu nie zastępuje przeglądu konfiguracji serwera.

## Macierz kontrolna — wymagania dobrane do projektu

| Kontrola ASVS 5.0.0 / L | Oczekiwany mechanizm (streszczenie własne) | Dowód, wykonawca, data, SHA/środowisko | Ocena / działanie |
| --- | --- | --- | --- |
| `v5.0.0-6.1.1` / L1 | Udokumentowane limity prób i zachowanie obrony przed brute force | `auth/router.py::count_attempt()` — limity po IP i loginie w PostgreSQL; przegląd kodu 17.11, main `9dad2b2` | **BLOCKED dokumentacja/QA**: dopisać politykę limitów, okno i sposób uniknięcia niezamierzonej blokady; ocenić realne próby |
| `v5.0.0-6.3.1` / L1 | Mechanizmy anti-brute-force realizują udokumentowane zasady | `count_attempt` + `backend/tests/test_auth.py`; przegląd agenta 17.11 | **PASS (kod)** / **BLOCKED** test i konfiguracja przyjętej polityki |
| `v5.0.0-6.2.8` / L1 | Hasło weryfikowane bez obcinania i normalizacji wartości | `auth/router.py` używa `SecretStr`, `service.password_hasher.verify` otrzymuje oryginalny sekret; przegląd kodu 17.11 | **PASS (kod)**; formalny QA i testy Unicode/whitespace do potwierdzenia |
| `v5.0.0-6.4.3` / L2 | Bezpieczny proces odzyskiwania hasła | Testy resetu z atrapą SMTP: SCRUM-56 i SCRUM-44; prawdziwa dostawa e-mail **NOT RUN** | **BLOCKED**: weryfikacja procesu tokenów, limitów, odcięcia sesji i odbioru według uzgodnionego zakresu (bez wysyłki live) |
| `v5.0.0-7.1.1` / L2 | Dokumentacja timeoutu bezczynności i maksymalnej długości sesji wraz z uzasadnieniem | `settings.py` domyślnie `session_hours=12`, `issue_session` ustala absolutny `expires_at`; przegląd kodu 17.11 | **BLOCKED / potencjalna luka**: udokumentować oba rodzaje limitów i ryzyko; brak dowodu niezależnego timeoutu bezczynności |
| `v5.0.0-7.1.2` / L2 | Polityka równoległych sesji jest udokumentowana | SCRUM-56, FF-QA-030 — test dwóch kart (nie dwóch sesji/urządzeń); przegląd 17.11 | **BLOCKED**: ustalić maksymalną liczbę sesji i działanie po przekroczeniu |
| `v5.0.0-7.2.1` / L1 | Weryfikacja tokenu sesyjnego w zaufanym backendzie | `auth/service.py::current_user` sprawdza rekord `LoginSession` i konto | **PASS (kod)**; CI i historyczne QA |
| `v5.0.0-7.2.3` / L1 | Losowy unikalny token referencyjny o odpowiedniej entropii | `secrets.token_urlsafe(32)` i SHA-256 w bazie (`auth/service.py::issue_session`) | **PASS (kod)**; wymaga niezależnego review |
| `v5.0.0-7.3.1` / L2 | Timeout bezczynności zgodny z analizą ryzyka | W `current_user` widoczny absolutny `expires_at`, brak osobnego sprawdzenia aktywności w zbadanym fragmencie | **BLOCKED/prawdopodobna luka**: architektoniczny przegląd całego mechanizmu i test bezczynności, nie ogłaszać FAIL bez potwierdzenia |
| `v5.0.0-7.3.2` / L2 | Absolutna maksymalna długość sesji | `session_hours*3600`, `LoginSession.expires_at`, walidacja przy każdym `current_user` | **PASS (kod)**; FF-QA-031 lokalnie 17.11: wymuszone expiry, Playwright **2/2 PASS** desktop/mobile, syntetyczna baza; to nie naturalny timeout produkcji; SHA lokalnego przebiegu nie odczytano ponownie (ostatni znany kontekst: b770298), nie przypisywac automatycznie do main |
| `v5.0.0-7.4.1` / L1 | Po logout lub expiry serwer odmawia użycia sesji | `current_user` sprawdza expiry; `test_login_opaque_session_and_logout` testuje odwołany token; FF-QA-031 2/2 lokalnie; FF-QA-030 dwie karty na HTTPS zgłoszone PASS | **PASS (kod/test w opisanym zakresie)**; nadal formalny odbiór SCRUM-16/56 |
| `v5.0.0-8.1.1` / L1 | Reguły autoryzacji funkcji/danych opisane w dokumentacji | `editor()` dopuszcza role admin/editor; brak kompletnej zatwierdzonej macierzy uprawnień w przejrzanych dowodach | **BLOCKED**: dodać tabelę admin/editor/viewer × operacje i zasoby |
| `v5.0.0-8.2.1` / L1 | Dostęp do funkcji ograniczany według uprawnień | `auth/service.py::editor()` odmawia viewer 403; ograniczenia pozostałych endpointów wymagają pełnego przeglądu | **PASS (kod częściowo)** / **BLOCKED** pełna inwentaryzacja API |
| `v5.0.0-8.2.2` / L1 | Ochrona dostępu do konkretnych danych/obiektów (IDOR) | `preferences/router.py` pobiera rekord `(user.id,module)`; raport SCRUM-91 wskazuje FAIL przenikania układu w UI A→B (SCRUM-144), niezależnie od klucza backendu | **FAIL w ścieżce izolacji kont (SCRUM-144)** / testy endpointów i UI po poprawce |
| `v5.0.0-8.3.1` / L1 | Autoryzacja po stronie usługi, nie tylko JS | `Depends(current_user)` na preferencjach; `editor` w backendzie; 17.11 Marcel: 3/3 żądań bez sesji API = HTTP 401 na fleet-flow.pl | **PASS (wybrane API)** / **BLOCKED** pełne pokrycie endpointów/roli viewer |
| `v5.0.0-3.3.1` / L1 | Secure cookie i wymagany prefiks nazwy `__Secure-` lub `__Host-` | `auth/service.py`: `COOKIE_NAME="fleet_flow_session"`, `secure=settings.cookie_secure`, bez wymaganego prefiksu; main `9dad2b2` | **FAIL**: zgłosić naprawę nazwy cookie, rozważyć `__Host-` z Secure, Path=/, bez Domain; migracja/cutover i retest obu kart |
| `v5.0.0-3.3.2` / L2 | SameSite adekwatny do celu | `issue_session` `samesite="strict"`; test `test_origin_and_cookie_flags` | **PASS (kod)** / **BLOCKED** końcowy rzeczywisty Set-Cookie na HTTPS |
| `v5.0.0-3.3.3` / L2 | Cookie `__Host-` z wyjątkiem świadomie współdzielonych między hostami | `fleet_flow_session` nie ma prefiksu, brak udokumentowanego uzasadnienia wyjątku | **FAIL**: weryfikacja i zmiana zgodna z 3.3.1 (bez dublowania naprawy) |
| `v5.0.0-3.3.4` / L2 | HttpOnly tokenu sesyjnego | `issue_session(... httponly=True)` oraz `test_origin_and_cookie_flags` | **PASS (kod/test)**; końcowy odczyt nagłówków HTTPS bez ujawnienia tokenu |
| `v5.0.0-3.4.2` / L1 | CORS z allowlistą Origin | `backend/app/main.py::create_app`: `CORSMiddleware` z `allow_origins=list(settings.origins)`. QA HTTPS 17.11.2026: preflight dozwolonego Origin HTTP 200 z `Access-Control-Allow-Origin: https://fleet-flow.pl`; obcego Origin HTTP 400 bez tego nagłówka. Dowód: SCRUM-101 komentarz 10296. `check_origin` dotyczy osobnej ochrony zapisów (CSRF). | **PASS testowanego preflight** / **BLOCKED** pełny audyt API i SCRUM-145 |
| `v5.0.0-2.2.1` / L1 | Walidacja danych i bezpieczne zakresy | SCRUM-146: skrajne wymiary → HTTP 500 zamiast 422 w reprodukcji niezależnego audytu; `_bounded_number` używa `math.isfinite` na olbrzymim int | **FAIL (SCRUM-146)**: poprawka backend i regresje ±, następnie retest QA |
| `v5.0.0-2.2.2` / L1 | Walidacja po stronie zaufanej usługi | `preferences/router.py` wykonuje walidację w backendzie, lecz ma lukę wyjątków z SCRUM-146 | **PASS (koncepcja)** / **FAIL (edge case)** — patrz SCRUM-146 |
| `v5.0.0-14.2.1` / L1 | Tokeny i sekrety nie są przesyłane w URL | Token sesyjny w cookie ustawianym przez `Set-Cookie`; brak jego przesyłania w widocznych URL przeglądu auth | **PASS (kod w zakresie auth)** / **BLOCKED** pełny audyt innych tokenów (np. resetu) |

### Osobne ustalenia bezpieczeństwa poza dosłowną macierzą

1. **SCRUM-145 (P2, FAIL według odtworzenia z 16.11):** `PUT /api/v1/preferences/{module}` przyjmuje brak/obcy `Origin`. W `preferences/router.py::write_preference` brak `Depends(check_origin)`. Jest to luka w kontroli zapisu względem polityki aplikacji — powiązać z analizą CSRF i testami odmowy; nie utożsamiać automatycznie z każdą konfiguracją CORS.
2. **SCRUM-144 (P2, FAIL według odtworzenia z 16.11):** preferencje dashboardu z konta A widoczne po przejściu na konto B. Naprawa i niezależne QA dwóch kont.
3. **SCRUM-146 (P2, FAIL według odtworzenia z 16.11):** duże liczby w layout preferencji mogą skutkować 500. Naprawa i regresje 422 bez zmiany wersji zapisu.
4. **Nowa luka ASVS cookie (P1 do triage):** prefiks `__Host-`/`__Secure-` nie jest stosowany. To ustalenie na podstawie kodu, **nie** przeprowadzony atak. Wymaga decyzji właściciela i osobnego zadania/PR, nie wdrażać bez analizy sesji i odbioru migracji.
5. **Ryzyko polityki timeoutu (do analizy):** opis i egzekwowanie *idle timeout* obok absolutnego `session_hours` pozostają nieudowodnione; po niezależnym potwierdzeniu sklasyfikować jako FAIL lub zaakceptowane ryzyko z dokumentacją.

## Wykonane i niewykonane sprawdzenia

- **PASS (QA):** 17.11.2026 Marcel: niezalogowane `GET /auth/me`, `GET /fleet/vehicles` i `PATCH /trips/{synthetic-id}/annotation` → **401**; na HTTPS wersja `9dad2b2` potwierdzona w Jira SCRUM-141/SCRUM-56. Dwie karty po logout z usuniętym szkicem bez F5 **PASS** (Chrome desktop, 17.11).
- **PASS (test izolowany):** 17.11.2026, FF-QA-031: wymuszenie `expires_at` wyłącznie syntetycznego użytkownika w `fleet_flow_test_e2e`, `GET auth/me` 401, brak szkicu po próbie zapisu; **2/2 Playwright desktop/mobile PASS**, dowód Jira SCRUM-56 oraz SCRUM-141. Nie jest to naturalne wygaśnięcie sesji produkcyjnej.
- **PASS (CI historyczne):** `https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/43965325439`, main `9dad2b2`, 16.11 — wynik run wg poprzedniego audytu Jira; przy oddaniu zweryfikować bieżące SHA i CI po własnym PR.
- **BLOCKED/NOT RUN:** niezależny całościowy code review auth przez Dawida; autoryzacja wszystkich endpointów i macierz ról; cookie `Set-Cookie` na docelowym nowym SHA; kontrola timeoutu bezczynności; realna dostawa SMTP (SCRUM-44, wymaga uzgodnienia); retesty SCRUM-144–146 po naprawach; restore/rollback migracji 0006; formalne QA i decyzja PO.

## Kryteria odbioru SCRUM-101

- [x] Źródło OWASP ASVS 5.0.0 i konkretne identyfikatory L1/L2 we wskazanym zakresie.
- [x] Wstępna macierz z SHA, środowiskiem, dowodami i oceną PASS/FAIL/BLOCKED (w tym FF-QA-031).
- [x] Otwarte znane usterki udokumentowane i powiązane; nowa luka cookie zgłoszona do triage w tym raporcie.
- [ ] Pełne uzgodnienie zakresu kontroli L2 dla auth/session/access/data i uzasadnień N/A z PO/security reviewerem.
- [ ] Testy brakujących scenariuszy i implementacja poprawek przez odpowiednich developerów.
- [ ] PR tej dokumentacji z osobnym review, zielonym wymaganym CI i niezależnym odbiorem.
- [ ] Macierz po ostatecznym SHA oraz wiarygodne potwierdzenie wdrożenia, gdzie wymagane.

**Bezpieczne granice:** brak rzeczywistych haseł, tokenów, cookies, maili, kont klientów i danych floty w dokumencie. Nie prowadzono testów live WEBFLEET/SMTP ani prób łamania produkcji. Raport nie stwierdza `ASVS L2 compliant`.
