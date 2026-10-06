# Serwer deweloperski Fleet-Flow w Azure

Krótka instrukcja dla właściciela infrastruktury:
[Dawid — uruchomienie na swojej subskrypcji](DAWID.md).

Szablon `main.json` i skrypt `deploy.py` odtwarzają niezależny serwer na aktywnej
subskrypcji **Azure for Students z włączonym limitem wydatków**. Nie zawierają
loginów do Azure, tokenów, kluczy prywatnych ani haseł. Parametry uruchomienia
powstają w ignorowanym katalogu `.local/`.

Na początku rozwijamy aplikację na `localhost`. Wspólny VPS działa według
harmonogramu: **pon.–pt. 15–22, sobota 8–21, niedziela 12–21**, czas polski.
Poza tymi godzinami VM jest dealokowana. SSH można sprawdzić podczas działania
serwera; na recenzję poza harmonogramem należy go wcześniej uruchomić i zmienić
lub wyłączyć automatyzację.

## Konfiguracja

- Ubuntu 24.04 LTS; domyślnie `Standard_B2als_v2`: 2 vCPU, 4 GiB RAM.
- Dysk systemowy Standard SSD LRS 32 GiB i 2 GiB swapu.
- Oddzielna grupa `fleet-flow-dev-rg`, sieć i stały publiczny IPv4.
- Z Internetu otwarty wyłącznie TCP 22. Aplikację można oglądać tunelem SSH;
  PostgreSQL i porty deweloperskie nie są publicznie dostępne.
- Logowanie SSH wyłącznie kluczem, bez logowania roota i bez haseł.
- `fail2ban` blokuje powtarzające się nieudane próby logowania.
- Cztery osobne konta Linux i wspólny katalog `/srv/fleet-flow` z grupą i ACL.
- Administrator wdrożenia i `dawidhnat` (infrastruktura) mają `sudo` oraz Docker.
  Pozostałe konta nie mają `sudo` ani grupy Docker. Docker daje uprawnienia
  równoważne administratorowi; dostęp grupy jest ograniczony do tych dwóch osób.
- Git, Python z obsługą venv, kompilator, Docker i Compose v2.
  Node/React można uruchamiać w kontenerze z aktualnym obrazem Node LTS.
- Pięć harmonogramów Logic Apps z czasem polskim, także po zmianie czasu.
  Każda tożsamość zarządzana ma tylko uprawnienie do startu albo dealokacji
  jednej VM; nie przechowujemy sekretów Azure. Harmonogramy są wdrażane osobno,
  więc zmiana godzin nie wymaga zmiany cloud-init istniejącej maszyny.

## Uruchomienie na swoim koncie lub koncie Dawida

Wymagania: Azure CLI, Python 3, OpenSSH i sesja `az login` osoby posiadającej
docelową subskrypcję. Każda osoba dostarcza własny publiczny klucz SSH zgodnie z
[instrukcją kluczy](public-keys/README.md). Prywatne klucze zostają u właścicieli.

```bash
az login
az account list --query '[].{name:name,id:id,state:state,tenant:tenantId}' -o table

# ID_SUBSKRYPCJI zastępujemy rzeczywistym ID konta wybranego do wdrożenia.
python3 infra/azure/deploy.py --subscription ID_SUBSKRYPCJI --render-only
python3 infra/azure/deploy.py --subscription ID_SUBSKRYPCJI --validate-only
python3 infra/azure/deploy.py --subscription ID_SUBSKRYPCJI
```

Na koncie Dawida najpierw zapisujemy jego klucz publiczny do
`public-keys/dawidhnat.pub`, a następnie uruchamiamy:

```bash
python3 infra/azure/deploy.py --subscription ID_SUBSKRYPCJI_DAWIDA --admin dawidhnat
```

Region `polandcentral` i rozmiar muszą być dozwolone w docelowej subskrypcji.
W razie ograniczeń można przekazać `--location` i `--vm-size`. Skrypt sprawdza
rodzaj subskrypcji oraz limit wydatków i nie zmienia oferty rozliczeniowej.

To skrypt **tworzenia nowego serwera**, a nie aktualizacji kont na istniejącym.
Cloud-init wykonuje się przy pierwszym uruchomieniu. Nowy klucz na istniejącej
VM dodajemy skryptem poniżej. Nie należy zmieniać `customData` wdrożonej VM.

## Harmonogramy

`deploy.py` domyślnie tworzy również harmonogramy. Opcja `--no-power-schedule`
pozwala pominąć je przy tworzeniu nowego serwera. Nowa VM od razu działa na
potrzeby konfiguracji i testu SSH, aż do ręcznej lub zaplanowanej dealokacji.

Na istniejącej VM harmonogramy wdrażamy lub zmieniamy osobnym skryptem:

