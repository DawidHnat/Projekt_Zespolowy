# Serwer deweloperski Fleet-Flow

Stan: **7 października 2026 — cztery konta utworzone; SSH jczaja51 działa, trzy klucze oczekujące**.

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
| Konto administratora | `ubuntu`, dostęp kluczem Jakuba Czai |
| Nazwa hosta | `fleet-flow-dev` |
| Dostępność | Stale; brak harmonogramu wyłączania |
| Odnowienie w panelu | Ręczne; obecna data wygaśnięcia: 7 listopada 2026 |

Cena pochodzi z odczytanego koszyka; kwotę opłaconego zamówienia trzeba
potwierdzić na fakturze. Przy odnowieniu sprawdzamy cenę i zakres promocji
kopii zapasowej. Wyłączenie systemu nie kończy abonamentu VPS. Harmonogram
wyłączeń nie jest planowany.

## Konta i klucze

| Osoba | GitHub | Docelowy login SSH | Stan |
| --- | --- | --- | --- |
| Jakub Czaja | `jczaja51` | `jczaja51` | Klucz dodany; rzeczywisty test BatchMode zakończony kodem `0` |
| Dawid Hnat | `DawidHnat` | `dawidhnat` | Konto utworzone; potrzebny własny klucz publiczny i test |
| Jakub Nazarewicz | `jnazarewiczs` | `jnazarewiczs` | Konto utworzone; potrzebny własny klucz publiczny i test |
| Marcel Głowacki | `mglowacki0` | `mglowacki0` | Konto utworzone; potrzebny własny klucz publiczny i test |

Każda osoba używa własnego klucza prywatnego przechowywanego na swoim
komputerze. Instrukcja przygotowania kont jest w [infra/vps](infra/vps/README.md).
Właściciel zadania infrastruktury: Dawid Hnat; konfiguracja: SCRUM-12.

## Zastosowana konfiguracja

- SSH przyjmuje klucze publiczne; logowanie SSH hasłem i bezpośrednio na root
  jest wyłączone. Świeże sesje `jczaja51` oraz administratora `ubuntu` działają
  również po przeładowaniu SSH i włączeniu firewalla.
- UFW działa i dopuszcza TCP 22 dla IPv4 i IPv6. Pozostały ruch przychodzący
  jest blokowany; nie uruchomiono jeszcze aplikacji ani bazy danych.
- Cztery konta mają zablokowane hasła i należą do grupy `fleet-flow`.
  Wspólny katalog `/srv/fleet-flow` ma prawa `2770`; `jczaja51` ma prawo zapisu.
  Konta zespołu nie otrzymały uprawnień `sudo`. Konfigurację systemu wykonujemy
  z konta administratora `ubuntu`; przekazanie administracji Dawidowi wymaga
  jego własnego klucza i osobnego ustalenia uprawnień.
- Strefa czasowa: `Europe/Warsaw`. Cloud-init zachowuje nazwę `fleet-flow-dev`.

## Wykonany test Jakuba Czai

7 października 2026 wykonano świeże połączenie z Maca z `BatchMode=yes`,
`IdentitiesOnly=yes`, własnym kluczem i ścisłą weryfikacją zapisanego klucza
hosta. Polecenie `hostname` na koncie `jczaja51@57.129.179.53` zwróciło:

Na Macu Jakuba skonfigurowano też alias `fleet-flow-dev`. Jego rzeczywisty test:

```bash
ssh -o BatchMode=yes fleet-flow-dev hostname; echo $?
```

```text
fleet-flow-dev
0
```

`0` jest rzeczywistym kodem zakończenia SSH. Odcisk klucza użytkownika:
`SHA256:yFsoSo10hJcY0MHVYWaY7RjOabcGfz/gy56b1rYvkxg`.

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

Każdy test ma zwrócić nazwę `fleet-flow-dev` i kod `0`. Każda osoba wkleja
własny rzeczywisty wynik do SCRUM-12. Zadanie pozostaje otwarte do czasu
konfiguracji czterech kluczy i testów.
