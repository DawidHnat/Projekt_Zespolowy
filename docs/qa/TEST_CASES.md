# Fleet-Flow — przypadki testowe i macierz pokrycia

**Jira:** SCRUM-37  
**Właściciel:** Marcel Głowacki  
**Wersja:** 1.0 — do review  
**Wykonanie:** **NOT RUN** dla wszystkich przypadków.

## Jak czytać i wykonać

Identyfikatory `FF-QA-NNN` są stabilne w obrębie tego dokumentu. Dane (V01, T01, D01, A01, U01 itd.) definiuje `TEST_DATA.json`. Priorytet P0 = bieżący Sprint 1, P1/P2 = plan następnych sprintów, nie przypisanie nowych dat. Kroki są instrukcją na przyszłość; przed faktycznym uruchomieniem fixture należy przekształcić do kontraktu/stubu użytego w odpowiednim teście. Sztuczne rekordy nie powinny trafiać do bazy produkcyjnej ani do żywego WEBFLEET.

Każdy przypadek ma z góry określony oczekiwany wynik i **miejsce na późniejszy dowód** (wspólna tabela wykonania na końcu). Nie przypisuj PASS bez rzeczywistego testu, numeru SHA, środowiska i dowodów.

## Scenariusze

### Sprint 1 — wygląd, personalizacja i układ

#### FF-QA-001 — Czysty checkout / testy / build

- **Jira:** SCRUM-40/38. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Commit SHA, środowisko bez lokalnych zmian.
- **Kroki:** npm ci; npm test; npm run typecheck; npm run build.
- **Oczekiwany wynik:** Polecenia kończą się kodem 0; SHA i wersje środowiska zapisane; bez deklarowania sukcesu bez wykonania.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-002 — Puste moduły bez udawanych danych

- **Jira:** SCRUM-40. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Konto testowe; niezrealizowane moduły.
- **Kroki:** Otwórz Pulpit, Mapę, Serwis, Ewidencję, Kierowców i Alerty.
- **Oczekiwany wynik:** Stany puste i komunikaty są czytelne; niewdrożona funkcja nie wyświetla fikcyjnych odczytów WEBFLEET.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-003 — Motyw, akcent i style

- **Jira:** SCRUM-40. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Wariant jasny/ciemny/system; klasyczny/szklany.
- **Kroki:** Zmień motyw, styl i kolor; odśwież stronę.
- **Oczekiwany wynik:** Zapis lokalny i poprawna czytelność w każdym wariancie.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-004 — Tło galerii i obraz własny

- **Jira:** SCRUM-40. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Poprawny JPG/PNG/WebP <10 MB i <=40 MP; błędny typ; ponad limity.
- **Kroki:** Wybierz, odśwież, usuń; podaj błędne pliki.
- **Oczekiwany wynik:** Poprawny obraz przechowywany lokalnie; błędny odrzucony z komunikatem; obraz nie jest wysyłany na backend.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-005 — Edytor: zapisz/anuluj

- **Jira:** SCRUM-40. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Pulpit; lokalny czysty stan.
- **Kroki:** Przesuń kafelek; Anuluj; powtórz i Zapisz; odśwież.
- **Oczekiwany wynik:** Anuluj nie utrwala; Zapisz utrwala; wejście w edycję nie przesuwa siatki.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-006 — Wymiar minimalny i reset

- **Jira:** SCRUM-40. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Duża i mała szerokość ekranu.
- **Kroki:** Zmniejsz kafelek do minimum, sprawdź nagłówki/pierwszy rekord; Reset.
- **Oczekiwany wynik:** Treść kluczowa czytelna; reset zgodny z domyślnym układem.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-007 — Niezależne układy Pulpit/Mapa, desktop/mobile

- **Jira:** SCRUM-40. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Dwa widoki, dwa tryby szerokości.
- **Kroki:** Zapisz Pulpit desktop; anuluj zmiany Mapy; zapisz osobny wariant mobile.
- **Oczekiwany wynik:** Ustawienia nie przeciekają między widokami i szerokościami.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-008 — Zbiorowa edycja i paginacja