```bash
python3 infra/azure/power_schedule.py --subscription ID_SUBSKRYPCJI --validate-only
python3 infra/azure/power_schedule.py --subscription ID_SUBSKRYPCJI
```

Godziny i dni są w `SCHEDULES` w `power_schedule.py`. Zmieniamy je i ponownie
wdrażamy ten skrypt. Szablon nie modyfikuje VM, danych, sieci ani kluczy SSH.
Wymaga uprawnień do tworzenia harmonogramów, ról i przypisań Azure RBAC.
Skrypt najpierw wdraża harmonogramy jako wyłączone, nadaje uprawnienia, a dopiero
potem je włącza. Początek cyklu w przeszłości pozwala wyznaczyć następne
zaplanowane wykonanie bez natychmiastowego uruchomienia przy wdrożeniu.

Przed recenzją poza zwykłymi godzinami można wyłączyć wszystkie harmonogramy
i uruchomić VM ręcznie:

```bash
python3 infra/azure/power_schedule.py --subscription ID_SUBSKRYPCJI --state disabled
az vm start --subscription ID_SUBSKRYPCJI -g fleet-flow-dev-rg -n fleet-flow-dev
```

Wyłączenie automatyzacji samo nie wyłącza VM. Po recenzji uruchamiamy skrypt
ponownie bez `--state disabled`, a poza godzinami pracy ręcznie dealokujemy VM.
Manualny start poza harmonogramem nie zapewnia automatycznego wyłączenia po
godzinie — kolejna dealokacja nastąpi dopiero o następnym zaplanowanym końcu pracy.

