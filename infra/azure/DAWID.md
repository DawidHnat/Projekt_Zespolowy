# Dawid: uruchomienie serwera na swojej subskrypcji

Na obecnym etapie najprościej odtworzyć serwer z przygotowanego skryptu.
Maszyna na Twoim koncie będzie zużywać **Twój** kredyt Azure for Students.
Powstaną te same cztery konta Linux, a nowy serwer otrzyma własny publiczny IP
i nowy klucz hosta. Klucze prywatne członków zespołu zostają na ich komputerach.

## 1. Pobierz konfigurację

Konfiguracja jest w PR #1, na gałęzi `codex/azure-dev-server`.
Dopóki PR nie jest scalony, pobierz tę gałąź:

```bash
git clone --branch codex/azure-dev-server https://github.com/DawidHnat/Projekt_Zespolowy.git
cd Projekt_Zespolowy
```

Potrzebujesz Git, Azure CLI, Python 3.9 lub nowszego oraz OpenSSH.
Wielowierszowe polecenia z `\` są zapisane dla Bash (Linux/macOS/Git Bash).
W PowerShell wpisuj je w jednym wierszu, bez znaków `\` na końcu linii.

## 2. Przygotuj swój klucz SSH

Wygeneruj klucz na **swoim komputerze** i ustaw własną frazę zabezpieczającą:

```bash
ssh-keygen -t ed25519 -a 64 -f ~/.ssh/fleet_flow_ed25519 -C "DawidHnat@fleet-flow"
```

Do `infra/azure/public-keys/dawidhnat.pub` skopiuj wyłącznie zawartość pliku
`~/.ssh/fleet_flow_ed25519.pub`. Pozostałe publiczne klucze, gdy właściciele
je dostarczą, również zapisujemy w `public-keys/`. Klucz Jakuba Czai jest
już w repozytorium. Brak publicznego klucza oznacza konto bez dostępu SSH.

Nie kopiuj do repozytorium pliku `fleet_flow_ed25519` bez końcówki `.pub`.
Twój login Linux będzie zapisany małymi literami: **`dawidhnat`**.

## 3. Zaloguj się do swojego Azure i uruchom skrypt

```bash
az login
az account list --query '[].{name:name,id:id,state:state,tenant:tenantId}' -o table
```

Znajdź własną aktywną subskrypcję **Azure for Students**. W poleceniach poniżej
zastąp `ID_SUBSKRYPCJI_DAWIDA` jej prawdziwym ID, a nie ID konta Jakuba:

```bash
python infra/azure/deploy.py --subscription ID_SUBSKRYPCJI_DAWIDA --admin dawidhnat --render-only
python infra/azure/deploy.py --subscription ID_SUBSKRYPCJI_DAWIDA --admin dawidhnat --validate-only
python infra/azure/deploy.py --subscription ID_SUBSKRYPCJI_DAWIDA --admin dawidhnat
```

Na Linuxie/macOS użyj `python3`, jeśli tak nazywa się zainstalowany Python.
Skrypt tworzy grupę `fleet-flow-dev-rg`, sieć, VM i harmonogramy oszczędzania
kredytu: pon.–pt. 15–22, sobota 8–21, niedziela 12–21, czas polski.
Sprawdza, czy subskrypcja jest aktywna, studencka i ma włączony limit wydatków.
Musisz mieć uprawnienia do tworzenia tych zasobów i przypisań ról Azure RBAC.
Nowa VM od razu działa do najbliższej ręcznej lub zaplanowanej dealokacji.
Pierwszy test SSH wykonaj podczas działania VM.

Przy ograniczeniu regionu lub rozmiaru maszyny wybierz wartości dostępne w
Twojej subskrypcji przez `--location` i `--vm-size`. Na koncie Jakuba działa
`polandcentral` oraz `Standard_B2als_v2`; dostępność na Twoim koncie wymaga
osobnej walidacji.

## 4. Sprawdź SSH i przekaż nowy adres zespołowi

Po udanym wdrożeniu skrypt wypisze `publicIp`. Poczekaj na zakończenie pierwszej
konfiguracji Linuxa. Zanim zaakceptujesz nowy host w SSH, odczytaj jego publiczny
klucz przez uwierzytelniony Azure Run Command:

```bash
az vm run-command invoke --subscription ID_SUBSKRYPCJI_DAWIDA \
  -g fleet-flow-dev-rg -n fleet-flow-dev --command-id RunShellScript \
  --scripts 'ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub; cloud-init status --long' \
  --query 'value[].message' -o tsv
