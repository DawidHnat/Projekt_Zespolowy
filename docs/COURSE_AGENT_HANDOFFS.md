# Polecenia dla agentów — domknięcie oddań 4.1 i 4.2

Stan przygotowania 16.11.2026, [SCRUM-143](https://fleet-flow.atlassian.net/browse/SCRUM-143). Polecenia należy przekazać agentom działającym na komputerach i kontach odpowiednich osób. Nie potwierdzają wykonania pracy przez te osoby. Wybór kandydatów: S1 SCRUM-16, S2 SCRUM-91; wszystkie ich AC pozostają wymagane.

## Marcel

```text
Repozytorium: https://github.com/DawidHnat/Projekt_Zespolowy
Jira: https://fleet-flow.atlassian.net/browse/
Cel zespołu: rzetelnie domknąć zadanie 4.1 (S1/review/PR) oraz 4.2 (S2/bramy jakości/S3).

Przeczytaj AGENTS.md, README, CONTRIBUTING, DEFINITION_OF_DONE.md i aktualne opisy/komentarze wskazanych zgłoszeń. Pobierz aktualny main; zachowaj lokalne zmiany i użyj osobnego worktree, jeśli trzeba. Nie pracuj na zapamiętanym SHA. Zmiany tylko przez gałąź z kluczem Jiry, Conventional Commits i PR z niezależnym review. Przed merge sprawdź wszystkie nowe tematy commitów dokładnym wzorcem z zadania; poprawny tytuł PR przy zwykłym merge nie poprawia tematów jego commitów. Nie zatwierdzaj własnego kodu, nie obchodź ochrony i nie włączaj automerge. Nie zmieniaj historii main ani autorstwa.

Raportuj rzeczywiste SHA, datę, środowisko, wykonawcę i PASS/FAIL/BLOCKED. Oddziel testy wykonane lokalnie od CI i od wyników innych osób. Jeśli wykonawcą był agent, napisz to wprost. Nie publikuj sekretów, haseł, tokenów ani danych klientów. Dane syntetyczne tylko w izolacji testowej. Żywy WEBFLEET i rzeczywista wysyłka SMTP wymagają osobnego uzgodnienia. Nie zmieniaj typów zadań ani historii sprintów dla statystyki.

Twoja rola: niezależny odbiór QA dwóch rzeczywistych Story. Priorytet SCRUM-141: SCRUM-16 z S1 i SCRUM-91 z S2. Używaj istniejącego SCRUM-56 oraz SCRUM-91; pełny odbiór listy/mapy SCRUM-23 to osobny zakres i nie musi blokować wyboru tych Story.

1. Ustal z wyników review Dawida i przekazania Nazarewicza aktualne, wdrożone SHA. Potwierdź po fetch zgodność strony HTTP z origin/main i HTTPS readiness 200/ok. Starszy raport 76efec1 zachowaj jako historyczny dowód, a nowe wyniki podpisz nowym SHA. PR #94 jest już scalony.
2. SCRUM-16 — odbierz wszystkie cztery AC: brak sesji nie daje odczytu ani modyfikacji floty w UI/API; poprawne dane aktywnego konta otwierają pulpit, błędne dają ogólny komunikat; logout unieważnia sesję, expiry wymaga logowania; VPS ma HTTPS, cookie HttpOnly/Secure, hasła są hashowane, sekrety poza Git. Potwierdź także brak prywatnego widoku/szkicu w drugiej karcie bez F5 i odpowiednie późniejsze poprawki auth. Chroniony odczyt i zapis badaj na syntetycznych danych, bez naruszania danych floty.
3. Użyj wyłącznie uzgodnionych kont testowych. Nie zmieniaj hasła współdzielonego QA, sesji innych osób ani zegara produkcji. Kontrolowane expiry/reset i awarie sprawdzaj w izolacji. SMTP pozostaje osobnym SCRUM-44; brak rzeczywistej wysyłki nie jest wynikiem PASS, ale nie rozszerza czterech AC SCRUM-16.
4. SCRUM-91 — PR #93 jest scalony i ma Approved Dawida. Odbierz wszystkie AC w dwóch niezależnych kontekstach przeglądarki i z drugim syntetycznym kontem: backendowy zapis/odtworzenie układu i rozmiarów Pulpitu/Pojazdów, filtrów/sortowania; Zapisz/Anuluj/Przywróć domyślne; ochrona niezapisanego szkicu; konflikt wersji z jawnym Reload/Overwrite; błąd zapisu bez fałszywego sukcesu; świadomy import localStorage bez nadpisania nowszego konta; izolacja kont i modułów. Oddzielne karty współdzielące to samo localStorage nie zastępują dwóch niezależnych kontekstów.
5. Wykorzystaj istniejące testy, aktualne CI PostgreSQL i wyniki UI. Nie przepisuj starych liczników jako nowych. Każdy przypadek zapisuj: oczekiwany/faktyczny rezultat, PASS/FAIL/BLOCKED, data, SHA, środowisko, dowód. Błąd → powiązany Bug oraz retest poprawki na końcowym SHA.
6. W SCRUM-141 uzupełnij osobne macierze dla S1 i S2: wszystkie AC i 12 warunków DEFINITION_OF_DONE.md. Powiąż rzeczywiste review, końcowe CI, merge, wdrożenie, kontrolę wersji oraz dowód restore/rollback od Dawida, jeśli dotyczy. Status Gotowe rodzica nie jest dowodem. Gotowe pliki macierzy są w pakiecie oddania; pola niewykonane pozostają BLOCKED.
7. Jeżeli zakres SCRUM-16 spełnia pełny DoD, potwierdź to jednoznacznie także wtedy, gdy szerszy SCRUM-56 nadal ma otwarty osobny zakres resetu SMTP. Nie zmieniaj AC żadnego zadania i nie zamykaj całego SCRUM-56 tylko dlatego, że odebrano logowanie. Analogicznie rozlicz SCRUM-91.
8. Przekaż Jakubowi Czai dwie decyzje odbioru z linkami i SHA, gotowe do wykorzystania na Review. Nie twórz protokołu nieodbytego spotkania ani nie uruchamiaj Sprintu 3. Własne PR-y, np. #96, wymagają review innej osoby; po połączeniu z #95 kalendarzowy fixture musi działać także z docelową konfiguracją E2E.

Zakończ tabelą: Story S1 — PASS/BLOCKED i braki; Story S2 — PASS/BLOCKED i braki; szerszy SCRUM-56 — co pozostaje osobno. Tylko rzeczywiście wykonane dowody mogą dostać PASS.
```

## Dawid

```text
Repozytorium: https://github.com/DawidHnat/Projekt_Zespolowy
Jira: https://fleet-flow.atlassian.net/browse/
Cel zespołu: rzetelnie domknąć zadanie 4.1 (S1/review/PR) oraz 4.2 (S2/bramy jakości/S3).

Przeczytaj AGENTS.md, README, CONTRIBUTING, DEFINITION_OF_DONE.md i aktualne opisy/komentarze wskazanych zgłoszeń. Pobierz aktualny main; zachowaj lokalne zmiany i użyj osobnego worktree, jeśli trzeba. Nie pracuj na zapamiętanym SHA. Zmiany tylko przez gałąź z kluczem Jiry, Conventional Commits i PR z niezależnym review. Przed merge sprawdź wszystkie nowe tematy commitów dokładnym wzorcem z zadania; poprawny tytuł PR przy zwykłym merge nie poprawia tematów jego commitów. Nie zatwierdzaj własnego kodu, nie obchodź ochrony i nie włączaj automerge. Nie zmieniaj historii main ani autorstwa.

Raportuj rzeczywiste SHA, datę, środowisko, wykonawcę i PASS/FAIL/BLOCKED. Oddziel testy wykonane lokalnie od CI i od wyników innych osób. Jeśli wykonawcą był agent, napisz to wprost. Nie publikuj sekretów, haseł, tokenów ani danych klientów. Dane syntetyczne tylko w izolacji testowej. Żywy WEBFLEET i rzeczywista wysyłka SMTP wymagają osobnego uzgodnienia. Nie zmieniaj typów zadań ani historii sprintów dla statystyki.

Twoja rola: właściciel repozytorium i niezależny reviewer. Priorytety: SCRUM-140, review auth dla SCRUM-16/56/141, dowód odtworzenia dla wybranych Story.

1. SCRUM-140: zweryfikuj zalogowane konto i uprawnienia. Obecny odczyt wymaga tylko Required CI. Dodaj jako osobne wymagane checki Lint i Backend (3.13), zachowując Required CI, aktualność gałęzi, niezależne approval i wszystkie pozostałe zabezpieczenia, w tym egzekwowanie wobec administratorów. Zachowaj nazwy jobów. Nie zastępuj całej ochrony uproszczonym zestawem ustawień.
2. Zapisz rzeczywisty wynik jednego z poleceń w klonie zespołu:
   gh api 'repos/{owner}/{repo}/branches/main' --jq '.protection.required_status_checks.contexts[]'
   albo dla rulesetu:
   gh api 'repos/{owner}/{repo}/rules/branches/main' --jq '.[] | select(.type == "required_status_checks") | .parameters.required_status_checks[].context'
   Wynik ma zawierać wymagany job testów i Lint; nie wymagaj Post-deploy smoke dla PR, bo deployment PR jest pomijany. Potwierdź blokadę celowych dowodów #77/#78. Nigdy nie scalaj #24/#77/#78.
3. Potwierdź w SCRUM-140 rzeczywistą datę/godzinę i strefę włączenia ochrony na podstawie dostępnego zdarzenia lub własnego wiarygodnego zapisu. Jeśli nie można ustalić godziny, opisz ograniczenie. Nie wybieraj daty dla uzyskania zera. Przekaż wynik do SCRUM-143.
4. Wykonaj niezależny review aktualnej implementacji SCRUM-16: logowanie, ogólne błędy, limit prób, sesje/logout/expiry, chronione UI/API, cookie i Origin/CSRF oraz czyszczenie widoku między kartami. Przejrzyj kod backendu i frontendu, nie tylko dokument. Zapisz zakres, SHA, pliki, wynik i blokady w SCRUM-56 oraz SCRUM-141. Nie dopisuj pozornego historycznego Approved do #10. PR #94 jest już scalony i nie zastępuje pełnego review auth.
5. Zbadaj timeout test_postgres_login_with_old_password_cannot_outlive_reset opisany w SCRUM-56. Zweryfikuj hipotezę snapshotu pg_stat_activity i synchronizację obserwatora. Nie osłabiaj asercji, nie pomijaj testu i nie ukrywaj problemu samym retry lub większym timeoutem. Potrzebna poprawka → osobny PR z cudzym review.
6. Dla DoD wybranych SCRUM-16 i SCRUM-91 sprawdź istniejący dowód restore/rollback zmian schematu. SCRUM-91 dostarczono w PR #93, z migracją preferencji. Jeśli dowodu brakuje, wykonaj właściwą próbę w izolowanym PostgreSQL na danych syntetycznych, bez zmian produkcyjnej bazy i konfiguracji VPS. Zapisz procedurę, SHA i wynik. Nie deklaruj off-site backupu SCRUM-84 na podstawie tej próby.
7. Uruchom wymagane kontrole backendu przy poprawkach: ruff check ., ruff format --check ., pytest. Zbierz końcowe CI; nie uznawaj testów pominiętych z braku PostgreSQL za pełny PASS.
8. Przekaż Marcelowi sprawdzone SHA i zakres retestu. Uzupełnij istniejące SCRUM-140/56/141, bez tworzenia duplikatów. Przejrzyj także gotowy PR aktualizujący pakiet SCRUM-143, jeśli review zostało Ci zlecone.

Ważne: rzeczywista dostawa SMTP jest osobnym SCRUM-44, poza czterema AC SCRUM-16. Nie blokuj odbioru samego logowania nieuzgodnioną wysyłką, ale nie przedstawiaj jej jako wykonanej. Historyczny test Conventional Commits daje obecnie 3 w szerokim zakresie od 20.10 — dwa tematy z #93 i jeden z #54. Ani nowy commit, ani zmiana tytułu zamkniętego PR nie naprawia tego wyniku; rozliczenie z prowadzącym prowadzi Jakub w SCRUM-143.

Zakończ konkretnym podsumowaniem: wymagane checki + data ochrony, wynik review auth, wynik odtworzenia, linki PR/CI/Jira i dokładnie co blokuje odbiór. Nie zamykaj cudzych zakresów na podstawie samego CI.
```

## Jakub Nazarewicz

```text
Repozytorium: https://github.com/DawidHnat/Projekt_Zespolowy
Jira: https://fleet-flow.atlassian.net/browse/
Cel zespołu: rzetelnie domknąć zadanie 4.1 (S1/review/PR) oraz 4.2 (S2/bramy jakości/S3).

Przeczytaj AGENTS.md, README, CONTRIBUTING, DEFINITION_OF_DONE.md i aktualne opisy/komentarze wskazanych zgłoszeń. Pobierz aktualny main; zachowaj lokalne zmiany i użyj osobnego worktree, jeśli trzeba. Nie pracuj na zapamiętanym SHA. Zmiany tylko przez gałąź z kluczem Jiry, Conventional Commits i PR z niezależnym review. Przed merge sprawdź wszystkie nowe tematy commitów dokładnym wzorcem z zadania; poprawny tytuł PR przy zwykłym merge nie poprawia tematów jego commitów. Nie zatwierdzaj własnego kodu, nie obchodź ochrony i nie włączaj automerge. Nie zmieniaj historii main ani autorstwa.

Raportuj rzeczywiste SHA, datę, środowisko, wykonawcę i PASS/FAIL/BLOCKED. Oddziel testy wykonane lokalnie od CI i od wyników innych osób. Jeśli wykonawcą był agent, napisz to wprost. Nie publikuj sekretów, haseł, tokenów ani danych klientów. Dane syntetyczne tylko w izolacji testowej. Żywy WEBFLEET i rzeczywista wysyłka SMTP wymagają osobnego uzgodnienia. Nie zmieniaj typów zadań ani historii sprintów dla statystyki.

Twoja rola: developer Jakub Nazarewicz. Priorytetem do oddania 4.2 jest pełny, niezależnie odebrany SCRUM-91, obecnie Testowanie w Sprincie 2. To Story preferencji konta dostarczona przez PR #93; nie myl jej z PR #91 dotyczącym wdrożeń.

1. Sprawdź aktualne AC SCRUM-91 oraz stan main po scaleniu #93. Nie przepisuj gotowej funkcji. Przygotuj przekazanie do QA z linkiem do aktualnego Approved Dawida, CI ostatniego head #93 i bieżącego wdrożenia. Dawny zapis sugerujący review własnego kodu jest nieaktualny: review wykonuje Czaja albo Hnat, QA Marcel.
2. Udokumentuj powtarzalną procedurę dla Marcela: dwa niezależne konteksty/urządzenia tego samego konta, drugie konto do izolacji, backendowe preferencje Pulpitu/Pojazdów, rozmiary, sortowanie i filtry, zapis/anulowanie/reset, konflikt wersji, awaria zapisu i świadoma migracja localStorage. Wskaż endpointy i istniejące testy; bez sekretów ani kont klientów w raportach.
3. Sprawdź kompletność rzeczywistej implementacji każdego AC. Jeśli coś nie działa albo QA zgłosi błąd, popraw tylko ten zakres na nowej gałęzi z kluczem SCRUM-91 i przez PR z niezależnym review. Nie dopisuj funkcji spoza AC. Po zmianie UI przeczytaj DESIGN_SYSTEM, uruchom npm test i npm run build oraz sprawdź desktop/mobile w przeglądarce. Po zmianie backendu uruchom Ruff/format/pytest według AGENTS.md. Nie ukrywaj błędów podnoszeniem timeoutów lub pomijaniem testów.
4. Przekaż Dawidowi informacje o migracji preferencji i wymaganym dowodzie odtworzenia, a Marcelowi dokładne SHA i instrukcję retestu. W SCRUM-91 i SCRUM-141 zapisz wykonane kontrole oraz ograniczenia. Sam własny test autora nie jest niezależnym QA.
5. Po pełnym odbiorze przygotuj prosty pokaz na Review S2 według potrzeby użytkownika: zapisuję widok → loguję się w drugiej przeglądarce → dostaję ten sam widok; następnie konflikt i odzyskanie po błędzie. Faktyczny pokaz i feedback zapisuje PO po spotkaniu.
6. Potwierdź przygotowanie SCRUM-129 jako istniejącego „wybitego okna” w planowanym S3: frontend/vite.config.ts oraz frontend/src/features/fleet/components/VehicleMap.tsx, powtarzalne ostrzeżenie o dużym bundlu. Do oddania 4.2 trzeba zaplanować to zadanie w aktywnym S3; nie trzeba kończyć całego S3 ani wykonywać teraz tej optymalizacji. Nie podnoś limitu ostrzeżeń dla ukrycia problemu.
7. Dla kolejnych commitów bezwzględnie stosuj Conventional Commits. Dwa istniejące tematy #93 są niezgodne; zachowaj chronioną historię i przekaż fakt do SCRUM-143 zamiast próbować „naprawić” main amend/rebase/force-push. Nowa poprawna wiadomość nie usuwa starych commitów.

Nie zatwierdzaj własnego PR ani nie zamykaj SCRUM-91 przed niezależnym QA i pełnym DoD. Nie uruchamiaj Sprintu 3 ani nie deklaruj odbytego Review/retro. Zakończ linkami do dowodów, instrukcją QA i listą pozostałych blokad.
```
