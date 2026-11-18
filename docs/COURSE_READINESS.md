# Gotowość do oddania zadań 3.2 i 4.2

Stan odczytu: **18.11.2026**, [SCRUM-143](https://fleet-flow.atlassian.net/browse/SCRUM-143).
**Oba oddania pozostają niekompletne.** Wystarczą odebrane przyrosty i wymagane dowody;
nie trzeba kończyć całego produktu ani Sprintu 3.

## Numeracja sprawdzona w kursie

| Cursora | Zakres | Instrukcja zespołu |
| --- | --- | --- |
| [Zadanie 3.2](https://cursora.org/pl/courses/projekt-zespolowy?lesson=nowa-lekcja-2-26&step=4) | Przegląd Sprintu i Pull Requesty | [Pakiet 3.2](SPRINT_REVIEW_SUBMISSION.md) |
| Lekcja 4.1 | Teoria Sprintu 2 | Wcześniejsze oznaczenie „oddanie 4.1” było błędne. |
| [Zadanie 4.2](https://cursora.org/pl/courses/projekt-zespolowy?lesson=nowa-lekcja-2-32&step=6) | Przegląd Sprintu 2 i bramy jakości w pipeline | [Pakiet 4.2](SPRINT_2_SUBMISSION.md) |

Numeracja pochodzi z odczytu zalogowanej Cursory 18.11.2026. Historyczne lokalne
pakiety z 12 i 16 listopada mogą jeszcze mieć dawną nazwę; nie są bieżącą instrukcją.

## Dowody potwierdzone

| Wymaganie | Aktualny dowód |
| --- | --- |
| Serwer i main | Po fetch `132fefc`; HTTP zawiera ten skrót, dokładne `grep -c` zwraca 1; HTTPS readiness HTTP 200, `status=ok`. |
| Testy, lint, deploy i smoke | [Run 44176327656](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/44176327656): 10/10 jobów success; `PASS deployed SHA 132fefc: HTTP status, HTTPS application, API readiness`. |
| Zależności wdrożenia | `.github/workflows/ci.yml`: deploy `needs: [required, frontend, backend, e2e, lint]`, smoke `needs: [deploy]`. |
| Autorzy i review | Dokładny filtr tutorialu zwraca 88 scalonych PR, wszystkie `key_in_body=true`. Zachowane dowody 4/4 osób poniżej. Filtr sam nie sprawdza aktualności Approved. |
| Konflikt kodu | [#62](https://github.com/DawidHnat/Projekt_Zespolowy/pull/62) po #30, wspólne linie TripDayPicker.tsx; zachowane `type=button` i `disabled`, Approved Nazarewicza na `f646c82`, [CI 42271127635](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/42271127635) success. |
| Czerwony lint | [#77](https://github.com/DawidHnat/Projekt_Zespolowy/pull/77), run 42815387118: Lint failure, deploy/smoke skipped. NIE SCALAĆ. |
| Czerwony test | [#78](https://github.com/DawidHnat/Projekt_Zespolowy/pull/78), run 42815401269: Frontend build failure na npm test, deploy/smoke skipped. NIE SCALAĆ. |
| DoD | [DoD](../DEFINITION_OF_DONE.md) ma 12 warunków z wykonawcą. [Macierz ASVS](security/SCRUM-101-ASVS-5.0.0-L2.md) jest na main po #98; nie zastępuje pełnego review auth ani odbioru Story. |
| Retro S1 | [Retro S1](retro/sprint-1.md), SCRUM-65 w aktywnym S2. #73 scalony z Approved i CI. Pomiar z 16.11: 0 zwykłych PR bez formalnego review ponad 24 h, z osobnym wyłączeniem dowodów #24/#77/#78. Nie jest to nowy pomiar z 18.11. |

| Członek | Własny scalony PR | Approved cudzego na końcowym head |
| --- | --- | --- |
| jczaja51 | #55 | #28 |
| DawidHnat | #60 | #22 |
| jnazarewiczs | #61 | #55 |
| mglowacki0 | #28 | #29 |

## Co jeszcze blokuje oddanie

| Zadanie / właściciel | Wykonane i pozostały krok |
| --- | --- |
| [SCRUM-140](https://fleet-flow.atlassian.net/browse/SCRUM-140), Dawid | Wymagany nadal tylko `Required CI`; ruleset nie zwrócił dodatkowych kontekstów. Dodać osobno wymagane `Lint` i `Backend (3.13)`, zachować zabezpieczenia i przedstawić nowy odczyt. Potwierdzić rzeczywistą datę ochrony. |
| [SCRUM-141 / S1](https://fleet-flow.atlassian.net/browse/SCRUM-141?focusedCommentId=10254), Dawid i Marcel, decyzja PO | Kandydat SCRUM-16 ma macierz 4 AC + 12 DoD. Kontrolowane expiry FF-QA-031: 2/2 PASS desktop/mobile. Pozostają całościowy niezależny review auth, końcowe cookie/Origin i odpowiednie retesty, wymagane dowody odtworzenia, pełny odbiór i decyzja PO. SMTP live jest osobnym SCRUM-44, poza czterema AC logowania. |
| [SCRUM-141 / S2](https://fleet-flow.atlassian.net/browse/SCRUM-141?focusedCommentId=10255), Nazarewicz, Dawid i Marcel, decyzja PO | SCRUM-91 nadal Testowanie. Poprawki SCRUM-144/145/146 są w otwartym [draft #99](https://github.com/DawidHnat/Projekt_Zespolowy/pull/99). Potrzebne ukończenie PR, CI, cudze review, merge/wdrożenie, retest dwóch kont i kontekstów, migracji i regresji oraz restore/rollback migracji 0006. |
| [Aktualizacja QA S2](https://fleet-flow.atlassian.net/browse/SCRUM-141?focusedCommentId=10287), Marcel | Offline z błędem i ochroną szkicu już PASS w opisanym zakresie. Brak osobnego potwierdzenia niezmienionej wartości backendu; nie daje to PASS całego AC3 ani Story. Nie powtarzać starego stwierdzenia, że próby Offline w ogóle nie wykonano. |
| [SCRUM-142](https://fleet-flow.atlassian.net/browse/SCRUM-142), PO i zespół | Po pełnym odbiorze S2 przeprowadzić Review/retro, zapisać datę, uczestników, feedback, ocenę działań S1 i nowe uzgodnione działanie. Rozliczyć S2 i uruchomić istniejący S3. Brak nowego potwierdzenia spotkań. |
| [SCRUM-143](https://fleet-flow.atlassian.net/browse/SCRUM-143), PO | Rozliczyć historyczne wyjątki z prowadzącym, dokończyć review/merge dokumentacji i po ostatnim wdrożeniu odświeżyć wyniki. |

## Historia Git

Dokładny wzorzec w szerokim zakresie od `2026-10-20T00:00:00+02:00` nadal zwraca
**3**, a nie 0. To zakres kontrolny, nie potwierdzona data ochrony.

| Commit | Niezgodny temat |
| --- | --- |
| `a2f4d61` | Fix SCRUM-91 preference E2E flows |
| `1293999` | SCRUM-91: sync account preferences across browsers |
| `2bffba9` | Update Marcel Głowacki's key status in DEV_SERVER.md |

Dwa tematy pochodzą z [#93](https://github.com/DawidHnat/Projekt_Zespolowy/pull/93),
jeden z [#54](https://github.com/DawidHnat/Projekt_Zespolowy/pull/54).
Gałęzie bez klucza: #1/#2 `codex/azure-dev-server`, #54 `jczaja51-patch-1`.
Potrzebne potwierdzenie daty i jawna decyzja prowadzącego o wyjątkach.
Nowy commit lub tytuł PR nie usuwa dawnych tematów; historii main nie przepisujemy.

## Sprinty i kolejność

Odczyt 18.11: S1 closed; **FF Sprint 2 - podstawa i QA** (id 3) active;
**FF Sprint 3 - dane i konta** (id 4) future. W S3 są SCRUM-128 (proponowane
działanie retro, Czaja) i SCRUM-129 (wybite okno, Nazarewicz:
`frontend/vite.config.ts`, `frontend/src/features/fleet/components/VehicleMap.tsx`).
Nie trzeba kończyć tych zadań do 4.2; muszą należeć do rzeczywiście aktywnego S3,
a działanie ma wynikać z uzgodnionej retrospektywy.

Najpierw zachować kompletny datowany pakiet **3.2** z aktywnym S2, pełnym DoD S1
i rozliczeniem Git. Następnie odebrać Story S2, przeprowadzić Review/retro,
rozliczyć S2 i uruchomić istniejący S3. Potem zebrać oddzielny komplet **4.2**.
Każdy oddaje osobno pod własnym kontem; szkic nie zastępuje spotkań.

Materiały: [3.2](SPRINT_REVIEW_SUBMISSION.md), [4.2](SPRINT_2_SUBMISSION.md),
[Review S2](SPRINT_2_REVIEW.md), [retro S2](retro/sprint-2.md),
[polecenia dla zespołu](COURSE_AGENT_HANDOFFS.md). Surowe wyniki i osobiste szkice
pozostają lokalne, poza publicznym repozytorium.
