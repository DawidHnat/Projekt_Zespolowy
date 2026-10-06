# Serwer deweloperski Fleet-Flow

Stan konfiguracji: **6 października 2026**.

| Parametr | Wartość |
| --- | --- |
| Adres do oddania zadania | **74.248.36.22** |
| Nazwa hosta | `fleet-flow-dev` |
| Dostawca | Microsoft Azure, subskrypcja Azure for Students |
| Region | Poland Central (`polandcentral`) |
| Grupa zasobów | `fleet-flow-dev-rg` |
| Maszyna | `fleet-flow-dev`, `Standard_B2als_v2` |
| Zasoby | 2 vCPU, 4 GiB RAM, SSD 32 GiB, swap 2 GiB |
| System | Ubuntu 24.04 LTS |
| SSH | TCP 22, wyłącznie klucze publiczne, bez logowania roota |
| Poniedziałek–piątek | Automatyczny start **15:00**, dealokacja **22:00** |
| Sobota | Automatyczny start **8:00**, dealokacja **21:00** |
| Niedziela | Automatyczny start **12:00**, dealokacja **21:00** |
| Strefa czasu | Europe/Warsaw, z uwzględnieniem zmiany czasu |

Kod aplikacji można rozwijać na własnym `localhost`. SSH na VPS jest dostępne
w godzinach działania serwera, po zakończeniu startu VM. Jeżeli recenzja zadania
ma odbywać się poza tymi godzinami, przed recenzją uruchamiamy VM i zmieniamy
lub wyłączamy harmonogramy. Zmiany godzin nie wpływają na klucze SSH.

## Konta zespołu

| Osoba | GitHub | Login SSH | Stan dostępu |
| --- | --- | --- | --- |
| Jakub Czaja | `jczaja51` | `jczaja51` | Klucz dodany; logowanie sprawdzone |
| Dawid Hnat | `DawidHnat` | `dawidhnat` | Konto utworzone; oczekuje na własny klucz publiczny |
| Jakub Nazarewicz | `jnazarewiczs` | `jnazarewiczs` | Konto utworzone; oczekuje na własny klucz publiczny |
| Marcel Głowacki | `mglowacki0` | `mglowacki0` | Konto utworzone; oczekuje na własny klucz publiczny |

Każda osoba używa własnego klucza. Konta bez klucza nie mogą się jeszcze
zalogować. Do spełnienia kryterium „każdy członek zespołu loguje się kluczem”
pozostało dodanie trzech kluczy publicznych i wykonanie testu przez każdą osobę.

Jakub Czaja i Dawid Hnat mają uprawnienia administracyjne w Linuxie (`sudo`
oraz Docker). Pozostałe osoby mają dostęp do wspólnego katalogu
`/srv/fleet-flow` przez grupę `fleet-flow`. Uprawnienia Linuxa nie nadają
dostępu do rozliczeń ani portalu Azure.

## Logowanie i wynik wymagany do oddania

Jakub Czaja, na komputerze z istniejącym kluczem:

```bash
ssh -i ~/.ssh/fleet_lite_azure_ed25519 jczaja51@74.248.36.22

ssh -o BatchMode=yes -o IdentitiesOnly=yes \
  -i ~/.ssh/fleet_lite_azure_ed25519 jczaja51@74.248.36.22 hostname; echo $?
```

Sprawdzony wynik:

```text
fleet-flow-dev
0
```

Pozostałe osoby po dodaniu własnego klucza zastępują login i ścieżkę klucza.
W PowerShell zamiast `echo $?` wyświetlają `$LASTEXITCODE`.
Nie używają prywatnego klucza Jakuba.

Odcisk klucza **serwera** ED25519, pobranego przez uwierzytelnione Azure Run Command:

```text
SHA256:yAki69iqtmhdnJbDCzpVBzf7jahIXgQI8Bg21I9FSiA
```

Należy porównać go przy pierwszym logowaniu. Po odtworzeniu VM klucz hosta
zmieni się i trzeba ponownie sprawdzić go przez Azure. Nie wyłączamy
weryfikacji hosta przez `StrictHostKeyChecking=no`.

## Start i wyłączenie

Właściciel subskrypcji lub osoba z nadanymi uprawnieniami Azure wykonuje:

```bash
az vm start --subscription ID_SUBSKRYPCJI -g fleet-flow-dev-rg -n fleet-flow-dev
az vm deallocate --subscription ID_SUBSKRYPCJI -g fleet-flow-dev-rg -n fleet-flow-dev
```

`ID_SUBSKRYPCJI` można odczytać z `az account list -o table`. Po dealokacji
SSH wraca dopiero po uruchomieniu maszyny przez Azure. SSH nie może uruchomić
wyłączonej VM. Stały adres IPv4 pozostaje taki sam. Dysk i adres IP są
rozliczane także po dealokacji.

Pięć harmonogramów Logic Apps obsługuje starty w tygodniu, sobotę i niedzielę
oraz wyłączenia w tygodniu i weekend. Zachowana nazwa
`fleet-flow-dev-nightly-shutdown` oznacza teraz wyłączenie w dni robocze o 22:00.
Każdy harmonogram ma tożsamość zarządzaną i rolę z jednym uprawnieniem:
`Microsoft.Compute/virtualMachines/start/action` albo
`Microsoft.Compute/virtualMachines/deallocate/action`, przypisaną tylko do
tej VM. Harmonogramy nie przechowują hasła ani sekretu Azure.

Aktualizacja godzin i czasowe wyłączenie automatyzacji są opisane w
[dokumentacji harmonogramów](infra/azure/README.md#harmonogramy).

## Kontrola konfiguracji

Sprawdzono poprawność cloud-init i jego zakończenie (`status: done`), aktywność
SSH, Dockera i fail2ban, blokadę logowania hasłem i roota, obecność czterech kont
oraz prawo wszystkich kont do zapisu we wspólnym katalogu. Konta kolegów nie
mają kluczy w `authorized_keys`. Podczas początkowej konfiguracji wykonano
kontrolne uruchomienie harmonogramu:
Logic Apps zwrócił `Succeeded`, a Azure potwierdził `VM deallocated`.
Po ponownym uruchomieniu VM test SSH ponownie zwrócił nazwę hosta i kod `0`.

Instrukcje dodawania kluczy, koszty i odtworzenie na subskrypcji Dawida znajdują
się w [dokumentacji infrastruktury](infra/azure/README.md).
Dawid może też skorzystać z [krótkiej instrukcji krok po kroku](infra/azure/DAWID.md).
