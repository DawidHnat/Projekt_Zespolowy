# SCRUM-120 — przegląd OWASP ASVS 5.0.0 L2

## Zakres i zasady

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

| ASVS v5.0.0 | Obszar | Dowód lub obserwacja | Stan |
| --- | --- | --- | --- |
| v5.0.0-6.4.3 | Reset hasła | auth/reset.py, test_password_reset.py; wymagany retest na SHA | BLOCKED |
| v5.0.0-7.1.1 | Polityka sesji | Absolutny limit 12 h; brak zatwierdzonego idle timeout | BLOCKED |
| v5.0.0-7.1.2 | Równoległe sesje | Brak zatwierdzonej polityki liczby sesji | BLOCKED |
| v5.0.0-7.3.1 | Idle timeout | Niezależny limit bezczynności niepotwierdzony | BLOCKED |
| v5.0.0-7.3.2 | Absolute timeout | W kodzie expires_at; potrzebny test na aktualnym SHA | BLOCKED |
| v5.0.0-7.4.1 | Logout i odwołanie | W kodzie usuwanie i odwoływanie sesji; wymagany retest | BLOCKED |
| v5.0.0-8.1.1 | Polityka ról | Do potwierdzenia pełna macierz admin/editor/viewer | BLOCKED |
| v5.0.0-8.2.1 | Autoryzacja | Sprawdzenie wszystkich istotnych endpointów | BLOCKED |
| v5.0.0-8.2.2 | IDOR | Test dwóch kont i izolacji danych | BLOCKED |
| v5.0.0-8.3.1 | Backend authorization | Niezależne próby 401/403 na istniejących obiektach | BLOCKED |
| v5.0.0-3.3.1 | Secure cookie | Nazwa fleet_flow_session bez bezpiecznego prefiksu | FAIL - kod |
| v5.0.0-3.3.2 | SameSite | W kodzie Strict; wymagany dowód Set-Cookie HTTPS | BLOCKED |
| v5.0.0-3.3.3 | Host cookie | Brak prefiksu __Host-; decyzja o naprawie | FAIL - kod |
| v5.0.0-3.3.4 | HttpOnly | W kodzie True; wymagany dowód na wdrożeniu | BLOCKED |
| v5.0.0-3.4.2 | CORS | CORSMiddleware allow_origins; Origin/CSRF to osobna kontrola | BLOCKED |

Oceny dotyczą wskazanych obserwacji, a nie całej
aplikacji. Pozostałe pozycje częściowej macierzy
znajdują się w SCRUM-101-ASVS-5.0.0-L2.md.

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