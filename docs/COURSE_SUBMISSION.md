# Backlog, prototyp i pipeline — odbiór zadania

Stan sprawdzony 23 października 2026; daty Sprintu 1 zaktualizowano
i ponownie odczytano w Jirze 24 października 2026. Dowody wdrożenia trzeba
odświeżyć po ostatnim scaleniu, również po scaleniu zmian samej dokumentacji.

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
  Każda zawiera link do swojego przepływu Figmy. Na polecenie PO ustawiono
  daty 24.10.2026, godz. 18:33 – 7.11.2026, godz. 18:33 (Europe/Warsaw),
  zachowując cel, skład i historię istniejącego sprintu.
- Podział pracy z 24.10.2026 obejmuje całą czwórkę: SCRUM-16 — Czaja,
  SCRUM-15 — Dawid, SCRUM-5 — Nazarewicz, SCRUM-37 — Marcel.
  Sprint 1 ma dziewięć zgłoszeń głównych, nadal trzy Story i 21 SP.
  Planowany Sprint 2 obejmuje SCRUM-6/62/42 (21 SP) oraz zadanie
  integracyjnego odbioru SCRUM-63; pozostaje nieuruchomiony.
- Prototyp ma 25 edytowalnych ekranów i trzy nazwane przepływy Sprintu 1.
  Szklany widok z tapetą miasta odpowiada wybranemu wariantowi aplikacji.
  [Scenariusze przeglądu](PROTOTYPE.md).
- [PR #22](https://github.com/DawidHnat/Projekt_Zespolowy/pull/22)
  jest scalony; `DEFINITION_OF_DONE.md` ma 12 sprawdzalnych warunków.
- [PR #23](https://github.com/DawidHnat/Projekt_Zespolowy/pull/23)
  jest scalony: CI każdego PR, `Required CI`, wdrożenie po scaleniu do `main`
  i siedmioznakowe SHA w HTML. Budowa i wdrożenie `main` przeszły w
  [runie CI](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/39485972458).
- [PR #25](https://github.com/DawidHnat/Projekt_Zespolowy/pull/25)
  jest scalony; README zawiera link do prototypu i dokumentacji MVP.
- Sekrety Actions `DEV_RUNTIME_ENV`, `DEV_SSH_PRIVATE_KEY` i
  `DEV_SSH_KNOWN_HOSTS` są skonfigurowane. `DEV_RUNTIME_ENV` zawiera
  konfigurację wdrożenia, a nie automatyczną kopię lokalnego `.env`.
  Wartości pozostają prywatne; do Git trafiają wyłącznie szablony `.env.example`.

21.10.2026 serwer pokazał `23dd927` zgodne z ówczesnym `origin/main`.
Dokładne polecenie kursowe zwróciło HTML z tym SHA i kod 0; API ready
odpowiedziało `{"status":"ok"}`. To dowód dla tego commita, wymagający
powtórzenia po każdym kolejnym scaleniu.

## Ochrona i czerwone CI — potwierdzone

Repozytorium jest publiczne. Odczyt gałęzi potwierdził `protected: true`
oraz wymagany `Required CI` z `enforcement_level: everyone`. Widok PR
potwierdził wymóg co najmniej jednego approval oraz zatwierdzenia ostatniego
pusha przez inną osobę. Konto współpracownika `jczaja51` ma push, ale nie
admin; pełne ustawienia ochrony przez API są dla niego niedostępne (404).

Przekazany przez Dawida zrzut pokazuje nowy commit `be4bc42` i odrzucenie
`git push origin main` przez GH006: wymagany PR i `Required CI`.
Wcześniejszy pusty test commit `23dd927` został przyjęty; dowodem odrzucenia
jest późniejsza próba `be4bc42`.

PR #24 ma bazę `main`, nie jest draftem i zawiera celowy błąd TypeScript.
W [runie 39552495593](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/39552495593)
`Frontend build` i `Required CI` mają FAILURE, backend i obraz przeszły,
wdrożenie zostało pominięte. Scalenie jest blokowane. **Tego PR nigdy nie scalać.**

Historycznie PR #23 został scalony bez wpisu approval w API reviews;
PR-y #22 i #25 mają APPROVED. Nie przedstawiamy scalenia #23 jako dowodu
przeglądu. Bieżące reguły wymagają approval dla kolejnych zmian.

## Pozostałe kroki do oddania

1. **Prowadzący — dostęp.** Udostępnić plik Figmy jako **Can view**
   i potwierdzić dostęp do Jiry. Ten krok odłożono na prośbę zespołu;
   adresu prowadzącego jeszcze nie podano. Publiczne repo daje dostęp do odczytu.
2. **Przegląd kolejnych PR.** Zmiany dokumentacji także przechodzą review
   drugiego developera i zielone CI przed scaleniem, zgodnie z
   [zasadami współpracy](../CONTRIBUTING.md). Nie włączamy automerge.
3. **Odświeżyć dowód wdrożenia po ostatnim scaleniu.** Poczekać na zielony
   job wdrożenia, wykonać poniższe polecenie z `git fetch` i zapisać wynik.
4. **Każdy oddaje osobno.** Wkleić linki, własny login, pełne odrzucenie
   pusha administratora oraz aktualny wynik porównania SHA.

## Dowód ochrony — wykonuje administrator

Poniższa instrukcja służy powtórzeniu dowodu z konta administratora.
Przed próbą właściciel sprawdza konto i regułę:

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
