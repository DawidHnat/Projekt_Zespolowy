# Retrospektywa Sprintu 2 — materiał do spotkania

**Aktualizacja 12.11.2026:** PO ponownie potwierdził, że Review/retro S2
i pełny odbiór całej Story jeszcze się nie odbyły. Organizacja spotkań
i start istniejącego S3: SCRUM-142; pełne DoD: SCRUM-141. Zachowujemy niżej
historyczne obserwacje z 10.11 jako materiał do oceny przez zespół.

Od tego czasu PR #76 trafił do main. Run `43105067278` dla `2b3f2ba`
potwierdza success testów, osobnego lintu, wdrożenia i smoke. HTTP pokazuje
to samo SHA, HTTPS readiness zwraca 200 i JSON `status=ok`. Wymagane checki
ochrony nadal obejmują tylko `Required CI`; dodanie dwóch osobnych checków
pozostaje u Dawida w SCRUM-140. S3 nadal jest przyszły, a SCRUM-128/129 są
w nim zaplanowane. [Aktualne dowody i braki](../COURSE_READINESS.md).

Po spotkaniu dopisać rzeczywistą datę, uczestników, ocenę skutków działań
S1 oraz decyzję o nowych działaniach; niniejszy materiał tego nie zastępuje.

Stan dowodów: **10.11.2026**, Sprint 2 nadal trwa. PO potwierdził, że Review
Sprintu 2 i odbiór przez Marcela całej historyjki jeszcze się nie odbyły.
To przygotowany zapis obserwacji i propozycji do prawdziwej retrospektywy;
nie protokół odbytego spotkania. Po spotkaniu PO dopisuje datę, uczestników,
rzeczywiste decyzje i ocenę efektu działań. Zadanie techniczne:
[SCRUM-127](https://fleet-flow.atlassian.net/browse/SCRUM-127).

## Co poszło dobrze

- Obecny `main` (`5b5fceb`) ma udane CI i wdrożenie
  [42302297975](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/42302297975).
  10.11 publiczny HTTP wskazał tę samą wersję, HTTPS aplikacji oraz readiness
  przeszły kontrolę. To częściowy dowód infrastruktury, nie pełny odbiór Story.
- Odtworzono utratę szkicu opisu przejazdu przez północ i przygotowano poprawkę
  [PR #75](https://github.com/DawidHnat/Projekt_Zespolowy/pull/75).
  CI #75 i zależnego #68 ma po 26 udanych testów przeglądarkowych.
- Są przygotowane poprawki i dowody desktop/mobile dla dashboardu,
  personalizacji i edycji zbiorowej: PR #70, #71 i #72. Każdy nadal wymaga
  właściwego review, kolejności scalenia, wdrożenia i QA.
- W SCRUM-127 powstają jawne bramy `Lint` i `Post-deploy smoke` oraz macierz
  odpowiedzialności DoD. Wyniki PR nie oznaczają jeszcze wykonania na main.

## Co poszło źle

- Wiele zielonych PR-ów oczekuje na review. Zielone CI nie jest odbiorem
  kryteriów ani dowodem gotowej całej historyjki.
- Ochrona `main` wymaga obecnie jednego agregatu `Required CI`; lint jest
  schowany w jobach backendu. Do dwóch osobnych wymaganych checków potrzebna
  jest zmiana właściciela repozytorium. jczaja51 nie ma uprawnień admin.
- Wersja po wdrożeniu była sprawdzana wewnątrz deploymentu, bez osobnego
  joba smoke wymaganego w zadaniu 4.2. Nowa konfiguracja wymaga review i merge.
- Build stale ostrzega o dużym bundlu mapy. Nie należy przyzwyczajać się do
  ostrzeżeń ani wyciszać ich przez podwyższanie limitu.
- Nie ma jeszcze potwierdzenia Review Sprintu 2 ani pełnego QA całej Story.
  Tych dowodów nie da się zastąpić przygotowaną instrukcją.

## Stan działań z retrospektywy Sprintu 1

Źródło: [retro Sprintu 1](sprint-1.md). Statusy opisują dostępne dowody,
nie deklarują decyzji nieodbytej retrospektywy Sprintu 2.

| Działanie i właściciel | Stan na 10.11 i co zostaje |
| --- | --- |
| Codzienne review i pierwsza odpowiedź do 24 h, Jakub Czaja — SCRUM-65 | Rytm został uzgodniony przez zespół. PR #73 zbiera kolejkę i dowody, nadal do review. Pomiar w połowie sprintu i ocena efektu pozostają do wykonania; nie wpisujemy z góry poprawy wyniku. |
| Stan synchronizacji i dostępność infrastruktury, Dawid Hnat — SCRUM-64/84 | Techniczne wydania mają CI, ale końcowy odbiór synchronizacji i recovery wymaga właściwych dowodów w Jirze. Nie uruchamiano żywego WEBFLEET w tym zadaniu. |
| Odbiór listy/mapy i zależności frontendu, Jakub Nazarewicz — SCRUM-5 | Poprawki #69/#67 czekają na review/QA. Nie potwierdzono całego DoD listy i mapy na podstawie tych PR. |
| Pełne QA logowania i plan QA, Marcel Głowacki — SCRUM-56/63 | PR #68 ma zielone CI i pakiet przekazania odbioru. Pozostają niezależny przegląd auth i kontrolowane brakujące scenariusze sesji; dokument nie zastępuje wykonania przez QA. |
| Zebrać feedback i rozliczyć otwarte prace, Jakub Czaja — SCRUM-3/65 | Review Sprintu 1 potwierdzono 06.11. Sprint 1 został zakończony, Sprint 2 jest aktywny. Historyczne uwagi w pliku S1 nie są aktualnym stanem sprintów. Dla S2 potrzebny rzeczywisty protokół i decyzje zespołu. |

## Nowe działania z właścicielami

| Działanie | Właściciel i termin względny | Dowód efektu |
| --- | --- | --- |
| [SCRUM-128](https://fleet-flow.atlassian.net/browse/SCRUM-128): od początku Sprintu 3 prowadzić do odbioru jedną całą Story i mierzyć kolejkę | Jakub Czaja, z QA Marcela i niezależnym reviewerem; wybór w pierwszych 2 dniach S3, ponowny pomiar po 7 dniach | Macierz DoD jednej Story, review aktualnego SHA, CI, wdrożenie i QA; liczba PR-ów bez odpowiedzi >24 h przed i po. Propozycja do zatwierdzenia na retro S2. |
| [SCRUM-129](https://fleet-flow.atlassian.net/browse/SCRUM-129): usunąć „wybite okno” dużego bundla | Jakub Nazarewicz, planowany Sprint 3 | Pomiar przed/po i mały PR dla `frontend/vite.config.ts` / importu Mapbox w `frontend/src/features/fleet/components/VehicleMap.tsx`, bez wyciszania limitu ostrzeżenia; testy i QA. |

Oba zgłoszenia są dodane do **planowanego** `FF Sprint 3 - dane i konta`.
Sprint 3 ma już cel i zakres; nie został uruchomiony przedwcześnie.
Po prawdziwym Review/retro S2 PO rozlicza niedokończone prace, kończy S2
w Jirze i uruchamia S3 z istniejącym celem oraz tymi zgłoszeniami.
