# SCRUM-14 — kontrolne potwierdzenie prędkości snapshotu

18.11.2026 PO wyraźnie zlecił uruchomienie odczytu prędkości w km/h,
w tym potrzebny kontrolowany odczyt żywego WEBFLEET. Badanie wykonano
poza CI na skonfigurowanym koncie źródła. Nie zmieniano danych dostawcy.

Źródło jednostki odniesienia: [WEBFLEET.connect 1.75.0, showTracks,
strona 253](https://media.webfleet.com/fl_attachment/media/doc/documentations/webfleet.connect-doc-1.75.0.pdf#page=253):
`speed` jest nieujemną liczbą całkowitą w km/h. Tabela snapshotu nadal
nie podaje jednostki tego pola wprost; poniższy wniosek jest empiryczny.

## Metoda i wynik

- Z `showObjectReportExtern` pobrano tylko UID, prędkość, czas pozycji,
  czas wiadomości i jakość GPS. Rzeczywisty JSON zwraca prędkość jako liczbę
  albo brak wartości; konwersja tekstowej jednostki nie jest potrzebna.
- W pamięci wybrano pomiar z jakością `A`, zgodnym `pos_time` i `msgtime`
  oraz niezerową prędkością co najmniej 10. Porównano go z `showTracks`
  dla tego samego UID i dokładnie tego samego czasu, z kolumnami czasu
  i prędkości. Nie porównywano kolejnych punktów trasy jako jednego pomiaru.
- Kontrola z 15:49:31 UTC dostarczyła **jeden pełny zgodny przypadek**:
  pojedyncza wartość prędkości w historii była dokładnie równa wartości
  snapshotu. Przeliczniki mph → km/h i m/s → km/h nie pasowały do tego
  niezerowego pomiaru. Wniosek dla używanego konta: snapshot już podaje km/h,
  więc nie mnożymy ani nie dzielimy wartości.
- Wcześniejsze próby oparte tylko na czasie pozycji zawierały rozbieżności;
  nie stanowią dowodu zgodności. Przypadki bez wspólnego rekordu historii
  również nie były zaliczane. Późniejsze pobranie bez wspólnego rekordu
  nie daje dodatkowego potwierdzenia. Wynik nie jest deklaracją przebadania
  całej floty ani wszystkich kont WEBFLEET.

Nie zapisano surowych odpowiedzi, UID, nazw, lokalizacji, czasów pomiarów
ani wartości prędkości klienta. Powyższa godzina oznacza czas diagnostyki.
Żywego testu nie dodano do CI ani do cyklicznego workera. Odczyty były
ograniczone, z zachowaniem limitów akcji; nie uruchomiono ciągłego odpytywania.

## Skutek dla implementacji SCRUM-22

API przestaje bezwarunkowo zwracać `speed_kmh: null`. Udostępnia już zapisaną
liczbę km/h, jeśli pomiar jest świeży, źródło działa, GPS ma jakość `A`,
pozycja i czas są dostępne, a prędkość mieści się w 0–300. Wartość `0`
jest poprawnym odczytem, a brak wartości nie jest zastępowany zerem.
Stare, przyszłe lub niepotwierdzone odczyty pozostają `null`.

Nie powstają dodatkowe wywołania dostawcy w działającej aplikacji.
Backend nadal synchronizuje co 60 s, a frontend odczytuje cache co 10 s.
Potwierdzenie autora oraz implementacja wymagają niezależnego review i QA;
ten zapis nie oznacza wdrożenia ani zamknięcia całego SCRUM-14.
