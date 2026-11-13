# Przegląd Sprintu i Pull Requesty — oddanie 4.1

Stan sprawdzony **12.11.2026**. Koordynacja:
[SCRUM-143](https://fleet-flow.atlassian.net/browse/SCRUM-143).
[Macierz obu zadań i właściciele braków](COURSE_READINESS.md).
To materiał do dokończenia: pełne DoD i historia Git nadal wymagają rozliczenia.

## 1. Serwer i ostatni main

Aplikacja: <https://fleet-flow.pl/>. Strona wersji do polecenia:
<http://57.129.179.53/>. W klonie zespołu, po ostatnim wdrożeniu:

```bash
git fetch && curl -s http://57.129.179.53/ | grep "$(git rev-parse --short=7 origin/main)"
curl -fsS https://fleet-flow.pl/api/health/ready
```

12.11 fetch wskazał `2b3f2ba`, znaleziony HTML zawierał
`<code data-build-sha="2b3f2ba">2b3f2ba</code>`, readiness zwróciło HTTP 200
i `{"status":"ok"}`. [Run 43105067278](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/43105067278)
ma sukces testów, lintu, deploymentu i smoke. To dowód wersji; nie zastępuje
pełnego odbioru Story z [SCRUM-141](https://fleet-flow.atlassian.net/browse/SCRUM-141).

## 2. Dokładny filtr autorów, review i gałęzi

Filtr z kroku 6 tutorialu, dostarczony 29.10.2026:

```bash
gh pr list --state merged --limit 100 --json number,headRefName,author,reviews,body \
  --jq '.[] | .author.login as $a | "#\(.number) \(.headRefName) author=\($a) reviewers=\([.reviews[].author.login] | unique | map(select(. != $a)) | join(",")) key_in_body=\(.body | test("[A-Z]+-[0-9]+"))"'
```

Odczyt 12.11: 67 scalonych PR, wszystkie `key_in_body=true`. Każdy członek
jest autorem i recenzentem cudzego scalonego PR:

| Login | Autor | Cudze review |
| --- | --- | --- |
| jczaja51 | #63 | #64 APPROVED |
| DawidHnat | #60 | #76 APPROVED |
| jnazarewiczs | #64 | #62 APPROVED |
| mglowacki0 | #28 | #63 APPROVED |

Do własnej odpowiedzi wkleić pełny rzeczywisty wynik filtra, nie tylko tę
tabelę. Filtr sam nie sprawdza aktualności ani stanu Approved — to osobny
warunek DoD. Dawnych PR bez approval nie przedstawiamy jako przejrzanych.

**Niezgodne historyczne gałęzie:** #1/#2 `codex/azure-dev-server` oraz
#54 `jczaja51-patch-1`. Ukończenie bieżących zadań nie zmieni tych nazw.
Rozliczenie wyjątków: SCRUM-143, z prowadzącym.

## 3. Conventional Commits i data ochrony

Dawid potwierdza dokładną datę/godzinę w
[SCRUM-140](https://fleet-flow.atlassian.net/browse/SCRUM-140).
Test `23dd927` był jeszcze przyjęty, późniejszy `be4bc42` odrzucony;
nie wyprowadzamy dokładnej godziny z daty pliku konfiguracji.

```bash
git fetch
git log --no-merges --since="<potwierdzona data włączenia ochrony>" --format=%s origin/main | grep -vcE '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|breaking)(\([^)]+\))?!?: .+'
```

W konserwatywnym zakresie od `2026-10-20T00:00:00+02:00` wynik wynosi **1**,
nie 0. Temat `2bffba9` z PR #54 to
`Update Marcel Głowacki's key status in DEV_SERVER.md`.
Nie podstawiać innej daty dla uzyskania zera i nie przepisywać main.
Wymagany sposób rozliczenia historycznego naruszenia pozostaje do uzgodnienia
z prowadzącym. Przy wyniku 0 grep może zwrócić kod 1; oceniamy także wynik,
nie sam kod wyjścia.

## 4. Gotowy dowód konfliktu

**[PR #62](https://github.com/DawidHnat/Projekt_Zespolowy/pull/62)** jest scalony
i ma APPROVED Nazarewicza dla ostatniego head `f646c82`.
Wcześniejszy PR #30 był już scalony do main. Dwie zmiany tych samych linii
`frontend/src/features/trips/components/TripDayPicker.tsx` powodowały konflikt
między `type="button"` a `disabled={disabled}`. Ręczne rozwiązanie zachowało oba:
skróty dat nie wysyłają formularza i respektują blokadę niezapisanego szkicu.
Opis PR zawiera przyczynę, znaczniki konfliktu, rodziców merge i walidację.

[CI 42271127635](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/42271127635)
dotyczy dokładnie ostatniego head `f646c82d1e0b35188cfe8d16ab1b9220860a61a7`;
wszystkie kontrole PR mają success, deployment jest prawidłowo skipped.
To istniejący dowód — nie trzeba tworzyć kolejnego sztucznego konfliktu.

## 5. Przyrost, retro i Sprint 2

Review S1 odbyło się 06.11, z udziałem całego zespołu i pozytywnym ogólnym
feedbackiem potwierdzonym przez PO. [Protokół](SPRINT_1_REVIEW.md) nie deklaruje
nieznanego SHA pokazu ani brakujących wyników QA.
[Retro S1](retro/sprint-1.md) ma trzy części i działanie
[SCRUM-65](https://fleet-flow.atlassian.net/browse/SCRUM-65).
Sprint 1 zakończono 09.11.2026; Sprint 2 jest aktywny.

**Nazwa:** `FF Sprint 2 - podstawa i QA` (id 3).
**Cel z Jiry, odczyt 12.11.2026:**

> Domknąć istniejący kod i odbiór floty/UI, źródłowe pola WEBFLEET, podstawową kartotekę, backup/odtworzenie i synchronizację. Równolegle preferencje konta oraz decyzje prywatności i macierz bezpieczeństwa. Bieżącą dostępność i pozostały wysiłek zespół aktualizuje podczas Planningu; historyczne SCRUM-4 jest zakończone. Priorytet: review/QA i usunięcie blokad przed nowymi funkcjami. SCRUM-64 wymaga odebranego SCRUM-84 i wymaganych decyzji. Założenie PO: 10–15 h/osobę/tydzień, z review i QA; dostępność i pozostały wysiłek potwierdzają wykonawcy. SP są istniejącą wyceną pełnego zakresu, nie pozostałymi godzinami. Nie sumować punktów rodzica i podzadań.

Pełne DoD jednej Story S1 nadal wymaga kompletu dowodów w SCRUM-141.
Administracyjne Gotowe SCRUM-16 nie zastępuje tego odbioru.

## Zebranie lokalnego pakietu

`tools/collect_sprint_evidence.py` zapisuje surowe wyniki do nowego ignorowanego
katalogu `.local/sprint-evidence/`. Bez potwierdzonej daty ochrony ma zakończyć
się jako NIEKOMPLETNE. [PR #87](https://github.com/DawidHnat/Projekt_Zespolowy/pull/87)
naprawia kontrolę readiness; przed jego scaleniem używać kanonicznego endpointu
i osobno wymagać HTTP 200 oraz JSON `status=ok`. Stary hostname zwraca 308,
a samo curl exit 0 nie potwierdza gotowości API.

Po spełnieniu braków każdy odświeża wyniki i oddaje osobno: serwer/HTML,
pełny filtr PR, wynik kontroli commitów, link #62, retro S1 oraz nazwę i cel S2.