- **Jira:** SCRUM-40/46. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Kilka kart pojazdów, mały ekran.
- **Kroki:** Zaznacz wszystkie/wybrane, zmień rozmiar, odrzuć szkic, przewiń listę.
- **Oczekiwany wynik:** Zmiany dotyczą tylko wyboru; paginacja nie zasłania kart; anulowanie odrzuca szkic.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-009 — Dostępność klawiatury i reduced motion

- **Jira:** SCRUM-40. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Tab/Enter/Escape/strzałki, prefers-reduced-motion.
- **Kroki:** Wykonaj podstawową obsługę bez myszy; ogranicz animacje.
- **Oczekiwany wynik:** Widoczny fokus, osiągalne kontrolki, zmniejszone animacje.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-010 — Safari i responsywność

- **Jira:** SCRUM-40. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Desktop, widok telefoniczny, Safari macOS/iOS.
- **Kroki:** Sprawdź motywy, edycję, tekst i menu.
- **Oczekiwany wynik:** Brak uciętych kluczowych treści, sterowanie działa; brak Safari = BLOCKED dla tego środowiska.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

### Sprint 1 — lista, mapa, synchronizacja

#### FF-QA-011 — API/lista bez sesji

- **Jira:** SCRUM-5/16/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Niezalogowany użytkownik.
- **Kroki:** GET /api/v1/fleet/vehicles i /map; otwórz UI.
- **Oczekiwany wynik:** API odrzuca nieautoryzowany odczyt (401); UI nie wyświetla danych.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-012 — Lista i mapa: wspólny zakres

- **Jira:** SCRUM-5/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** V01–V06; świeże i stare GPS.
- **Kroki:** Wczytaj listę i mapę; porównaj wszystkie rekordy oraz ich mapowalność.
- **Oczekiwany wynik:** Zgodne filtry i identyfikacja; pozycje bez ważnego GPS nie dostają fikcyjnych markerów; stare wyraźnie opisane.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-013 — Wyszukiwanie po nazwie i rejestracji

- **Jira:** SCRUM-5/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** QA Dostawczy, ZZ 1001A, brak dopasowań.
- **Kroki:** Wykonaj trzy zapytania w UI i API; wyczyść q.
- **Oczekiwany wynik:** Wyniki zgodne z TEST_DATA.search_expectations; brak dopasowań jest pustym stanem.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-014 — Filtr statusu i łączenie z q

- **Jira:** SCRUM-5/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** moving/stopped/offline/unknown, V01–V06.
- **Kroki:** Ustaw kolejno statusy i q; zresetuj oba filtry.
- **Oczekiwany wynik:** Lista i mapa mają jeden stan filtrów; reset przywraca pełen zbiór.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-015 — Brak GPS i nieznane pola

- **Jira:** SCRUM-5/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** V04, null GPS/odometer/speed.
- **Kroki:** Znajdź V04 na liście, otwórz widok mapy.
- **Oczekiwany wynik:** V04 nadal na liście, bez markera; brak GPS i nieznane wartości są jawne, nie zastąpione zerami.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-016 — Nakładające się markery bez klastrów

- **Jira:** SCRUM-5/21/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** V01 i V05 — ten sam punkt.
- **Kroki:** Kliknij marker i rozwiń wybór; wybierz każdego pojazdu.
- **Oczekiwany wynik:** Każdy pojazd dostępny osobno, brak klastrów; zaznaczenie spójne z listą.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-017 — Podgląd → Szczegóły, fokus, Escape

- **Jira:** SCRUM-5/21/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** V01 z poprawnym GPS.
- **Kroki:** Wybierz na liście i mapie; otwórz podgląd; Szczegóły; Escape.
- **Oczekiwany wynik:** Najpierw mały podgląd; dopiero przycisk otwiera duży dialog; cztery zakładki, klawiatura i fokus działają.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-018 — Nieaktualność a czas otrzymania

