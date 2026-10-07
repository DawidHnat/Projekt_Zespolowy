# Przygotowanie VPS OVHcloud

VPS został zakupiony. Instrukcję stosujemy po aktywacji serwera; nie stanowi
ona potwierdzenia istniejących kont ani działającego SSH. Stan jest w
[DEV_SERVER.md](../../DEV_SERVER.md), właściciel zadania: Dawid (SCRUM-12).

## Klucze czterech osób

Każdy generuje klucz na swoim komputerze, jeśli nie ma własnego odpowiedniego
klucza. Przy istniejącym pliku wybieramy inną nazwę, aby go nie nadpisać:

```bash
ssh-keygen -t ed25519 -C "fleet-flow-TWOJ_LOGIN" -f ~/.ssh/fleet_flow_ed25519
```

Hasło klucza ustala właściciel. Do zespołu przekazuje wyłącznie plik `.pub`.
Klucz prywatny pozostaje na komputerze. Na Windows ścieżka to
`$env:USERPROFILE/.ssh/fleet_flow_ed25519`. Publiczne pliki zapisujemy jako:
`jczaja51.pub`, `dawidhnat.pub`, `jnazarewiczs.pub`, `mglowacki0.pub`.

## Pierwsze połączenie

1. Po aktywacji odczytaj IP i login systemowy w panelu serwera. Dla Ubuntu
   zwykle jest to `ubuntu`, ale sprawdź dane dostarczone dla zamówienia.
2. Jeśli instalacja pozwala wskazać klucz SSH, wybierz własny klucz publiczny
   administratora. Jeżeli dostarczono hasło pierwszego logowania, właściciel
   używa go lokalnie; hasła nie wklejamy do repozytorium ani czatu.
3. Odcisk klucza hosta odczytaj w zaufanej konsoli OVH/KVM i porównaj przy
   pierwszym SSH. Nie wyłączaj weryfikacji hosta.
4. Sprawdź dostęp administratora i zachowaj otwartą sesję podczas konfiguracji.

Oficjalne instrukcje: [OVH — pierwsze kroki z VPS](https://docs.ovhcloud.com/en/guides/bare-metal-cloud/virtual-private-servers/starting-with-a-vps).

## Konta Linux i klucze

Na nowym serwerze administrator wykonuje:

```bash
sudo hostnamectl set-hostname fleet-flow-dev
sudo timedatectl set-timezone Europe/Warsaw
sudo groupadd -f fleet-flow
for member in jczaja51 dawidhnat jnazarewiczs mglowacki0; do
  id "$member" >/dev/null 2>&1 || sudo useradd -m -s /bin/bash "$member"
  sudo usermod -aG fleet-flow "$member"
  sudo passwd -l "$member"
  sudo install -d -m 700 -o "$member" -g "$member" "/home/$member/.ssh"
done
sudo install -d -o root -g fleet-flow -m 2770 /srv/fleet-flow
```

Publiczne klucze przenieś do tymczasowego katalogu na serwerze. Dla każdego
otrzymanego klucza sprawdź `ssh-keygen -lf LOGIN.pub`, a następnie na **nowym
koncie** zainstaluj go (podmień login i ścieżkę):

```bash
sudo install -m 600 -o LOGIN -g LOGIN /sciezka/LOGIN.pub /home/LOGIN/.ssh/authorized_keys
```

Powyższe polecenie zastępuje `authorized_keys`; przy dodawaniu kolejnego klucza
na istniejącym koncie dopisujemy zatwierdzony klucz zamiast kasować wcześniejsze.
Konto bez klucza pozostaje niedostępne. Uprawnienia administracyjne nadajemy
Jakubowi Czai i Dawidowi zgodnie z rolą; inni mają grupę `fleet-flow`:

```bash
sudo usermod -aG sudo jczaja51
sudo usermod -aG sudo dawidhnat
printf 'jczaja51 ALL=(ALL) NOPASSWD:ALL
dawidhnat ALL=(ALL) NOPASSWD:ALL
' | sudo tee /etc/sudoers.d/fleet-flow-admins >/dev/null
sudo chmod 440 /etc/sudoers.d/fleet-flow-admins
sudo visudo -cf /etc/sudoers.d/fleet-flow-admins
```

## Zabezpieczenie i sprawdzenie

Najpierw potwierdź w **drugiej sesji** logowanie kluczem `jczaja51` oraz działanie
`sudo`. Dopiero po sukcesie utwórz `/etc/ssh/sshd_config.d/00-fleet-flow.conf`:

```text
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
```

Sprawdź `sudo sshd -t`, następnie `sudo systemctl reload ssh`. Nie zamykaj
pierwszej sesji, dopóki nowa sesja działa. Firewall ma dopuszczać TCP 22;
przed włączeniem UFW dodaj regułę `sudo ufw allow OpenSSH`. Nie wystawiaj bazy
ani API na Internet. Porty WWW i TLS dodamy w zadaniu wdrożenia SCRUM-18.

Każda osoba sprawdza własny klucz poleceniem z DEV_SERVER.md. Zapisz w SCRUM-12
cztery rzeczywiste wyniki oraz adres, odcisk hosta i stan kluczy w DEV_SERVER.md.
Dopiero wtedy kryterium dostępu zespołu jest wykonane. Pracę nad aplikacją
prowadzimy lokalnie, a VPS pozostaje dostępny dla recenzji SSH.
