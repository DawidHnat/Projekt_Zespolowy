# SCRUM-133 — bieżący rejestr integracji

Bazowy odczyt **19.11.2026**, agent Codex na polecenie **Jakuba Czai (jczaja51)**. Main `cb634da0ece8cd93424bfc16a5185cf817a0cbb1`. Środowisko: izolowany checkout, GitHub/Jira oraz publiczne HTTP/HTTPS/readiness; bez rekordów floty.

**Stan integracji: #101 i #110 pozostają otwarte i wymagają niezależnego review.** Narzędzia backupu są w `main` (`70a38db`) po scaleniu #105 o 20:22 czasu polskiego. Uruchomienie backupu off-site i odbiór SCRUM-84 pozostają w Sprincie 5 (id 37). [PR #105](https://github.com/DawidHnat/Projekt_Zespolowy/pull/105)

Reguła Jira ustawiła SCRUM-133 na **Gotowe** po scaleniu #105. Jakub przywrócił **W toku** o 20:24. [SCRUM-133](https://fleet-flow.atlassian.net/browse/SCRUM-133)

JSON dowodów zawiera stany z bazowego odczytu oraz `follow_up` ze scaleniem #105. Dotychczasowe wyniki CI, wdrożenia i QA zachowują daty oraz SHA sprawdzonych wersji. [JSON dowodów](SCRUM-133-evidence.json)

## Wszystkie 12 zakresów i dodatkowy #79