- **Jira:** SCRUM-5/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** V03 (stare position_at, późne received_at).
- **Kroki:** Otwórz V03, sprawdź czas pomiaru i świeżość.
- **Oczekiwany wynik:** Nie jest traktowany jak świeży na podstawie received_at; pojawia się status offline/stale i widoczna data pomiaru.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-019 — GPS (0,0) jako wartość poprawna

- **Jira:** SCRUM-5/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** V06: lat=0 lon=0, gps_quality=A.
- **Kroki:** Wyświetl V06 na mapie.
- **Oczekiwany wynik:** Marker może być wyświetlony w punkcie (0,0); zero nie jest traktowane jako brak danych.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-020 — Nieprawidłowa jakość/współrzędne

- **Jira:** SCRUM-5/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** BadFix-01…04 z TEST_DATA.
- **Kroki:** Podaj pomiary V/L/0, niepełny GPS oraz zakres poza granicami.
- **Oczekiwany wynik:** Nie są przedstawiane jako aktualna, dokładna pozycja; nie powstają sztuczne markery.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-021 — Pusta flota a pusty filtr

- **Jira:** SCRUM-5/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** E01 poprawne [] oraz istniejący zbiór z q bez dopasowań.
- **Kroki:** Odtwórz wariant E01 i q bez trafień.
- **Oczekiwany wynik:** Odrębne, czytelne komunikaty; prawidłowo pusta flota nie oznacza awarii.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-022 — Zimny cache i awaria API

- **Jira:** SCRUM-5/15/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** E02: brak cache i źródła.
- **Kroki:** Zasymuluj brak źródła, GET listy/mapy.
- **Oczekiwany wynik:** HTTP 503 SOURCE_UNAVAILABLE, komunikat bez wycieku tajnych danych.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-023 — Awaria po sukcesie i odzyskanie

- **Jira:** SCRUM-5/15/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** E03; poprzednio poprawny cache.
- **Kroki:** Zasymuluj sukces, awarię źródła, następnie odzyskanie.
- **Oczekiwany wynik:** Cache dostępny ze statusem degraded i czasem ostatniego sukcesu; po sukcesie ostrzeżenie ustępuje.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-024 — Timeout i ponowienia

- **Jira:** SCRUM-5/15/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** E04: timeout WEBFLEET.
- **Kroki:** Zasymuluj timeout w izolacji.
- **Oczekiwany wynik:** Bez pętli nieograniczonych retry; jawny stan błędu, brak zmiany ostatniego sukcesu.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-025 — Idempotencja, stabilne UID i dane ręczne

- **Jira:** SCRUM-5/15/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** V01; powtórzony zestaw; zmieniona nazwa.
- **Kroki:** Zaimportuj snapshot 2x; zmień nazwę; sprawdź metadane lokalne.
- **Oczekiwany wynik:** Jeden rekord na source_account+external_uid; brak nadpisania lokalnych kierowców, przypisań, adnotacji.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-026 — Paginacja i mapa bez paginacji

- **Jira:** SCRUM-5/19/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Co najmniej 3 rekordy; page_size=2.
- **Kroki:** GET lista page=1/2; GET mapa z tymi samymi filtrami.
- **Oczekiwany wynik:** Lista ma total po filtrach i stabilne strony; mapa nie ogranicza się do pierwszej strony listy.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-027 — Mapbox niedostępny / responsywność

- **Jira:** SCRUM-5/23. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Brak pk. tokenu, WebGL; mały ekran.
- **Kroki:** Otwórz UI przy braku Mapbox i na telefonie.
- **Oczekiwany wynik:** Lista nadal działa, brak pustego ekranu, informacja o mapie; mapa nad listą na małym ekranie.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

### Sprint 1 — logowanie, sesje i reset

#### FF-QA-028 — Logowanie aktywnego użytkownika

- **Jira:** SCRUM-16/56. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** U01; hasło ustawione poza fixture JSON.
- **Kroki:** Zaloguj się poprawnymi danymi.
- **Oczekiwany wynik:** Zwrócony profil/chronione UI bez wycieku sekretów.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-029 — Niepoprawne hasło i nieistniejący login

