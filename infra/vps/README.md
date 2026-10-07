# Przygotowanie VPS OVHcloud

VPS jest aktywny pod adresem `57.129.179.53`. Cztery konta są utworzone;
logowanie kluczem `jczaja51` sprawdzono, pozostałe konta czekają na klucze.
Szczegóły i wynik testu są w [DEV_SERVER.md](../../DEV_SERVER.md),
właściciel zadania: Dawid (SCRUM-12).

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

## Pierwsze połączenie administratora po instalacji VPS

Ten etap już wykonano na obecnym VPS. Konto `ubuntu` przyjmuje klucz
administratora; logowanie SSH hasłem jest wyłączone.

1. Potwierdzony adres tego VPS to `57.129.179.53`, a początkowy login to `ubuntu`.
2. Jeśli instalacja pozwala wskazać klucz SSH, wybierz własny klucz publiczny
   administratora. Jeżeli dostarczono hasło pierwszego logowania, właściciel
   używa go lokalnie; hasła nie wklejamy do repozytorium ani czatu.
   Link do hasła tymczasowego znajduje się w wiadomości OVH o dostarczeniu VPS.
   Właściciel sam wykonuje wymaganą zmianę hasła i ponownie się loguje.
3. Odcisk klucza hosta odczytaj w zaufanej konsoli OVH/KVM i porównaj przy
   pierwszym SSH. Nie wyłączaj weryfikacji hosta.
4. Sprawdź dostęp administratora i zachowaj otwartą sesję podczas konfiguracji.

Oficjalne instrukcje: [OVH — pierwsze kroki z VPS](https://docs.ovhcloud.com/en/guides/bare-metal-cloud/virtual-private-servers/starting-with-a-vps).

## Konta Linux i dodawanie kolejnych kluczy

Konta `jczaja51`, `dawidhnat`, `jnazarewiczs` i `mglowacki0` już istnieją.
Poniższy proces pozwala dodać brakujące klucze lub odtworzyć konta na nowym VPS.

Po pierwszym logowaniu administrator przenosi skrypt oraz zatwierdzone
publiczne klucze z lokalnego repozytorium na VPS:

```bash
ssh ubuntu@57.129.179.53 'mkdir -p ~/fleet-flow-vps'
scp infra/vps/setup-accounts.sh ubuntu@57.129.179.53:fleet-flow-vps/
scp -r infra/vps/public-keys ubuntu@57.129.179.53:fleet-flow-vps/
ssh ubuntu@57.129.179.53 'sudo bash ~/fleet-flow-vps/setup-accounts.sh ~/fleet-flow-vps/public-keys'
```

Powyższe polecenia mogą wymagać hasła administratora. Gdy jego klucz jest już
dodany, lokalnie wskaż go przez `ssh-agent` albo opcję `-i` w SSH/SCP.

[setup-accounts.sh](setup-accounts.sh) sprawdza format kluczy przed zmianą
kont, tworzy cztery konta z zablokowanymi hasłami, grupę `fleet-flow` i wspólny
katalog `/srv/fleet-flow`. Dodaje dostarczone klucze bez usuwania wcześniejszych.
Brakującego klucza nie generuje za inną osobę. Przy pierwszym uruchomieniu
konto bez własnego klucza pozostaje niedostępne; przy powtórnym uruchomieniu
istniejące klucze pozostają. Cztery konta mają dostęp do wspólnego katalogu.
Skrypt nie nadaje uprawnień `sudo`; konfigurację systemu wykonuje administrator
na koncie `ubuntu`.

Po otrzymaniu kolejnych kluczy prześlij aktualny katalog `public-keys` i ponownie
uruchom skrypt z konta administratora `ubuntu`.

Nazwę hosta i strefę czasową ustaw na serwerze:

```bash
sudo hostnamectl set-hostname fleet-flow-dev
sudo timedatectl set-timezone Europe/Warsaw
```

Jeżeli obraz korzysta z cloud-init, w jego konfiguracji ustaw
`preserve_hostname: true`, aby nazwa hosta została zachowana po restarcie.

## Zabezpieczenie i sprawdzenie

Na obecnym VPS zastosowano opisane ustawienia SSH i UFW oraz potwierdzono
nowe sesje `jczaja51` i `ubuntu`. Przy odtwarzaniu VPS wykonujemy kolejno:

Najpierw potwierdź w **drugiej sesji** logowanie kluczem `jczaja51` i zachowaj
działającą sesję administratora `ubuntu`. Dopiero po sukcesie utwórz
`/etc/ssh/sshd_config.d/00-fleet-flow.conf` z konta administratora:

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
