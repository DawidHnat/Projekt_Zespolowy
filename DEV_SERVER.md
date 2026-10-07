# Serwer deweloperski Fleet-Flow

Stan: **7 października 2026 — VPS OVH aktywny; indywidualne SSH jeszcze niezweryfikowane**.

| Parametr | Wartość |
| --- | --- |
| Dostawca | OVHcloud, VPS-1 2027 |
| Zasoby potwierdzone w panelu | 2 vCore, 4 GB RAM, 40 GB SSD NVMe |
| System | Ubuntu 26.04 LTS |
| Koszt w koszyku | 23,62 zł brutto / miesiąc, okres 1 miesiąc |
| Nazwa usługi OVH | `vps-9171bf52.vps.ovh.net` |
| IPv4 | `57.129.179.53` |
| IPv6 | `2001:41d0:801:2000::411f` |
| Lokalizacja | Londyn, Wielka Brytania (`os-uk2`) |
| Odcisk hosta ED25519 odczytany w KVM | `SHA256:cIMIkbry/6rulRdE+qxj/+axWrbc6vMitYn75gEofqo` |
| Początkowe konto administratora | `ubuntu` |
| Docelowa nazwa hosta | `fleet-flow-dev` |
| Dostępność | Docelowo stale; SSH ma działać podczas recenzji |
| Odnowienie w panelu | Ręczne; obecna data wygaśnięcia: 7 listopada 2026 |

Cena pochodzi z odczytanego koszyka; kwotę opłaconego zamówienia trzeba
potwierdzić na fakturze. Przy odnowieniu sprawdzamy cenę i zakres promocji
kopii zapasowej. Wyłączenie systemu nie kończy abonamentu VPS. Harmonogram
wyłączeń nie jest planowany.

## Konta i klucze

| Osoba | GitHub | Docelowy login SSH | Stan |
| --- | --- | --- | --- |
| Jakub Czaja | `jczaja51` | `jczaja51` | Publiczny klucz przygotowany; logowanie na nowym VPS do sprawdzenia |
| Dawid Hnat | `DawidHnat` | `dawidhnat` | Potrzebny własny klucz publiczny |
| Jakub Nazarewicz | `jnazarewiczs` | `jnazarewiczs` | Potrzebny własny klucz publiczny |
| Marcel Głowacki | `mglowacki0` | `mglowacki0` | Potrzebny własny klucz publiczny |

Każda osoba używa własnego klucza prywatnego przechowywanego na swoim
komputerze. Instrukcja przygotowania kont jest w [infra/vps](infra/vps/README.md).
Właściciel administracji: Dawid Hnat; konfiguracja: SCRUM-12.

## Wynik do oddania

Po dodaniu klucza właściciel wykonuje na swoim komputerze (macOS/Linux):

```bash
ssh -o BatchMode=yes -o IdentitiesOnly=yes -i /sciezka/do/klucza LOGIN@57.129.179.53 hostname; echo $?
```

W PowerShell:

```powershell
ssh -o BatchMode=yes -o IdentitiesOnly=yes -i $env:USERPROFILE/.ssh/fleet_flow_ed25519 LOGIN@57.129.179.53 hostname
$LASTEXITCODE
```

`LOGIN` oraz ścieżkę klucza zastępujemy własnymi wartościami.
Przy pierwszym połączeniu porównujemy odcisk klucza serwera z wynikiem
`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` odczytanym w konsoli OVH/KVM.
Klucz z hasłem wcześniej dodajemy do `ssh-agent`; tryb BatchMode nie pyta o hasło.

Oczekiwany wynik to nazwa `fleet-flow-dev` i kod `0`. To przykład oczekiwania,
nie dowód wykonanego testu. Każda osoba wkleja własny rzeczywisty wynik do
SCRUM-12. Zadanie pozostaje otwarte do czasu konfiguracji czterech kluczy i testów.