- **Jira:** SCRUM-16/56. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** U01/U04; błędne testowe hasło.
- **Kroki:** Dwa żądania login.
- **Oczekiwany wynik:** 401 i neutralny komunikat bez rozpoznania konta.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-030 — Wylogowanie w wielu kartach

- **Jira:** SCRUM-16/56. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** U01; dwie karty i jedna sesja.
- **Kroki:** Zaloguj, otwórz drugą kartę, wyloguj, odśwież obie.
- **Oczekiwany wynik:** Sesja unieważniona; brak chronionego odczytu w obu kartach.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-031 — Wygasła sesja i ponowne logowanie

- **Jira:** SCRUM-16/56. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Krótki czas sesji wyłącznie na izolowanym środowisku.
- **Kroki:** Wygaśnij sesję i wyślij GET /auth/me oraz /fleet/vehicles.
- **Oczekiwany wynik:** Odmowa dostępu; UI żąda logowania, nie pokazuje prywatnych danych.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-032 — Cookies i Origin / CSRF

- **Jira:** SCRUM-16/56. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** HTTPS, prawidłowy i obcy Origin.
- **Kroki:** Sprawdź Set-Cookie; POST/PATCH z obcym Origin.
- **Oczekiwany wynik:** HttpOnly/SameSite=Strict/Secure (HTTPS); niepoprawny Origin odrzucony (403).
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-033 — Limit prób logowania

- **Jira:** SCRUM-16/56. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** U01; test izolowany, brak współdzielonych użytkowników.
- **Kroki:** Przekrocz 10 prób na IP/login w minutę.
- **Oczekiwany wynik:** 429 RATE_LIMITED; nie wykonuj na produkcyjnych kontach.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-034 — Konto nieaktywne i role

- **Jira:** SCRUM-16/56. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** U02 viewer, U03 inactive, U01 editor.
- **Kroki:** Logowanie inactive; wykonaj chroniony odczyt i próbę zapisu viewerem.
- **Oczekiwany wynik:** Nieaktywny nie loguje się; viewer może czytać, lecz nie edytować reguł; editor z właściwym Origin może je edytować.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-035 — Neutralny reset i atrapa SMTP

- **Jira:** SCRUM-44/56. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Istniejący login z/bez e-maila oraz U04.
- **Kroki:** Zażądaj resetu dla trzech wariantów, odczytaj atrapę.
- **Oczekiwany wynik:** Odpowiedź publiczna neutralna; brak prawdziwej wysyłki.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-036 — Token jednorazowy, wygasły, limity

- **Jira:** SCRUM-44/56. **Priorytet:** P0. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Wyłącznie syntetyczny token wygenerowany przez izolowany test.
- **Kroki:** Zresetuj hasło ważnym tokenem, powtórz; przetestuj wygasły; sprawdź sesje.
- **Oczekiwany wynik:** Powtórne/wygasłe tokeny odrzucone; reset unieważnia wcześniejsze sesje; ograniczenia działają.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

### Sprint 2 — historia, ewidencja, kierowcy

#### FF-QA-037 — Izolacja historii pojazdu

- **Jira:** SCRUM-6/28. **Priorytet:** P1. **Status:** NOT RUN.
- **Dane / warunki wstępne:** T01–T04, V01/V02.
- **Kroki:** Otwórz historię V01, następnie V02, spróbuj niewłaściwego ID.
- **Oczekiwany wynik:** Widoczne wyłącznie właściwe przejazdy; brak przenikania danych i uprawnień.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-038 — Półotwarte granice zakresu dat

- **Jira:** SCRUM-6/28. **Priorytet:** P1. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Przejazdy T01–T04; lokalne 24.10.
- **Kroki:** Pobierz [2026-10-24,2026-10-25) oraz odwrócony zakres.
- **Oczekiwany wynik:** Uwzględnione tylko dni i rekordy pasujące do [from,to); odwrócony zakres odrzucony.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-039 — Zmiana czasu wiosenna i jesienna

