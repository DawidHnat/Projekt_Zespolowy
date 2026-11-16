# Gotowość do oddania zadań 4.1 i 4.2

Stan odczytu: **16.11.2026**, [SCRUM-143](https://fleet-flow.atlassian.net/browse/SCRUM-143).
Pakiet nie jest jeszcze kompletny. [Polecenia dla agentów zespołu](COURSE_AGENT_HANDOFFS.md).
Do obu oddań wystarczą pełne odebrane przyrosty i wymagane dowody; nie trzeba kończyć całego produktu ani Sprintu 3.

## Dowody potwierdzone

| Wymaganie | Aktualny dowód |
| --- | --- |
| Bieżący serwer i main | Po fetch `c0544d1`; HTTP zawiera to SHA, polecenie z grep -c zwraca 1; HTTPS readiness 200 i status ok. |
| Testy, lint, deploy i smoke | [Run 43948005790](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/43948005790) dla `c0544d1`: wszystkie joby success; log `PASS deployed SHA c0544d1: HTTP status, HTTPS application, API readiness`. |
| Zależności deploymentu | `.github/workflows/ci.yml`: deploy `needs: [required, frontend, backend, e2e, lint]`, smoke `needs: [deploy]`. |
| Autorzy i review | Dokładny filtr tutorialu zwraca 86 scalonych PR. Wszystkie opisy mają klucz Jiry; 4/4 osób ma własny scalony PR i Approved cudzego. |
| Konflikt kodu | [#62](https://github.com/DawidHnat/Projekt_Zespolowy/pull/62) po #30, te same linie TripDayPicker.tsx; zachowane type=button oraz disabled. Aktualny Approved Nazarewicza na f646c82, [CI 42271127635](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/42271127635) success. |
| Czerwony lint | [#77](https://github.com/DawidHnat/Projekt_Zespolowy/pull/77), run 42815387118: Lint failure, deploy/smoke skipped. NIE SCALAĆ. |
| Czerwony test | [#78](https://github.com/DawidHnat/Projekt_Zespolowy/pull/78), run 42815401269: Frontend build failure na npm test, deploy/smoke skipped. NIE SCALAĆ. |
| Odpowiedzialność DoD | [DoD](../DEFINITION_OF_DONE.md): przy wszystkich 12 warunkach jest wykonawca; istnieją joby testów, Lint i Post-deploy smoke oraz odbiory człowieka. Macierz sama nie jest odbiorem Story. |
| Retro S1 i działanie | [Retro S1](retro/sprint-1.md), SCRUM-65 w aktywnym S2. #73 scalony z Approved Dawida i zielonym CI. Pomiar 16.11: 0 zwykłych PR bez pierwszego formalnego review ponad 24 h; dowody #24/#77/#78 liczone osobno. |

| Członek | Własny scalony PR | Approved cudzego na końcowym head |
| --- | --- | --- |
| jczaja51 | #55 | #28 |
| DawidHnat | #60 | #22 |
| jnazarewiczs | #61 | #55 |
| mglowacki0 | #28 | #29 |

## Pozostałe warunki oddania

| Brak | Konkretny następny krok |
| --- | --- |
| Dwa osobne wymagane checki | Aktualny odczyt nadal wypisuje tylko Required CI. Dawid w [SCRUM-140](https://fleet-flow.atlassian.net/browse/SCRUM-140) dodaje Lint i Backend (3.13), zachowując ochronę, a następnie zapisuje odczyt API. Konto jczaja51 ma push, bez admin/maintain. |
| Data ochrony i historia Git | Dawid potwierdza datę; PO rozlicza jawne wyjątki z prowadzącym w SCRUM-143. Poniżej rzeczywisty wynik 3, bez przepisywania historii. |
| Pełne DoD Story S1 | Kandydat SCRUM-16: niezależny review aktualnego auth przez Dawida, końcowe QA Marcela odpowiednich AC i komplet 12 warunków w [SCRUM-141](https://fleet-flow.atlassian.net/browse/SCRUM-141). Rzeczywista dostawa SMTP jest osobnym SCRUM-44, poza czterema AC Story logowania. |
| Pełne DoD Story S2 | Kandydat SCRUM-91, już Testowanie: #93 jest scalony, Approved Dawida na a2f4d61 i [CI 43906895184](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/43906895184) success. Nazarewicz przekazuje funkcję, Marcel odbiera wszystkie AC dwóch kontekstów, konfliktów, izolacji i migracji; Dawid potwierdza potrzebny restore/rollback. SCRUM-84 pozostaje alternatywą wymagającą storage/recovery. |
| Review/retro S2 i aktywny S3 | [SCRUM-142](https://fleet-flow.atlassian.net/browse/SCRUM-142): po pełnym odbiorze rzeczywisty pokaz i feedback, retro, jawne rozliczenie S2 i start istniejącego S3. Brak nowego potwierdzenia odbytych spotkań. Nie wpisujemy ich jako wykonanych. |
| Końcowe odpowiedzi | Każdy odświeża wyniki po ostatnim merge/wdrożeniu i oddaje osobno. Przygotowane dowody są migawką `c0544d1`; także merge dokumentacji wymaga odświeżenia. |

### Wynik kontroli commitów

Dokładny wzorzec kursowy w szerokim zakresie od `2026-10-20T00:00:00+02:00` zwraca **3**, a nie 0. Ta data jest konserwatywnym zakresem audytu; dokładnej chwili ochrony nadal nie potwierdzono.

| Commit | Niezgodny temat |
| --- | --- |
| `a2f4d61` | Fix SCRUM-91 preference E2E flows |
| `1293999` | SCRUM-91: sync account preferences across browsers |
| `2bffba9` | Update Marcel Głowacki's key status in DEV_SERVER.md |

Dwa nowe tematy pochodzą ze scalonego [#93](https://github.com/DawidHnat/Projekt_Zespolowy/pull/93), dawny z [#54](https://github.com/DawidHnat/Projekt_Zespolowy/pull/54). Historyczne gałęzie bez klucza: #1/#2 `codex/azure-dev-server`, #54 `jczaja51-patch-1`. Opisy mają klucz. Poprawienie tytułu PR lub nowy Conventional Commit nie usuwa starych tematów. Nie przesuwamy daty pod wynik i nie przepisujemy chronionego main. Potrzebna jawna decyzja prowadzącego o rozliczeniu wyjątków; przygotowanie pakietu nie jest jej uzyskaniem.

## Sprinty i kolejność

Odczyt 16.11: S1 closed; **FF Sprint 2 - podstawa i QA** (id 3) active; **FF Sprint 3 - dane i konta** (id 4) future. W S3 są SCRUM-128 (proponowane działanie retro, Czaja) i SCRUM-129 (wybite okno, Nazarewicz: frontend/vite.config.ts oraz frontend/src/features/fleet/components/VehicleMap.tsx). Nie trzeba ich kończyć do 4.2; muszą być w rzeczywiście uruchomionym S3, z uzgodnionym działaniem retro.

Najpierw zachować datowany komplet 4.1 z aktywnym S2, pełnym DoD S1 i rozliczeniem wyjątków Git. Następnie odebrać Story S2 i przeprowadzić Review/retro, rozliczyć S2 i uruchomić istniejący S3. Potem zebrać oddzielny komplet 4.2. Nie uruchamiać równoległego sprintu tylko dla zrzutu.

Materiały: [4.1](SPRINT_REVIEW_SUBMISSION.md), [4.2](SPRINT_2_SUBMISSION.md), [Review S2](SPRINT_2_REVIEW.md), [retro S2 — materiał do spotkania](retro/sprint-2.md). Surowe wyniki i szkice osobistych odpowiedzi są lokalne; nie publikujemy eksportów Jiry ani danych prywatnych w repo.