[Zasady cyklicznych harmonogramów Microsoft](https://learn.microsoft.com/en-us/azure/logic-apps/concepts-schedule-automated-recurring-tasks-workflows).

## Dodanie klucza do istniejącego konta

Najpierw porównujemy odcisk klucza z odciskiem przekazanym przez jego właściciela.
W miejsce `IP_SERWERA` wpisujemy adres z `DEV_SERVER.md`.

```bash
python3 infra/azure/add-ssh-key.py dawidhnat /sciezka/dawid.pub \
  --host IP_SERWERA --admin jczaja51 --identity ~/.ssh/fleet_lite_azure_ed25519
```

Analogicznie dla `jnazarewiczs` i `mglowacki0`. Skrypt dopisuje klucz zamiast
nadpisywać pozostałe, ustawia uprawnienia `.ssh`, a klucz **publiczny** zachowuje
w lokalnym `public-keys/`, aby kolejne wdrożenie miało te same konta i dostęp.
Po zmianie należy zapisać publiczne pliki w repozytorium zespołu.

## Test wymagany do oddania

Po dodaniu swojego klucza każda osoba wykonuje test ze swojego komputera.
Przy pierwszym połączeniu porównuje odcisk serwera z `DEV_SERVER.md`.
Przy kluczu zabezpieczonym frazą najpierw dodaje go do `ssh-agent`, aby
`BatchMode=yes` nie musiał pytać o hasło:

```bash
ssh-add ~/.ssh/fleet_flow_ed25519
ssh -i ~/.ssh/fleet_flow_ed25519 LOGIN_LINUX@IP_SERWERA hostname
ssh -o BatchMode=yes -o IdentitiesOnly=yes \
  -i ~/.ssh/fleet_flow_ed25519 LOGIN_LINUX@IP_SERWERA hostname; echo $?
```

Oczekiwany wynik to `fleet-flow-dev` oraz `0`. Samo utworzenie konta lub odczyt
jego `authorized_keys` nie dowodzi, że właściciel potrafi zalogować się swoim
kluczem. Każda osoba samodzielnie zachowuje wynik swojego testu.

W PowerShell kod wyjścia wyświetlamy przez `$LASTEXITCODE` zamiast `echo $?`.
Jakub Czaja używa już istniejącego `~/.ssh/fleet_lite_azure_ed25519`.

## Start, oszczędzanie kredytu i tunel do aplikacji

```bash
az vm start --subscription ID_SUBSKRYPCJI -g fleet-flow-dev-rg -n fleet-flow-dev
az vm get-instance-view --subscription ID_SUBSKRYPCJI \
  -g fleet-flow-dev-rg -n fleet-flow-dev \
  --query 'instanceView.statuses[].displayStatus' -o table

# Kończąc pracę, używamy deallocate, a nie shutdown wewnątrz Linuxa.
az vm deallocate --subscription ID_SUBSKRYPCJI -g fleet-flow-dev-rg -n fleet-flow-dev

# Przykładowy dostęp do frontendu (5173) i API (8000) przez SSH.
ssh -L 5173:127.0.0.1:5173 -L 8000:127.0.0.1:8000 LOGIN_LINUX@IP_SERWERA
```

Po dealokacji nie są naliczane opłaty za procesor i RAM; dysk i stały IPv4
nadal kosztują. Wyłączenie poleceniem `shutdown` w Linuxie nie gwarantuje
zatrzymania opłat za VM. SSH nie może włączyć dealokowanej maszyny; potrzebne
jest konto z uprawnieniami do uruchomienia VM w Azure.

Cennik detaliczny Azure dla `polandcentral`, odczyt 06.10.2026 (USD,
bez uwzględnienia ewentualnych darmowych limitów subskrypcji):

| Element | Stawka | Szacunek za 730 godzin |
| --- | --- | --- |
| B2als_v2 Linux | 0,0432 USD/h działania | 31,54 USD |
| Standard SSD E4, 32 GiB | 2,40 USD/miesiąc | 2,40 USD |
| Stały publiczny IPv4 Standard | 0,005 USD/h | 3,65 USD |
| Razem przy pracy całą dobę | | **37,59 USD/miesiąc** |

Dodatkowo mogą być naliczane operacje dyskowe i transfer wychodzący.
Przy ciągłej dealokacji pozostaje około **6,05 USD/miesiąc** za dysk i IPv4.
Przy obecnym harmonogramie (57 godzin tygodniowo) szacunek to około
**16,75 USD/miesiąc** za VM, dysk i IPv4, plus operacje, transfer i niewielkie
opłaty za wykonania harmonogramów. To szacunek, a nie limit kosztów.
Przy 10 godzinach pracy dziennie przez 30 dni szacunek wynosi
**19,01 USD/miesiąc + operacje i transfer**. Nie jest to limit kosztów.
Saldo w portalu może być wyświetlane w EUR; nie należy utożsamiać kwot EUR i USD.
Pozostałe zasoby tej samej subskrypcji również zużywają kredyt.

[Cennik i API Microsoft](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices),
[kontrola kredytu studenckiego](https://learn.microsoft.com/en-us/azure/education-hub/navigate-costs),
[stany i rozliczanie VM](https://learn.microsoft.com/en-us/azure/virtual-machines/states-billing).

## Przeniesienie na subskrypcję Dawida

Najprostsza opcja: odtworzyć serwer tym samym skryptem na subskrypcji Dawida,
przenieść dane aplikacji i zmienić IP w dokumentacji. Dostęp SSH pozostaje oparty
na publicznych kluczach tych samych osób; nowa VM ma nowe klucze **serwera**.
Nie kopiujemy kluczy prywatnych ani loginów do Azure.

1. Dawid dodaje swój `.pub` i wykonuje nowe wdrożenie z `--admin dawidhnat`.
2. Porównujemy klucz hosta nowej VM, otrzymany przez Azure Run Command.
3. Jeżeli na starym serwerze są już dane, wykonujemy spójną kopię. Pliki
   `/srv/fleet-flow` kopiujemy przez SSH, a bazę PostgreSQL eksportujemy
   `pg_dump`/`pg_dumpall`. Nazwany wolumen Dockera nie jest częścią kopii katalogu.
4. Odtwarzamy pliki, bazę i osobno ustawiamy sekrety na nowym serwerze.
5. Testujemy aplikację i logowanie każdej osoby na nowy adres.
6. Dealokujemy stary serwer. Usunięcie starej grupy zasobów dopiero po
   sprawdzeniu kopii i decyzji właściciela, bo usuwa także dysk z danymi.

Przykładowy transfer samego katalogu aplikacji (po zatrzymaniu zapisów do niego;
zmienne adresów, loginów i ścieżek muszą wskazywać właściwe serwery):

```bash
mkdir -p infra/azure/.local
umask 077
ssh -i ~/.ssh/fleet_lite_azure_ed25519 jczaja51@STARE_IP \
  'sudo tar --acls --xattrs -C /srv -czf - fleet-flow' \
  > infra/azure/.local/fleet-flow-data.tar.gz

ssh -i ~/.ssh/fleet_flow_ed25519 dawidhnat@NOWE_IP \
  'sudo tar --acls --xattrs --no-same-owner -C /srv -xzf - && sudo chown -R root:fleet-flow /srv/fleet-flow' \
  < infra/azure/.local/fleet-flow-data.tar.gz
```

Archiwum może zawierać sekrety aplikacji: przechowujemy je prywatnie, poza Git.
Powyższy przykład nie tworzy kopii bazy w wolumenie Dockera.

Alternatywa: bezpośrednie przeniesienie VM, dysku, sieci i IPv4 między
subskrypcjami. Azure wymaga tej samej dzierżawy Microsoft Entra oraz uprawnień
na obu subskrypcjach. Trzeba wykonać walidację przeniesienia wszystkich
zależności; nie wszystkie typy zasobów i konfiguracje wspierają taki ruch.
Nie zakładamy, że da się przenieść kredyt studencki — docelowa subskrypcja
zużywa własny kredyt.

[Oficjalne zasady przenoszenia zasobów](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/move-resource-group-and-subscription).