- **Jira:** SCRUM-6/28. **Priorytet:** P1. **Status:** NOT RUN.
- **Dane / warunki wstępne:** DST-SPRING-2026 i DST-AUTUMN-2026.
- **Kroki:** Porównaj UTC i lokalny zapis, granice dnia.
- **Oczekiwany wynik:** Brak fikcyjnej godziny 02:30 wiosną; dwa odrębne 02:30 jesienią; poprawne offsety.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-040 — Chronologia, stronicowanie, brak geometrii

- **Jira:** SCRUM-6/28. **Priorytet:** P1. **Status:** NOT RUN.
- **Dane / warunki wstępne:** T01–T04, null geometry, page_size=2.
- **Kroki:** Przejdź przez kolejne strony historii i otwórz detal.
- **Oczekiwany wynik:** Kolejność stabilna, brak duplikatów/opuszczeń; brak trasy to jawny brak, nie wymyślony przebieg.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-041 — Brak historii / timeout / awaria

- **Jira:** SCRUM-6/28. **Priorytet:** P1. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Puste trips; 503 lub błąd stubu.
- **Kroki:** Otwórz puste i błędne zakresy.
- **Oczekiwany wynik:** Czytelne i różne stany, bez wycieku szczegółów backendu.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-042 — Cel i opis trwałe po synchronizacji

- **Jira:** SCRUM-62/28. **Priorytet:** P1. **Status:** NOT RUN.
- **Dane / warunki wstępne:** T01 opis; T02 bez celu.
- **Kroki:** Uzupełnij T02; odśwież; powtórz syntetyczny import.
- **Oczekiwany wynik:** Adnotacja zachowana z autorem i czasem, źródłowy dystans/czas niezmieniony.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-043 — Walidacja, anulowanie i błąd zapisu

- **Jira:** SCRUM-62/28. **Priorytet:** P1. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Puste/niedozwolone/długie pola wg zatwierdzonego kontraktu.
- **Kroki:** Zmień adnotację; anuluj; wymuś błąd; ponów odczyt.
- **Oczekiwany wynik:** Niepoprawny zapis odrzucony; poprzednia notatka nie znika; anulowanie bez skutku.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-044 — Konflikt wersji adnotacji

- **Jira:** SCRUM-62/28. **Priorytet:** P1. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Dwie sesje, annotation.version.
- **Kroki:** Edytuj ten sam przejazd z dwóch sesji, zapisz starą wersję.
- **Oczekiwany wynik:** 409 przy konflikcie; bez cichego nadpisania (wymaga potwierdzenia końcowego kontraktu).
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-045 — Suma i brakujące cele w okresie

- **Jira:** SCRUM-62/28. **Priorytet:** P1. **Status:** NOT RUN.
- **Dane / warunki wstępne:** T01–T04 oraz expected_trip_aggregates.
- **Kroki:** Wybierz lokalną datę 2026-10-24.
- **Oczekiwany wynik:** V01=20 km/2 trasy, V02=15 km/1 trasa; razem 35 km/3; T02 bez celu.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-046 — Pola ręczne pojazdu a ponowna synchronizacja

- **Jira:** SCRUM-28/51. **Priorytet:** P1. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Marka/model/rok/VIN/typ syntetyczne.
- **Kroki:** Zapisz pola, wykonaj sync z null, odśwież.
- **Oczekiwany wynik:** Dane ręczne zachowane, walidacja pól, nieznany ID i uprawnienia sprawdzone.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-047 — Kierowcy ręczni i historia przypisania

- **Jira:** SCRUM-42/54/63. **Priorytet:** P1. **Status:** NOT RUN.
- **Dane / warunki wstępne:** DR01/DR02, V01, T01.
- **Kroki:** Przypisz DR01, zmień na DR02 i zasymuluj WEBFLEET sync.
- **Oczekiwany wynik:** Nie importuje kierowcy; przypisania i stare przejazdy nie są nieprawidłowo przepisywane.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

