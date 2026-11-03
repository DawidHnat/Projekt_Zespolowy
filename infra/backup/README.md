# Cykliczny backup - SCRUM-84

Przyrost audytu z 27.10.2026. Kod jest gotowy do review; nie oznacza uruchomienia
backupu na VPS ani odbioru SCRUM-84. Przed aktywacją właściciel wskazuje niezależne
repozytorium, koszt, opiekuna klucza oraz akceptuje RPO/RTO. Nie zamawiamy storage.

`backup.py` wymaga Pythona 3.12+, Docker Compose i restic 0.17+. Wykonuje spójny
`pg_dump -Fc`, zapisuje manifest SHA-256 i SHA wydania, wysyła do szyfrowanego
repozytorium restic, pobiera tę konkretną kopię i sprawdza sumę. Dopiero po tym
wykonuje `restic check` i retencję: 7 kopii dziennych, 4 tygodniowe i 6 miesięcznych.
Zrzut jest tymczasowy, w katalogu 0700; po operacji zostaje usunięty. Blokada pliku
wyklucza nakładanie backupu i restore. Kopia przed deploymentem działa osobno.

Obecna aplikacja nie przechowuje przesłanych plików na serwerze: zdjęcia są w
przeglądarce. Nie są objęte backupem PostgreSQL. Przed wdrożeniem dokumentów lub
zdjęć współdzielonych trzeba rozszerzyć manifest o ich storage i zapewnić spójny
punkt odtworzenia bazy oraz plików. Nie kopiujemy całego katalogu aplikacji ani
sekretów do archiwum danych. Sekrety wdrożenia i hasło restic wymagają osobnego
bezpiecznego magazynu dostępnego także po utracie VPS.

## Instalacja po review

1. Utwórz repozytorium u innego dostawcy / na innym koncie niż VPS. Użyj HTTPS,
   ograniczonego konta storage i osobnego hasła restic. Zachowaj klucz odtwarzania
   poza VPS. Lokalna ścieżka jest celowo odrzucana. Sam adres sieciowy nie dowodzi
   niezależności storage - potwierdza ją administrator.
2. Zainstaluj sprawdzone wydanie restic i PostgreSQL 17 image. Zweryfikuj sumę
   pobranego programu. Zainstaluj `backup.py` do `/opt/fleet-flow/backup/` jako
   root:root 0755, jednostki do `/etc/systemd/system/` jako root:root 0644.
3. Prywatnie utwórz `/etc/fleet-flow/backup.env` na podstawie szablonu i plik
   `/etc/fleet-flow/restic-password`, oba root:root 0600, katalog 0700. Dla sftp
   skonfiguruj zweryfikowany host key; nie wyłączaj sprawdzania TLS/SSH.
4. Załaduj te zmienne w prywatnej sesji administratora i wykonaj jednorazowe
   `restic init`. Narzędzie nie tworzy automatycznie repozytorium po błędzie sieci.
5. `systemctl daemon-reload`, następnie `systemctl start fleet-flow-backup`.
   Po sukcesie `systemctl start fleet-flow-restore-check`.
6. Po odebranej próbie włącz timery:
   `systemctl enable --now fleet-flow-backup.timer fleet-flow-restore-check.timer`.

Backup startuje co 6 h UTC, z opóźnieniem losowym do 5 min. Miesięczny test
odtwarzania uruchamia **oddzielny, tymczasowy PostgreSQL** bez sieci, portów i
trwałego wolumenu. Pobiera dump ze storage, sprawdza SHA-256, wykonuje pełne
`pg_restore --exit-on-error`, sprawdza tabele i usuwa kontener. Nie zmienia bazy
aplikacji. Miesięczny lokalny test nie zastępuje próby po utracie całego VPS.

## Odtworzenie poza VPS

Na nowej maszynie z Pythonem, Dockerem, obrazem PostgreSQL 17 i restic, bez
aplikacyjnej bazy i katalogu `current`, ustaw prywatnie dostęp do repozytorium:

```bash
python3 /opt/fleet-flow/backup/backup.py restore-check
# Lub konkretne ID snapshotu z restic snapshots --tag fleet-flow-postgres:
python3 /opt/fleet-flow/backup/backup.py restore-check ID_SNAPSHOTU
```

Nie podawaj ID jako części polecenia shell pochodzącej z niezaufanego tekstu.
Repozytorium wybierane jest przez środowisko; `latest` jest ograniczone tagiem
`fleet-flow-postgres`. Dla kilku deploymentów używaj osobnych repozytoriów/prefiksów.
Pełne przywrócenie usługi wykonuje administrator: osobna nowa baza, restore,
migracje do SHA wydania, uruchomienie API i smoke logowania/floty. Bez automatycznego
nadpisywania działającej bazy. Zmierz rzeczywiste RPO/RTO i sprawdź relacje danych.

## Status i odbiór

Nieudane polecenie kończy się kodem 1 i bezpiecznym kodem błędu w journalu.
Nie wypisuje URL storage, stderr dostawcy, danych bazy ani zmiennych środowiska.
`/var/lib/fleet-flow-backup/last-backup.json` i `last-restore.json` są atomowymi
znacznikami **ostatniego pełnego sukcesu**; awaria ich nie odświeża. Podłącz
monitoring systemd failed oraz alarm wieku backupu >7 h i restore >32 dni.
Nie ma jeszcze centralnego odbiornika alarmów; to warunek uruchomienia operacyjnego.

Protokół QA: UTC, SHA kodu, środowisko, ID snapshotu, wiek punktu kopii, czas
odtworzenia, wynik PASS/FAIL/BLOCKED i właściciel. Bez rekordów klienta i sekretów.
Wymagane: brak dostępu do storage, nieudany dump, uszkodzona suma, nieudany restore,
równoległe uruchomienie, retencja i pełne odtworzenie **na innym hoście**.

Testy automatyczne: `cd backend && pytest tests/test_backup_operations.py`.
Opcjonalny lokalny test z prawdziwym restic i Dockerem, wyłącznie syntetyczne dane:
`BACKUP_INTEGRATION_TEST=true pytest tests/test_backup_operations.py`.

Źródła: [backup restic](https://restic.readthedocs.io/en/stable/040_backup.html),
[backup PostgreSQL](https://www.postgresql.org/docs/17/backup-dump.html).
