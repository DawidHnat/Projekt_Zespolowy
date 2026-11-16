# Gotowość do oddania zadań 4.1 i 4.2

Stan audytu: **12.11.2026**, zadanie [SCRUM-143](https://fleet-flow.atlassian.net/browse/SCRUM-143).
To rejestr dowodów i braków, nie potwierdzenie zaliczenia. Ukończenie wszystkich
zadań sprintu nie zastępuje wymaganych poleceń, pełnego DoD ani spotkań.
Do tych dwóch zadań nie trzeba kończyć całego produktu ani całego Sprintu 3.

## Co jest już potwierdzone

| Wymaganie | Rzeczywisty dowód |
| --- | --- |
| Wdrożony aktualny main | Po fetch `2b3f2ba`; HTTP `http://57.129.179.53/` zawiera ten SHA. `https://fleet-flow.pl/api/health/ready` zwraca HTTP 200 i `{"status":"ok"}`. |
| CI, lint, wdrożenie i test po wdrożeniu | [Run main 43105067278](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/43105067278): wszystkie joby success. Log: `PASS deployed SHA 2b3f2ba: HTTP status, HTTPS application, API readiness`. |
| Wdrożenie zależy od testów i lintu | `.github/workflows/ci.yml`: deploy `needs: [required, frontend, backend, e2e, lint]`; smoke `needs: [deploy]`. |
| Autorstwo i review czterech osób | 67 scalonych PR; wszystkie mają klucz Jiry w opisie. Każdy członek ma własny scalony PR i wykonane review cudzego. Przykłady poniżej. |
| Rozwiązany konflikt kodu | Scalony [PR #62](https://github.com/DawidHnat/Projekt_Zespolowy/pull/62), po wcześniejszym #30; `TripDayPicker.tsx`, zachowane `type="button"` i `disabled={disabled}`. CI ostatniego head `f646c82` zielone, [run 42271127635](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/42271127635). |
| Celowo czerwony lint | [PR #77 — NIE SCALAĆ](https://github.com/DawidHnat/Projekt_Zespolowy/pull/77), run `42815387118`: `Lint failure`, deployment i smoke skipped. |
| Celowo czerwony test | [PR #78 — NIE SCALAĆ](https://github.com/DawidHnat/Projekt_Zespolowy/pull/78), run `42815401269`: `Frontend build failure` na npm test, deployment i smoke skipped. |
| Macierz DoD | [DEFINITION_OF_DONE.md](../DEFINITION_OF_DONE.md) ma odpowiedzialność przy każdym warunku; testy, lint i smoke istnieją już na main. |
| Retro S1 i działanie w S2 | [Retro S1](retro/sprint-1.md), działanie SCRUM-65; Sprint 1 closed, Sprint 2 active. Review S1 z 06.11 jest potwierdzone przez PO. |
| Przygotowane następne usprawnienia | SCRUM-128 i SCRUM-129 są w przyszłym Sprincie 3, który ma cel. Planowany sprint nie spełnia jeszcze warunku „trwa Sprint 3”. |

| Członek | Przykład własnego scalonego PR | Przykład review cudzego scalonego PR |
| --- | --- | --- |
| Jakub Czaja — `jczaja51` | #63 | #64 APPROVED |
| Dawid Hnat — `DawidHnat` | #60 | #76 APPROVED |
| Jakub Nazarewicz — `jnazarewiczs` | #64 | #62 APPROVED |
| Marcel Głowacki — `mglowacki0` | #28 | #63 APPROVED |

## Co blokuje kompletne oddanie

| Brak | Kto i gdzie go domyka |
| --- | --- |
| Ochrona wymaga tylko `Required CI`; brakuje osobno wymaganego testu i lintu. | Dawid: [SCRUM-140](https://fleet-flow.atlassian.net/browse/SCRUM-140), podzadanie SCRUM-127. Dodać `Backend (3.13)` i `Lint`, zachować dotychczasową ochronę, nazwy i brak bypass. |
| Brak potwierdzonej dokładnej daty ochrony i niezgodności historyczne. | Dawid podaje datę w SCRUM-140. Jakub: SCRUM-143, wyjaśnia rozliczenie z prowadzącym. Szczegóły poniżej. |
| Brak kompletnego dowodu pełnego DoD całej Story S1 i S2. | Marcel z PO i niezależnym reviewerem: [SCRUM-141](https://fleet-flow.atlassian.net/browse/SCRUM-141). Wykorzystać istniejące QA, nie powielać testów ani nie utożsamiać statusu Gotowe z odbiorem. |
| Brak Review/retro S2, rozliczenia i startu S3. | Jakub i zespół: [SCRUM-142](https://fleet-flow.atlassian.net/browse/SCRUM-142), po SCRUM-141. PO potwierdził 12.11, że spotkania jeszcze się nie odbyły. |
| Brak finalnych odpowiedzi po ostatnim merge/wdrożeniu. | Jakub: SCRUM-143; każdy członek wykonuje końcowe polecenia i oddaje osobno. |

SCRUM-140 blokuje SCRUM-143; SCRUM-141 blokuje SCRUM-142, a SCRUM-142 blokuje
SCRUM-143. Techniczne przygotowanie nie pozwala zamknąć tych zależności za zespół.

### Historia Git — wynik nie jest równy zero

Kontrola z dokładnym wzorcem kursowym w szerszym zakresie od
`2026-10-20T00:00:00+02:00` zwraca **1**. Niezgodny temat:

```text
2bffba97550d6addf02dd0ef17bb09cf070f7fbf
Update Marcel Głowacki's key status in DEV_SERVER.md
```

Commit trafił do main przez [PR #54](https://github.com/DawidHnat/Projekt_Zespolowy/pull/54).
Gałęzie bez klucza Jiry w wyniku filtra: #1/#2 `codex/azure-dev-server`
i #54 `jczaja51-patch-1`. Opisy tych PR zawierają klucz.
Dokładną datę ochrony nadal potwierdza Dawid. Nie przesuwamy daty pod wynik,
nie przepisujemy main ani historycznych autorów i nie przedstawiamy `1` jako `0`.
Te historyczne wyjątki wymagają jawnego rozliczenia z prowadzącym; poprawna
nazwa następnej gałęzi i nowy commit nie zmieniają starych wyników.

### Wybór Story Sprintu 2

Odczyt `sprint = 3 AND issuetype = Story` zwraca wyłącznie:

- **SCRUM-84 — kopie poza VPS**, Dawid, Do zrobienia. Pełne DoD wymaga
  uzgodnionego storage/kosztu/RPO/RTO oraz niezależnego odtworzenia. Istniejąca
  decyzja odkłada wybór storage; sam kod backupu nie jest pełnym odbiorem.
- **SCRUM-91 — preferencje konta między urządzeniami**, Nazarewicz,
  Do zrobienia. Wymagane backendowe preferencje, dwa urządzenia, izolacja kont,
  konflikt wersji i jawna migracja ustawień lokalnych.

PO wybiera rzeczywisty wykonalny przyrost z zespołem. SCRUM-38/45/46 oraz
SCRUM-127 są Zadaniami; nie zamieniamy ich w Story dla wyniku kursowego.
SCRUM-83 ma lokalne QA Marcela, ale należy do zamkniętego Sprintu 1.

## Materiały do użycia

### Kolejność dwóch oddań

1. **Podczas aktywnego Sprintu 2** domknąć DoD Story S1 i rozliczenie historii
   Git, zebrać komplet 4.1 z datowanym odczytem aktywnego S2 i jego celem.
   Zachować tę migawkę przed zamknięciem S2; nie zastępować jej późniejszym
   twierdzeniem, że zamknięty sprint nadal trwa.
2. Domknąć DoD Story S2, wymagane checki oraz prawdziwe Review/retro S2.
   Przed rozliczeniem sprintu sprawdzić, czy komplet 4.1 jest już zapisany.
3. Rozliczyć S2 i uruchomić istniejący S3. Zebrać komplet 4.2 z nowym odczytem
   aktywnego S3 oraz świeżym main/runem/wersją serwera. Pierwsze i drugie
   oddanie opisują kolejne etapy, nie dwa równolegle aktywne sprinty.

- [Polecenia i dowody 4.1](SPRINT_REVIEW_SUBMISSION.md).
- [Polecenia i dowody 4.2](SPRINT_2_SUBMISSION.md).
- [Review S1](SPRINT_1_REVIEW.md), [scenariusz i protokół S2](SPRINT_2_REVIEW.md).
- [Retro S1](retro/sprint-1.md), [materiał na retro S2](retro/sprint-2.md).

Surowe odczyty audytu są lokalne. Do publicznego repo nie dodajemy eksportów
Jiry, logów z danymi floty, sekretów ani danych klientów. Wyniki wersji i runu
trzeba odświeżyć po każdym kolejnym wdrożeniu.