```

Porównaj odcisk przy pierwszym logowaniu i zastąp `NOWE_IP` prawdziwym adresem:

```bash
ssh-add ~/.ssh/fleet_flow_ed25519
ssh -i ~/.ssh/fleet_flow_ed25519 dawidhnat@NOWE_IP
```

Po zalogowaniu potwierdź zakończenie konfiguracji:

```bash
sudo cloud-init status --wait
```

Powinno zwrócić `status: done`. Następnie na swoim komputerze wykonaj test
do oddania zadania:

```bash
ssh -o BatchMode=yes -o IdentitiesOnly=yes \
  -i ~/.ssh/fleet_flow_ed25519 dawidhnat@NOWE_IP hostname; echo $?
```

Oczekiwany wynik: `fleet-flow-dev` i `0`. W PowerShell użyj `$LASTEXITCODE`
zamiast `echo $?`. Pozostali członkowie wykonują własny test, swoimi kluczami.
Zaktualizujcie IP i odcisk hosta w `DEV_SERVER.md`.

## 5. Zakończ korzystanie z serwera na koncie Jakuba

Przed recenzją upewniamy się, że serwer działa w godzinach sprawdzania zadania.
W razie potrzeby zmieniamy lub wyłączamy harmonogramy zgodnie z
[instrukcją](README.md#harmonogramy). Nie zmieniamy adresu podanego prowadzącemu
bez poinformowania go o nowym adresie.

Gdy nowy serwer oraz dostęp zespołu działają i ustalony zostanie adres
używany do recenzji, Jakub dealokuje starą VM.
Jeżeli w międzyczasie pojawiły się na niej dane aplikacji lub baza, najpierw
przenosimy je zgodnie z [pełną instrukcją migracji](README.md#przeniesienie-na-subskrypcję-dawida).

Dealokacja zatrzymuje naliczanie kosztów procesora i RAM. Dysk i adres IP nadal
kosztują, więc po sprawdzeniu nowego serwera i kopii danych właściciel starego
konta może usunąć starą grupę `fleet-flow-dev-rg`. Nie dotyczy to niezależnego
projektu `fleet-lite-rg`.

## Localhost i wspólny VPS

Frontend React, API FastAPI i PostgreSQL można rozwijać na komputerach
członków zespołu. Każda osoba korzysta wtedy z własnego `localhost`, lokalnej
bazy oraz własnego pliku `.env` poza Git. Współpracę nad kodem zapewnia GitHub.
Wspólna konfiguracja Docker Compose ułatwi później uruchamianie takiego samego
zestawu usług u każdej osoby; kod aplikacji i ta konfiguracja są dopiero do
przygotowania.

VPS służy jako wspólne środowisko testowe i do prezentacji. Zadanie z kursu
wymaga też serwera i osobnego dostępu SSH wszystkich czterech osób — praca
lokalna nie zastępuje tego kryterium. Godziny działania serwera można ograniczyć
do czasu, gdy zespół go potrzebuje. Właściciel subskrypcji może też ręcznie
wyłączać i uruchamiać serwer:

```bash
az vm deallocate --subscription ID_SUBSKRYPCJI_DAWIDA -g fleet-flow-dev-rg -n fleet-flow-dev
az vm start --subscription ID_SUBSKRYPCJI_DAWIDA -g fleet-flow-dev-rg -n fleet-flow-dev
```

SSH nie włączy wyłączonej maszyny; do startu potrzebne są uprawnienia Azure.
