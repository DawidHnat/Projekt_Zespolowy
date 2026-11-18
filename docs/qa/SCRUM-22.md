# SCRUM-22 — aktualność pozycji i synchronizacja

Przyrost w [PR #67](https://github.com/DawidHnat/Projekt_Zespolowy/pull/67).
Backend odczytuje WEBFLEET domyślnie co 60 s, widoczny frontend nasze API
co 10 s, a próg starego pomiaru wynosi domyślnie 900 s. Są to oddzielne
ustawienia. Przyrost nie zmienia konfiguracji ani czasu pomiaru źródłowego.

„Ostatni znany stan” zastępuje ogólną etykietę „Dane nieaktualne”.
Przy pojeździe widać wiek jego `position_at`, a po wskazaniu czasu pełną
datę w Europe/Warsaw. Czas synchronizacji pozostaje osobną informacją.
Udana synchronizacja nie odmładza starej pozycji i nie potwierdza obecnego
ruchu/postoju. Błąd źródła ma oddzielne ostrzeżenie.

## Scenariusze odbioru SCRUM-23

Na komputerze i telefonie, w jasnym i ciemnym motywie:

1. Udana synchronizacja z pozycją sprzed 18 min: „Pozycja sprzed 18 min”,
   „Ostatni znany stan” oraz osobny czas synchronizacji. Galeria, lista przy
   mapie i tabela Pulpitu pokazują czas pozycji.
2. Podgląd mapy bez prędkości: bez powtarzanego „Brak odczytu prędkości”.
   Lista przy mapie pomija pustą prędkość; tabela zachowuje „Brak danych”.
3. Nowy świeży pomiar w następnym cyklu: status „W ruchu” i nowy wiek
   bez przeładowania oraz bez utraty wyboru pojazdu.
4. Syntetyczny, poprawny odczyt 42 km/h i 0 km/h: widoczna liczba i jednostka.
5. Awaria źródła: osobne ostrzeżenie WEBFLEET, zachowana ostatnia pozycja,
   prędkość z nieaktualnego odczytu ukryta w podglądzie i liście, brak bieżącej
   wartości w tabeli. Czas pozycji nie jest czasem błędu źródła.
6. Brak czasu i GPS: jawne komunikaty, bez wymyślonej daty lub lokalizacji.
7. Przyszły czas pozycji: jawny komunikat, bez ujemnego wieku.
8. Zachowanie układu na 1440 × 1000 i 390 × 844, bez poziomego przewijania.

## Walidacja autora — 18.11.2026

`npm test`: 58/58 PASS; `npm run build`: PASS; `git diff --check`: PASS.
Chromium: powyższe przypadki podglądu/galerii/listy przy mapie i tabeli Pulpitu na obu ekranach
i w obu motywach, na syntetycznych odpowiedziach naszego API, z blokadą
zewnętrznych żądań. Mapa dostawcy nie była przedmiotem tego testu.
Niezależny review i odbiór QA pozostają wymagane przed Done.

Prędkość z rzeczywistego snapshotu nadal pozostaje `null`: jednostka
`showObjectReportExtern.speed` jest otwartym punktem SCRUM-14. Usunięcie pustej
etykiety nie jest uruchomieniem odczytu prędkości. Nie odpytywano żywego
WEBFLEET ani nie zmieniano konfiguracji VPS.
