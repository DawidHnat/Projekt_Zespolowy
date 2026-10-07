# Serwer deweloperski Fleet-Flow

Stan: **7 października 2026 — VPS jeszcze niezamówiony**.

| Parametr | Plan |
| --- | --- |
| Dostawca | OVHcloud, VPS-1 2027 |
| Zasoby w wybranym koszyku | 2 vCore, 4 GB RAM, 40 GB SSD NVMe |
| System | Ubuntu 26.04 LTS |
| Koszt w koszyku | 23,62 zł brutto / miesiąc, okres 1 miesiąc |
| Adres i odcisk klucza hosta | Do uzupełnienia po aktywacji |
| Docelowa nazwa hosta | `fleet-flow-dev` |
| Dostępność | Docelowo stale; SSH ma działać podczas recenzji |

Cena dotyczy odczytanego koszyka, a nie opłaconego zamówienia. Przy odnowieniu
trzeba sprawdzić cenę i zakres promocji kopii zapasowej. Wyłączenie systemu
nie kończy abonamentu VPS. Harmonogram wyłączeń nie jest planowany.

## Konta i klucze

| Osoba | GitHub | Docelowy login SSH | Stan |
| --- | --- | --- | --- |
| Jakub Czaja | `jczaja51` | `jczaja51` | Publiczny klucz przygotowany, serwer oczekuje na aktywację |
| Dawid Hnat | `DawidHnat` | `dawidhnat` | Potrzebny własny klucz publiczny |
| Jakub Nazarewicz | `jnazarewiczs` | `jnazarewiczs` | Potrzebny własny klucz publiczny |
| Marcel Głowacki | `mglowacki0` | `mglowacki0` | Potrzebny własny klucz publiczny |

Każda osoba używa własnego klucza prywatnego przechowywanego na swoim
komputerze. Instrukcja przygotowania kont jest w [infra/vps](infra/vps/README.md).
Właściciel administracji: Dawid Hnat; konfiguracja: SCRUM-12.

## Wynik do oddania

Po dodaniu klucza właściciel wykonuje na swoim komputerze (macOS/Linux):

```bash
ssh -o BatchMode=yes -o IdentitiesOnly=yes -i /sciezka/do/klucza LOGIN@IP_VPS hostname; echo $?
```

W PowerShell:

```powershell
ssh -o BatchMode=yes -o IdentitiesOnly=yes -i $env:USERPROFILE/.ssh/fleet_flow_ed25519 LOGIN@IP_VPS hostname
$LASTEXITCODE
```

`LOGIN`, `IP_VPS` oraz ścieżkę klucza zastępujemy własnymi wartościami.
Przy pierwszym połączeniu porównujemy odcisk klucza serwera z wynikiem
`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` odczytanym w konsoli OVH/KVM.
Klucz z hasłem wcześniej dodajemy do `ssh-agent`; tryb BatchMode nie pyta o hasło.

Oczekiwany wynik to nazwa `fleet-flow-dev` i kod `0`. To przykład oczekiwania,
nie dowód wykonanego testu. Każda osoba wkleja własny rzeczywisty wynik do
SCRUM-12. Zadanie pozostaje otwarte do czasu aktywacji, czterech kluczy i testów.
