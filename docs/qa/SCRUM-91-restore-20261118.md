# SCRUM-91 — lokalna próba odtworzenia, 18.11.2026

**Wynik: PASS w opisanym środowisku.** Wykonawca: agent Codex działający
na polecenie Jakuba Czai. Dawid w odbiorze sprawdza zakres i przydatność
tego dowodu do warunku DoD; nie przypisujemy mu wykonania tej próby.

## Wersja i środowisko

- Backend gałęzi `fix/SCRUM-91-preference-isolation`, lokalny merge
  `253617c07895b38402b6d91a8b38c1701b75d1d5` z main `132fefc`.
- PostgreSQL **17.11**, tymczasowy kontener dostępny tylko przez localhost.
- Dwie oddzielne nowe bazy testowe: źródło i cel odtworzenia.
- Schemat **0007**, obejmujący preferencje z migracji **0006**.
- Jeden syntetyczny użytkownik i dwie preferencje: `dashboard` i `vehicles`,
  każda w wersji 7. Bez rzeczywistych kont, sesji i danych floty.

## Wykonana procedura

1. `alembic upgrade head` na nowej bazie źródłowej; zapis syntetycznego
   użytkownika i preferencji przez modele aplikacji.
2. `pg_dump --format=custom --no-owner` i `pg_restore --clean --if-exists
   --no-owner --no-privileges` do osobnej bazy docelowej.
3. Porównanie dokładnych wartości JSON, wersji i dat obu preferencji,
   identyfikatora użytkownika oraz wersji schematu: **PASS**.
4. `alembic downgrade 0005` w bazie docelowej: migracje 0007 i 0006 cofnięte,
   tabela preferencji usunięta, użytkownik zachowany: **PASS**.
5. `alembic upgrade head`: schemat 0007 i pusta tabela preferencji odtworzone,
   użytkownik nadal istnieje: **PASS**.
6. Ponowne `pg_restore` z tej samej kopii: oryginalny użytkownik i dokładne
   wartości, wersje oraz daty obu preferencji odzyskane: **PASS**.

Downgrade 0006 usuwa tabelę i jej dane. Sam ponowny upgrade nie odzyskuje
preferencji; odzyskanie w tej próbie zapewniło przywrócenie kopii.

SHA-256 syntetycznej kopii:
`596cfe8f3801907dc3cb4805adbd3b80bdcd2ad0ebcc45dcb5b8f8f4a7391261`.
Próba zakończona 18.11.2026 o 12:51:04 UTC.

## Zakres dowodu

Sprawdzono rzeczywiste narzędzia PostgreSQL i migracje na danych testowych.
Nie zmieniano VPS, produkcyjnej bazy ani konfiguracji usług. Ten wynik nie
potwierdza kopii off-site, harmonogramu backupu ani całej Story SCRUM-84.
Nie zastępuje niezależnego review i końcowego QA SCRUM-91. Surowy wynik,
skrypt oraz syntetyczna kopia pozostają w lokalnym pakiecie wykonawcy
`output/course-finish-20261118/`.