### Sprint 3 — analityka i alerty

#### FF-QA-048 — Suma przejazdów / dni aktywnych

- **Jira:** SCRUM-61/33. **Priorytet:** P2. **Status:** NOT RUN.
- **Dane / warunki wstępne:** T01–T04 i expected_trip_aggregates.
- **Kroki:** Oblicz sumy dla 24.10 na V01/V02 i flocie.
- **Oczekiwany wynik:** V01: 20 km, 2 przejazdy, 1 dzień; V02: 15 km, 1 przejazd, 1 dzień; suma 35 km i 3 przejazdy; rozróżnij unikalny dzień floty (1) od sumy pojazdo-dni (2).
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-049 — Dystans z odcinków licznika, a nie licznika absolutnego

- **Jira:** SCRUM-7/31/33. **Priorytet:** P2. **Status:** NOT RUN.
- **Dane / warunki wstępne:** D01–D05; expected_distance.
- **Kroki:** Przetwórz kolejne pary odczytów <=15 min, w danym dniu lokalnym.
- **Oczekiwany wynik:** V01=20 km (12+8), V02=15 km; partial coverage; pierwszego odczytu nie liczymy jako dystans.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-050 — Nieważny odcinek pomiarowy

- **Jira:** SCRUM-7/31/33. **Priorytet:** P2. **Status:** NOT RUN.
- **Dane / warunki wstępne:** distance_invalid_intervals.
- **Kroki:** Sprawdź brak czasu/licznika, odczyt w przyszłości, cofnięcie, lukę 901 s, duplikat i przejście przez północ.
- **Oczekiwany wynik:** Żaden odrzucony odcinek nie zwiększa DailyDistance ani nie tworzy alertu.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-051 — Poniżej progu / równość / powyżej

- **Jira:** SCRUM-7/33. **Priorytet:** P2. **Status:** NOT RUN.
- **Dane / warunki wstępne:** A01–A03, reguła i świeży czas oceny.
- **Kroki:** Przelicz dla 21.0/20.0/19.0 km.
- **Oczekiwany wynik:** 20<21: brak; 20=20: brak; 20>19: jeden alert.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-052 — Idempotencja alertu

- **Jira:** SCRUM-7/33. **Priorytet:** P2. **Status:** NOT RUN.
- **Dane / warunki wstępne:** A03, reguła+pojazd+dzień.
- **Kroki:** Przelicz ponownie tę samą regułę.
- **Oczekiwany wynik:** Łącznie jeden alert dla tego samego klucza, nie dwa.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-053 — Wyłączona reguła i brak danych

- **Jira:** SCRUM-7/33. **Priorytet:** P2. **Status:** NOT RUN.
- **Dane / warunki wstępne:** A04–A05.
- **Kroki:** Wyłącz regułę, przelicz; użyj pojazdu bez dziennego dystansu.
- **Oczekiwany wynik:** Brak nowych alertów; istniejących nie usuwa; null nie jest udawany jako zero.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-054 — Edycja reguły / granice / dostęp

- **Jira:** SCRUM-7/33. **Priorytet:** P2. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Próg 0/ujemny/NaN/zbyt wiele miejsc, viewer/editor.
- **Kroki:** POST/PATCH reguły, wyłącz, próba zapisu jako viewer.
- **Oczekiwany wynik:** Niepoprawny próg 422; viewer tylko odczyt, editor może edytować; istniejąca historia alertów nie jest usuwana.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-055 — Trwały odczyt alertu na użytkownika

- **Jira:** SCRUM-7/33. **Priorytet:** P2. **Status:** NOT RUN.
- **Dane / warunki wstępne:** A03, U01 i U02.
- **Kroki:** Oznacz read=true dla U01, odśwież; odczytaj jako U02; powtórz read=true.
- **Oczekiwany wynik:** Stan U01 trwały i idempotentny; U02 ma niezależny stan; API wymaga sesji.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

#### FF-QA-056 — Czas i granica doby alertu