| Źródło / Jira | Integracja / head | Dostarczenie | Dowód zachowania i pozostały odbiór |
| --- | --- | --- | --- |
| [#35](https://github.com/DawidHnat/Projekt_Zespolowy/pull/35) / [SCRUM-84](https://fleet-flow.atlassian.net/browse/SCRUM-84) | [#105](https://github.com/DawidHnat/Projekt_Zespolowy/pull/105) / `90f8832` | DELIVERED_TO_MAIN | Narzędzia i timery w `main` od `70a38db`. CI PR przeszło. Uruchomienie storage i timerów oraz operacyjny odbiór pozostają w Sprint 5. |
| [#36](https://github.com/DawidHnat/Projekt_Zespolowy/pull/36) / [SCRUM-64](https://fleet-flow.atlassian.net/browse/SCRUM-64) | [#107](https://github.com/DawidHnat/Projekt_Zespolowy/pull/107) / `f794b8d` | DELIVERED_TO_MAIN | app/sync_control.py oraz bezpieczne zdarzenia workera są w main przez #107. Odbiór kontrolowanego live SCRUM-64 jest odrębny. |
| [#38](https://github.com/DawidHnat/Projekt_Zespolowy/pull/38) / [SCRUM-97](https://fleet-flow.atlassian.net/browse/SCRUM-97) | [#103](https://github.com/DawidHnat/Projekt_Zespolowy/pull/103) / `b897dc6` | DELIVERED_TO_MAIN | Paginacja SQL, prywatne indeksy wyszukiwania i migracja 0008 są w main przez #103. Zachowano speed_kmh w serializacji. |
| [#40](https://github.com/DawidHnat/Projekt_Zespolowy/pull/40) / [SCRUM-95](https://fleet-flow.atlassian.net/browse/SCRUM-95) | [#101](https://github.com/DawidHnat/Projekt_Zespolowy/pull/101) / `a8476ac` | PENDING | Skany są w #101/a8476ac, ale nie w main. Pełny aktualny CI 44487974169 PASS; wymagane nowe review Dawida i rollout/rollback obrazu. |
| [#43](https://github.com/DawidHnat/Projekt_Zespolowy/pull/43) / [SCRUM-107](https://fleet-flow.atlassian.net/browse/SCRUM-107) | [#106](https://github.com/DawidHnat/Projekt_Zespolowy/pull/106) / `7d3852a` | DELIVERED_TO_MAIN | Axe i regresje fokusu są w main przez #106, łącznie z zależnym UX #108. To nie deklaracja pełnego ręcznego QA. |
| [#44](https://github.com/DawidHnat/Projekt_Zespolowy/pull/44) / [SCRUM-96](https://fleet-flow.atlassian.net/browse/SCRUM-96) | [#100](https://github.com/DawidHnat/Projekt_Zespolowy/pull/100) / `6edc12a` | DELIVERED_TO_MAIN | Edge/Caddy/trusted proxy oraz test prawdziwego Caddy są w main przez #100. |
| [#45](https://github.com/DawidHnat/Projekt_Zespolowy/pull/45) / [SCRUM-108](https://fleet-flow.atlassian.net/browse/SCRUM-108) | [#102](https://github.com/DawidHnat/Projekt_Zespolowy/pull/102) / `d13850b` | DELIVERED_TO_MAIN | Generator, wygenerowane typy i testy kontraktów są w main przez #102. Bieżący main-run PASS; historyczne canceled/failure nie są przepisywane na PASS. |
| [#47](https://github.com/DawidHnat/Projekt_Zespolowy/pull/47) / [SCRUM-105](https://fleet-flow.atlassian.net/browse/SCRUM-105) | [#108](https://github.com/DawidHnat/Projekt_Zespolowy/pull/108) / `bf7e7cb` | DELIVERED_TO_MAIN | UX modułów i lokalnych danych jest w main przez #108 → #106. |
| [#48](https://github.com/DawidHnat/Projekt_Zespolowy/pull/48) / [SCRUM-103](https://fleet-flow.atlassian.net/browse/SCRUM-103) | [#104](https://github.com/DawidHnat/Projekt_Zespolowy/pull/104) / `ec02780` | DELIVERED_TO_MAIN | Constraint ról, blokada publicznych docs i migracja 0009 są w main przez #104 → #103. |
| [#49](https://github.com/DawidHnat/Projekt_Zespolowy/pull/49) / [SCRUM-32](https://fleet-flow.atlassian.net/browse/SCRUM-32) | [#109](https://github.com/DawidHnat/Projekt_Zespolowy/pull/109) / `b39607c` | PENDING | UI alertów z #109 scalono wyłącznie do zależności; kod czeka na #110/be609d7 i QA SCRUM-33. |
| [#50](https://github.com/DawidHnat/Projekt_Zespolowy/pull/50) / [SCRUM-52](https://fleet-flow.atlassian.net/browse/SCRUM-52) | [#110](https://github.com/DawidHnat/Projekt_Zespolowy/pull/110) / `be609d7` | PENDING | API ręcznych kierowców i migracja 0010 są w #110/be609d7; brak w main. QA SCRUM-54 oraz odbiór operatora migracji/rollbacku oczekują. |
| [#51](https://github.com/DawidHnat/Projekt_Zespolowy/pull/51) / [SCRUM-53](https://fleet-flow.atlassian.net/browse/SCRUM-53) | [#111](https://github.com/DawidHnat/Projekt_Zespolowy/pull/111) / `caf3ccd` | PENDING | UI kierowców z #111 scalono tylko do #110; brak w main. Pełny diff #110 obejmuje #109 i #111; QA SCRUM-54. |

#79 jest **DELIVERED_TO_MAIN przez #53**: merge `a739d68` jest przodkiem main. Własnego nieistniejącego Approved #79 nie dopisano; dowód review ścieżki #53 pozostaje w GitHub.

## Jedna kolejka: #101 → #110

Poniższe SHA i wyniki opisują bazowy odczyt. Wyniki nowych commitów są w kartach Checks obu PR-ów.

1. **#101, `a8476ac`**: dołączono aktualny main bez konfliktów. [CI 44487974169](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/44487974169): wszystkie wymagane testy i skanery PASS, deploy/smoke PR SKIPPED. Logi potwierdzają faktyczne npm/pip, Semgrep, Gitleaks i Trivy; ostrzeżenie npm z 17.11 jest historyczne. Lokalnie agent 19.11: Ruff check/format PASS, 255 pytest PostgreSQL PASS, 58 npm test/build PASS, generator kontraktów i 3 testy wyjątku tekstowego PASS. Progi i ochrona zachowane. **Dawid Hnat** ma wykonać aktualne review całego head, w tym istniejącego ograniczonego fingerprintu Gitleaks i rollout/rollback obrazu. Stare reviews są DISMISSED. Dopiero po komplecie bramek zwykły merge, deploy i smoke.
2. **#110, `be609d7`**: pozostawiono bez aktualizacji do czasu dostarczenia #101. [CI 44414413143](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/44414413143) PASS dla obecnego head. Diff zawiera API/UI ręcznych kierowców, kategorie/przypisania, alerty #109 i UI #111. `0010_manual_drivers` następuje po 0009; waliduje legacy i blokuje stratny downgrade. Po #101: aktualizacja wyłącznie tego PR, testy/CI i nowe niezależne review Dawida/Nazarewicza; obecne reviews DISMISSED. QA: **Marcel**, [SCRUM-54](https://fleet-flow.atlassian.net/browse/SCRUM-54) i [SCRUM-33](https://fleet-flow.atlassian.net/browse/SCRUM-33). Operator odbiera migrację/rollback; merge nie zamyka całych Story.

## Wdrożenie i warunki zakończenia

[Main CI/deploy/smoke 44386951054](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/44386951054) **PASS** dla `cb634da`; odczyt agenta 19.11 potwierdził to samo SHA HTTP/HTTPS oraz readiness **200 / status ok** z poprawną walidacją TLS. To stan dostarczonych zakresów; otwartych #101/#110 nie wdrożono.

133 kończymy po dostarczeniu nieodłożonych zakresów z aktualnym review, CI, adekwatnym QA i dowodem wdrożenia. Kontrolowany live odbiera osobno Dawid w SCRUM-64 na jego własnych AC i dotychczasowych kopiach/rollbacku SCRUM-18; **zakończenie odłożonego SCRUM-84 nie jest blokadą**. Nie uruchomiono żywego WEBFLEET/SMTP, nie zmieniano ochrony ani konfiguracji VPS i nie włączono automerge.

Każdy nowy wynik: wykonawca (agent/człowiek), data, SHA, środowisko, dowód i PASS/FAIL/BLOCKED. Brak niezależnego QA ma konkretną rolę i nie jest naprawiany samą zmianą statusu.
