# Backlog, prototyp i pipeline — odbiór zadania

Stan przygotowania na 20 października 2026. Ten dokument oddziela gotowe
artefakty od dowodów, które trzeba zebrać po włączeniu ochrony i scaleniu PR.

## Linki do odpowiedzi

| Element | Adres |
| --- | --- |
| Repozytorium | https://github.com/DawidHnat/Projekt_Zespolowy |
| Prototyp w trybie prezentacji | https://www.figma.com/proto/4EFjRAUbCoTjemZpQRVDu9?node-id=2-46&starting-point-node-id=2%3A46&scaling=scale-down |
| Plik Figmy do udostępnienia | https://www.figma.com/design/4EFjRAUbCoTjemZpQRVDu9 |
| Backlog Jira | https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1/backlog |
| Serwer: aplikacja HTTPS | https://vps-9171bf52.vps.ovh.net/ |
| Serwer: strona wersji HTTP do polecenia z zadania | http://57.129.179.53/ |
| PR z celowo zepsutą budową | [#24 — nie scalać](https://github.com/DawidHnat/Projekt_Zespolowy/pull/24) |

Każdy członek zespołu oddaje własną odpowiedź. Do linków trzeba dołączyć
rzeczywiste wyniki dwóch poleceń opisanych poniżej oraz zapewnić prowadzącemu
dostęp do repozytorium, Figmy i Jiry.

## Przygotowane artefakty

- Jira ma osiem uporządkowanych Story MVP z opisem Jako/chcę/aby,
  kryteriami akceptacji i oszacowaniami ze skali 1, 2, 3, 5, 8.
  [Lista i zakres Story](MVP_BACKLOG.md).
- Aktywny Sprint 1 ma cel i trzy Story: SCRUM-16, SCRUM-15 i SCRUM-5.
  Każda zawiera link do swojego przepływu Figmy.
- Prototyp ma 18 edytowalnych ekranów i trzy nazwane przepływy Sprintu 1.
  [Scenariusze przeglądu](PROTOTYPE.md).
- [PR #22](https://github.com/DawidHnat/Projekt_Zespolowy/pull/22)
  dodaje `DEFINITION_OF_DONE.md` z 12 sprawdzalnymi warunkami.
- [PR #23](https://github.com/DawidHnat/Projekt_Zespolowy/pull/23)
  dodaje CI każdego PR, `Required CI`, wdrożenie po scaleniu do `main`
  i siedmioznakowe SHA w HTML. Wymagane kontrole przeszły w
  [runie CI](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/39381389953).
- [PR #25](https://github.com/DawidHnat/Projekt_Zespolowy/pull/25)
  dodaje link do prototypu w README i dokumentację MVP.
- Sekrety Actions `DEV_RUNTIME_ENV`, `DEV_SSH_PRIVATE_KEY` i
  `DEV_SSH_KNOWN_HOSTS` są skonfigurowane. `DEV_RUNTIME_ENV` zawiera
  konfigurację wdrożenia, a nie automatyczną kopię lokalnego `.env`.
  Wartości pozostają prywatne; do Git trafiają wyłącznie szablony `.env.example`.

Na VPS działa testowa wersja PR #23 (`e30cadd`), a gotowość API została
sprawdzona. Końcowym dowodem jest dopiero zgodność serwera z aktualnym
`origin/main` po automatycznym wdrożeniu.

## Kolejność dokończenia

1. **Dawid — plan i ochrona `main`.** Repozytorium jest prywatne. Odczyt
   reguł zwraca HTTP 403 z żądaniem GitHub Pro albo upublicznienia repozytorium.
   Konto `jczaja51` ma prawo push, ale nie admin. Właściciel musi zapewnić
   obsługiwany plan na swoim koncie albo podjąć decyzję o widoczności repo.
   Następnie stosuje konfigurację
   [main-protection.json z PR #23](https://github.com/DawidHnat/Projekt_Zespolowy/blob/feat/SCRUM-18-continuous-delivery/infra/deploy/main-protection.json).
   Reguła musi wymagać PR, jednego approval, aktualnego zielonego `Required CI`
   i obowiązywać administratorów bez wyjątków. Automerge pozostaje wyłączone.
2. **Drugi developer i QA — odbiór oraz scalenie.** Najpierw sprawdzić
   i scalić #23, potem zaktualizować #22 i #25 względem nowego `main`,
   uzyskać zielone CI i review oraz je scalić. Ostatnie scalenie także
   uruchomi wdrożenie; z dowodem SHA poczekać do końca tego wdrożenia.
   Autor PR nie zatwierdza własnej zmiany. Obowiązują
   [zasady współpracy](../CONTRIBUTING.md).
3. **Dowód czerwonego CI.** Dopiero po scaleniu #23 przestawić bazę #24
   z gałęzi zależnej na `main`, zaktualizować gałąź i zakończyć tryb draft.
   Zachować błąd składni. Sprawdzić, że `Frontend build` oraz `Required CI`
   są czerwone, a ochrona `main` blokuje scalenie. Sam tryb draft nie jest
   dowodem wymuszenia CI. Tego PR nigdy nie scalać.
4. **Prowadzący — dostęp.** Po uzyskaniu jego adresu e-mail udostępnić plik
   Figmy jako **Can view** i potwierdzić dostęp do Jiry oraz repozytorium.
   Ten krok został odłożony przez zespół do czasu podania danych.
5. **PO — termin Sprintu 1.** Sprint pozostaje aktywny, ale zapisane daty
   to 5–19.10.2026. Uzgodnić ze zespołem i prowadzącym dalszy termin;
   samo przepisanie dat nie zastępuje odbioru historyjek.
6. **Zebrać wyniki poniższych poleceń** i wkleić je do własnej odpowiedzi.

## Dowód ochrony — wykonuje administrator

Próbę wykonać po włączeniu i odczytaniu ochrony, z konta administratora
repozytorium. Przy obecnej niechronionej gałęzi push mógłby się powieść.
Właściciel może najpierw sprawdzić konto i regułę:

```bash
gh api user --jq .login
gh api repos/DawidHnat/Projekt_Zespolowy --jq .permissions.admin
gh api repos/DawidHnat/Projekt_Zespolowy/branches/main/protection
```

Drugi wynik musi być `true`, a reguła musi egzekwować PR z approval,
`Required CI` i `enforce_admins.enabled: true`. Dopiero wtedy w osobnym
katalogu sklonować repozytorium i utworzyć nowy pusty commit:

```bash
git clone https://github.com/DawidHnat/Projekt_Zespolowy.git fleet-flow-test-ochrony
cd fleet-flow-test-ochrony
git switch main
git commit --allow-empty -m "test: sprawdzenie ochrony main"
git push origin main
```

Zapisać pełny rzeczywisty wynik `git push origin main`: ma zawierać odrzucenie
przez regułę. `Everything up-to-date` nie spełnia kryterium nowego commita.
Jeśli push zostanie przyjęty, kryterium nie jest spełnione i należy poprawić
regułę; nie przedstawiać takiej próby jako zaliczonej.

## Dowód wdrożenia ostatniego `main`

Po ostatnim scaleniu poczekać na zielone CI **łącznie z jobem wdrożenia**,
a następnie w zwykłym klonie projektu wykonać dokładne polecenie kursowe:

```bash
git fetch && curl -s http://57.129.179.53/ | grep "$(git rev-parse --short=7 origin/main)"
```

Wkleić rzeczywisty znaleziony fragment HTML i sprawdzone SHA. Pusty wynik
oznacza, że zgodność nie została potwierdzona. Nie podstawiać SHA gałęzi PR.
Gotowość API można sprawdzić osobno:

```bash
curl -fsS https://vps-9171bf52.vps.ovh.net/api/health/ready
```

## Szablon własnej odpowiedzi

Skopiować linki z pierwszej tabeli, a pola poniżej zastąpić rzeczywistymi
dowodami dopiero po wykonaniu prób:

- Login GitHub: **[swój login]**.
- PR z błędnym buildem: **#24**, z widocznym czerwonym CI i blokadą ochrony `main`.
- Wynik `git push origin main` z nowym commitem na koncie administratora:
  **[wkleić pełne odrzucenie]**.
- Wynik `git fetch && curl ... | grep ...` po ostatnim wdrożeniu:
  **[wkleić znaleziony HTML z siedmioma znakami SHA]**.

Nie oddawać pustych pól ani opisu planowanej konfiguracji jako wykonanego dowodu.