- **Jira:** SCRUM-7/33. **Priorytet:** P2. **Status:** NOT RUN.
- **Dane / warunki wstępne:** 2026-10-25T00:30Z i 01:30Z, Warszawa.
- **Kroki:** Oceń dzień zdarzenia na granicy DST; porównaj UTC i event_day.
- **Oczekiwany wynik:** event_day bazuje na Europe/Warsaw, brak fikcyjnego przekroczenia/przejścia dnia.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

### Regresja przekrojowa

#### FF-QA-057 — Spójność przepływu końcowego

- **Jira:** SCRUM-17/63. **Priorytet:** P2. **Status:** NOT RUN.
- **Dane / warunki wstępne:** Fikcyjny użytkownik, V01, T01–T04, A03.
- **Kroki:** Login → mapa → historia → cel → analityka/alert → wylogowanie.
- **Oczekiwany wynik:** Bez utraty danych, poprawne łącza między funkcjami; wykonanie dopiero po wdrożeniu; bez deklaracji PASS teraz.
- **Rzeczywisty wynik / dowód:** do uzupełnienia dopiero przy wykonaniu testu (raport w zadaniu odbiorowym).

## Macierz śledzenia wymagań (ID przypadków)

| Jira | Obszar | Przypadki |
|---|---|---|
| SCRUM-5 | Lista i mapa, filtry, brak GPS, aktualność | FF-QA-011, FF-QA-012, FF-QA-013, FF-QA-014, FF-QA-015, FF-QA-016, FF-QA-017, FF-QA-018, FF-QA-019, FF-QA-020, FF-QA-021, FF-QA-022, FF-QA-023, FF-QA-024, FF-QA-025, FF-QA-026, FF-QA-027 |
| SCRUM-6 | Historia, izolacja, daty, DST | FF-QA-037, FF-QA-038, FF-QA-039, FF-QA-040, FF-QA-041 |
| SCRUM-7 | Reguły, progi, alerty | FF-QA-049, FF-QA-050, FF-QA-051, FF-QA-052, FF-QA-053, FF-QA-054, FF-QA-055, FF-QA-056 |
| SCRUM-62 | Cel i opis przejazdów | FF-QA-042, FF-QA-043, FF-QA-044, FF-QA-045 |
| SCRUM-61 | Agregacje i porównania | FF-QA-048 |
| SCRUM-16 | Logowanie | FF-QA-028, FF-QA-029, FF-QA-030, FF-QA-031, FF-QA-032, FF-QA-033, FF-QA-034 |
| SCRUM-15 | Synchronizacja | — |
| SCRUM-40 | Personalizacja | FF-QA-001, FF-QA-002, FF-QA-003, FF-QA-004, FF-QA-005, FF-QA-006, FF-QA-007, FF-QA-008, FF-QA-009, FF-QA-010 |
| SCRUM-56 | Odbiór logowania | — |
| SCRUM-23 | Odbiór listy i mapy | — |
| SCRUM-28 | Odbiór historii | FF-QA-046 |
| SCRUM-33 | Odbiór alertów | — |
| SCRUM-42 | Kierowcy | FF-QA-047 |
| SCRUM-17 | Regresja | FF-QA-057 |

Ta macierz indeksuje obszary i ich wymagania; przy odbiorze trzeba sprawdzić pełną aktualną listę kryteriów w danej Story. SCRUM-5 ma dodatkowo przypadki dla poszczególnych stanów, SCRUM-6 i SCRUM-7 są uzupełnione przez wydzielone Story SCRUM-62 i SCRUM-61.

## Rejestr wykonania — wzór

| ID | Data i TZ | Środowisko / przeglądarka | SHA | Wynik rzeczywisty | Status | Dowód / Bug / przyczyna BLOCKED |
|---|---|---|---|---|---|---|
| FF-QA-XXX | _do uzupełnienia_ | _do uzupełnienia_ | _do uzupełnienia_ | NOT RUN | _wypełnić po teście_ | _do uzupełnienia_ |

**Wszystkie przypadki obecnie NOT RUN.**
