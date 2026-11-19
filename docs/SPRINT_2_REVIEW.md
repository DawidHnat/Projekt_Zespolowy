# Sprint 2 Review — potwierdzone ustalenia i uzupełnienie odbioru

**Spotkanie odbyło się 18.11.2026** — potwierdzenie PO Jakuba Czai przekazane
19.11.2026. Obecni: **Jakub Czaja, Dawid Hnat, Jakub Nazarewicz, Marcel Głowacki**.
Godziny i miejsce: nieustalone. Zapis: **agent Codex na polecenie Jakuba Czai**;
agent nie uczestniczył w spotkaniu.
[Źródło potwierdzenia, SCRUM-142/10347](https://fleet-flow.atlassian.net/browse/SCRUM-142?focusedCommentId=10347).
[Uzupełniony zakres pokazu i ocena retro](https://fleet-flow.atlassian.net/browse/SCRUM-142?focusedCommentId=10365).

| Element protokołu | Rzeczywiście przekazany wynik | Ocena dowodu |
| --- | --- | --- |
| Data / obecność | 18.11.2026, cała czwórka | PASS potwierdzenia PO |
| Przyrost / feedback | PO: przyrost jest w porządku, ale na razie mało widoczny na stronie; Story trzeba jak najszybciej odebrać | PASS zapisu feedbacku; bez domniemania pełnego odbioru |
| Pokaz / SHA / scenariusze | PO opisał pokaz mapy, szczegółów i zdjęć pojazdów, ustawień/stylów, kafelków i zapisu, aktualizacji/statusów, login/logout i wyszukiwania modułów; szczegóły poniżej. SHA i adres pokazu nieustalone | PASS relacji o zakresie; nie pełny protokół AC/DoD |
| Priorytet | Dokończyć bieżący S2 i rozpocząć istniejący S3 z przygotowanymi odpowiedziami 3.2/4.2 | PASS decyzji PO; wykonanie zależy od kryteriów |
| Zakres / dostępność S3 | PO 19.11 potwierdził zakres oraz stabilną dostępność dla istniejącego planu, w tym 128/129 | PASS potwierdzenia PO, bez cudzych indywidualnych podpisów |

## Faktycznie pokazany zakres — relacja PO uzupełniona 19.11

Na Review 18.11 zespół obejrzał całą mapę z przybliżaniem/oddalaniem,
wybierał pojazdy i otwierał szczegóły, ustawiał zdjęcia i sprawdzał ich
prezentację na mapie. Przejrzano ustawienia, style i personalizację,
odświeżanie danych, statusy i aktualność synchronizacji, logowanie/wylogowanie,
wyszukiwanie modułów oraz personalizację kafelków wszystkich modułów i zapis.

Mapowanie opisu przez agenta: SCRUM-5/21 (mapa), 16 (auth), 38 (dashboard),
45 (zdjęcia/personalizacja), częściowo 46/91 (układ i zapis), 15 (synchronizacja).
PO nie podał numerów Story. **SHA i dokładne środowisko pokazu nieustalone.**
Nie dopisujemy synchronizacji dwóch urządzeń, izolacji kont, pełnych regresji
46 ani kontrolowanego live 64, których relacja nie potwierdza. Zakres pokazu
nie zastępuje pełnego AC/DoD ani podpisu końcowego QA.

## Krótki pokaz SCRUM-91 po odbiorze

To przygotowanie **uzupełniającego pokazu**, nie opis niewykonanych kroków
z 18.11. Kandydat S2: **SCRUM-91**. Administracyjne Gotowe nie jest jeszcze
pełnym odbiorem. Używamy dwóch niezależnych kontekstów tego samego silnika
(np. Chrome i okno incognito), tego samego konta do synchronizacji i drugiego
syntetycznego konta do izolacji. **Jedna firma i jedno API** pozostają zakresem.

Warunek pokazu jako ukończonej Story: Marcel zapisuje wszystkie 4 AC i 12 DoD
w SCRUM-141, a PO potwierdza zakres. Review auth i ocena restore z 10324/10345
są już wykonane; nie uruchamiamy odłożonego off-site SCRUM-84 ani żywego SMTP.

| Czas agendy Review (15–20 min) | Czynność i dowód |
| --- | --- |
| 0–3 min | Potrzeba: własny układ wraca na innym urządzeniu. Odczyt main/HTTP/HTTPS/readiness, wskazanie testowanego SHA i pełnej macierzy 141. |
| 3–10 min | Kontekst A: zapisać Pulpit i rozmiar/filtr/limit Pojazdów. Kontekst B tego samego konta: odczytać wynik. Pokazać Zapisz, Anuluj i Reset bez utraty niezapisanego szkicu. |
| 10–15 min | W kontrolowanej izolacji: konflikt Reload/Overwrite, błąd zapisu bez fałszywego sukcesu; świadoma migracja, drugie konto bez ustawień A. Bez danych klientów. |
| 15–20 min | Zebrać konkretne uwagi, zaakceptowany zakres i otwarte zgłoszenia z właścicielami; przejść po 12 pozostałych pracach S2. |

### Karta feedbacku do uzupełniającego pokazu

| Pole | Zapis po rzeczywistym wykonaniu |
| --- | --- |
| Wykonawca, data, SHA, środowisko | Konkretne osoby i wersja, bez przypisywania dzisiejszego main wczorajszemu spotkaniu |
| Scenariusz / oczekiwany / faktyczny rezultat | Każde wykonane AC oraz PASS/FAIL/BLOCKED, odnośnik do dowodu |
| Feedback / decyzja | Konkretna uwaga; jawnie brak uwag tylko jeśli taki wynik faktycznie zebrano |
| Błąd / dalsze działanie | Istniejący lub nowy klucz, właściciel, uzgodniony termin |
| Akceptacja | Niezależny QA Marcela i decyzja zakresu PO; brak podpisu pozostaje BLOCKED |

## Stan S2 przed rozliczeniem — 19.11.2026

Main `cb634da0ece8cd93424bfc16a5185cf817a0cbb1`,
[CI/deploy/smoke 44386951054](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/44386951054)
PASS; publiczny HTTP i HTTPS wskazują `cb634da`, readiness 200/status ok.
Sprawdził agent Jakuba Czai 19.11, bez odczytu floty. Nie jest to SHA pokazu.
S2 id=3 **active**, S3 id=4 **future**; nie tworzono sprintów ani nie przenoszono prac.

| Pozycje z bazowego odczytu S2 (12) | Właściciel | Wynik i pozostały zakres |
| --- | --- | --- |
| SCRUM-21 | Jakub Nazarewicz | Odbiór markerów/wyboru/podglądu i zakresu danych; Safari wyłączone z obowiązkowego zakresu decyzją PO 19.11, bez PASS niewykonanego testu |
| SCRUM-23 | Marcel Głowacki | Brakujące scenariusze kontrolowanych markerów/nowych pól i adekwatny odbiór synchronizacji po 64 |
| SCRUM-40 | Marcel Głowacki | Końcowy niezależny odbiór układu/personalizacji i izolacji kont; wykorzystać wspólne scenariusze 46 |
| SCRUM-46 | Jakub Czaja | Regresja z #120 trafiła do `main`. #126 poprawia nadpisywanie zapisanego rozmiaru przez opóźniony zapis filtra. |
| SCRUM-64 | Dawid Hnat | Własny kontrolowany live: pierwszy odczyt/cykle/API/UI/restart i QA; kopie/rollback SCRUM-18, bez wymagania zakończonego 84 |
| SCRUM-65 | Jakub Czaja | Pomiar i ocena retro zapisane, nowe działanie Jakuba z 19.11; pozostają pełny DoD jednej Story w 141 i review/main dokumentacji |
| SCRUM-94 | Jakub Czaja | Arkusz #121 uzupełniony danymi PO; właściciel wskazany lokalnie, brak konsultacji i pełnych procedur 113 |
| SCRUM-101 | Marcel Głowacki | Własne AC bezpieczeństwa i otwarte pozycje ASVS; review auth jest już dowodem, nie nowym brakiem |
| SCRUM-133 | Jakub Czaja | Po scaleniu #105 automat krótko ustawił Gotowe. Jakub przywrócił W toku. #101 i #110 nadal oczekują dostarczenia do `main`, a odbiór kierowców i alertów pozostaje w QA 54/33. |
| SCRUM-141 | Marcel Głowacki | Pełne AC/12 DoD 16/91 i końcowy niezależny QA, zachowując wykonany review/restore |
| SCRUM-142 | Jakub Czaja | Uzupełnienie rzeczywistych wyników, PR/review/CI/main i późniejsze przełączenie S2→S3 |
| SCRUM-143 | Jakub Czaja | Pakiet 3.2 przed zamknięciem S2; końcowy 4.2 po rzeczywistym starcie S3, dowody po ostatnim merge |

**Osobno SCRUM-84: końcowy S5 id=37, Dawid Hnat.** Narzędzia backupu są w
`main` od `70a38db`. Wybór storage, uruchomienie timerów i operacyjna próba
odtworzenia pozostają w Sprint 5. [PR #105](https://github.com/DawidHnat/Projekt_Zespolowy/pull/105)
#119/SCRUM-150 jest poza S2; nie jest dodatkowym warunkiem zamknięcia i nie
ponawiamy odmówionej prośby o dostępność reviewera.

## Rozliczenie i następny sprint

[Retro S2](retro/sprint-2.md) zapisuje potwierdzone fakty i brakujące oceny.
Przed przełączeniem należy zachować datowany kompletny pakiet **3.2** z aktywnym
S2 i pełnym S1. Po spełnieniu kryteriów bieżącego S2 oraz decyzji PO o jego
rozliczeniu zamykamy **istniejący S2 id=3** i uruchamiamy **istniejący S3 id=4**,
bez antydatowania, równoległego sprintu i przenoszenia niedokończonych prac dla wyniku.
Na końcu: deploy/smoke, świeży SHA i pakiet **4.2**. 142/143 nie są Done przed tym krokiem.
