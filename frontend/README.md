# Frontend Fleet-Flow

Lokalny szkielet dashboardu React + TypeScript + Vite, zadanie SCRUM-38.

## Uruchomienie

Używamy Node.js 22.18.0 i npm (wersja Node jest w `.nvmrc`). Jeśli korzystasz
z nvm, wykonaj `nvm install` i `nvm use` w tym katalogu.

```bash
cd frontend           # z głównego katalogu repozytorium
npm ci
npm run dev
```

Otwórz http://127.0.0.1:5173. Serwer nasłuchuje tylko lokalnie.
Jeżeli port jest zajęty, zakończ wcześniejszy proces lub użyj
`npm run dev -- --port 5174`. Wymagane są lokalne `.env`, API oraz konto aplikacji; VPS nie jest potrzebny.

```bash
npm test              # migracja, zapis i ograniczenia układu
npm run typecheck     # sprawdzenie typów
npm run build         # typecheck oraz build do dist/
npm run preview       # podgląd zbudowanego frontendu na 127.0.0.1:4173
```

## Co już działa

- Pulpit oraz sekcje: Mapa, Pojazdy, Serwis, Ewidencja przebiegu, Kierowcy,
  Karty paliwowe i Alerty.
- Osobny widok Mapy z listą pojazdów obok (pod mapą na małym ekranie).
  Serwis, Ewidencja przebiegu, Kierowcy, Karty paliwowe i Alerty czekają na implementację.
- Sześć niezależnych kafelków; lista, mapa i wskaźniki mają dane z API,
  pozostałe czekają na implementację.
- Motyw jasny, ciemny i zgodny z systemem; pięć akcentów i własny kolor.
- Włączanie i ukrywanie modułów, wyszukiwanie po nazwie modułu.
- Edytor Pulpitu i Mapy: chwytanie całego kafelka, podgląd miejsca upuszczenia,
  płynne przesuwanie sąsiednich kart, rozciąganie i ustawienia rozmiaru.
- Niezależne Zapisz/Anuluj oraz układy telefonu i komputera dla obu widoków.
- Opcjonalne szkło z połyskiem na kartach, przyciskach i nawigacji oraz styl klasyczny.
- Tło domyślne, galeria i własny obraz, z wyciszeniem i rozmyciem w obu stylach.
- Zapamiętywanie ustawień na urządzeniu i przywracanie domyślnych.
- Osobna strona Ustawień (`#settings`): Wygląd, Tło oraz Układ i moduły.
  Koło zębate prowadzi do tej strony; edycja układu pozostaje przy każdym widoku.
- Lokalna czcionka Inter i ikony Lucide, bez pobierania fontu z Google.

Mapa, lista i wskaźniki floty korzystają z API po zalogowaniu. Edycja przejazdów
i właściwe wykresy pozostają kolejnymi zadaniami.
Wyszukiwarka szuka nazw modułów, nie pojazdów.

## Edycja Pulpitu i Mapy

Na Pulpicie lub Mapie kliknij „Edytuj układ”. Chwyć dowolną część kafelka
poza przyciskami i polami formularzy. Podświetlony obrys pokazuje docelowe
miejsce, a sąsiednie kafelki robią przestrzeń. Prawy dolny narożnik zmienia
rozmiar. Ikona ustawień otwiera suwaki i presety, a na Pulpicie także ukrywanie.
Uchwyt z kropkami obsługuje strzałki oraz Shift + strzałki;
Enter otwiera ustawienia. „Zapisz układ” zatwierdza, „Anuluj” odrzuca szkic.
Kontrolki zastępują przycisk w nagłówku, bez dodatkowego pasa nad siatką.
Włączenie i zakończenie edycji nie przesuwają kafelków.

Rozciąganie ma krok wysokości 17 px. Minimalny rozmiar każdego kafelka
uwzględnia jego szerokość i treść, w tym zawijanie tekstu. Nagłówki,
informacje statyczne i pierwszy wiersz tabeli mieszczą się w całości;
przy większej liczbie wierszy zawartość jest przewijalna.

Motyw, akcent, tło i styl powierzchni zmieniają się od razu. Podczas edycji zmiany
widoczności widgetów Pulpitu czekają na zapis jego układu. Przejście do innej
sekcji zachowuje niezapisany szkic w pamięci; wróć do edytowanego widoku,
aby go zapisać lub anulować. Zapis Mapy nie zatwierdza szkicu Pulpitu i odwrotnie.
Odświeżenie odrzuca niezapisane szkice. Ustawienia modułów dotyczą Pulpitu;
dedykowana Mapa zawsze pokazuje mapę i listę pojazdów, z własną kolejnością
i rozmiarami. Każdy widok zapamiętuje osobny układ dla telefonu i komputera.

## Tło przestrzeni

W „Ustawieniach” → „Tło” → „Tło przestrzeni” wybierz „Galeria” albo „Własne”. Galeria zawiera miasto,
góry oraz dwa gradienty. Wyciszenie nakłada osłonę zgodną z motywem:
w jasnym rozjaśnia zdjęcie, w ciemnym je przyciemnia. Rozmycie ma zakres
0–16 px. Nagłówek i podpisy zachowują czytelne powierzchnie nawet przy 0% osłony.

Własny obraz: JPG, PNG lub WebP, do 10 MB i 40 megapikseli. Aplikacja zmniejsza
go do maksymalnie 2560 px na dłuższym boku i zapisuje przygotowany obraz
w IndexedDB. Zdjęcie i jego nazwa nie są wysyłane na serwer. Preferencje
zawierają tylko identyfikator obrazu i ustawienia wyglądu. Brak miejsca
na zapis pozwala korzystać ze zdjęcia w bieżącej sesji; panel o tym informuje.

„Usuń własne zdjęcie” usuwa zapisany obraz. „Domyślne” przywraca zwykłe tło,
a „Przywróć domyślne” resetuje preferencje; zdjęcie można później ponownie
wybrać w zakładce „Własne”. Wyczyszczenie danych przeglądarki usuwa również
lokalne zdjęcie. Ustawienia zwiększonego kontrastu lub ograniczenia
przezroczystości wyłączają dekoracyjne tło.

## Dalsza praca

Kolory i wspólne komponenty opisuje [system wyglądu](../docs/DESIGN_SYSTEM.md).
Kafelki funkcji znajdują się w `src/features/fleet`, `trips` i `analytics`.
Uzgodnij typy i odpowiedzi API z Dawidem przed podłączaniem danych.
Nie dodawaj sekretów do zmiennych `VITE_*`: trafiają one do przeglądarki.

Po zmianie uruchom testy i build i sprawdź odpowiedni widok w przeglądarce. Zmiany
wprowadzamy gałęzią zadania i PR zgodnie z [CONTRIBUTING](../CONTRIBUTING.md).

## Dane floty i logowanie — SCRUM-20

Uruchom najpierw bazę, migracje i API według backend/README.md oraz utwórz swoje
konto lokalnym poleceniem administratora. Vite przekazuje `/api` do localhost:8000.
Główny `.env` jest czytany wyłącznie dla publicznych zmiennych `VITE_*`.
Jeśli używasz portu 5174, dodaj `http://127.0.0.1:5174` do `CORS_ORIGINS`.

Po zalogowaniu lista i wskaźniki korzystają z rzeczywistych danych cache.
Filtry nazwy/rejestracji i statusu są współdzielone z mapą. Odświeżanie API co
60 s nie wywołuje dodatkowych odczytów WEBFLEET. Sesja nie trafia do localStorage;
401 usuwa widok floty. Wylogowanie unieważnia sesję w bazie. Kierowców import
nie pobiera; do czasu ręcznego przypisania lista pokazuje „Nieprzypisany”.

## Mapa Mapbox — SCRUM-21

Uzupełnij publiczny `VITE_MAPBOX_TOKEN` (`pk.`) w głównym lokalnym `.env` i
zrestartuj Vite. Publiczny token trafia do przeglądarki; ogranicz go w Mapbox
wyłącznie do adresów aplikacji i uprawnień odczytu map. Nie wpisuj tokenu `sk.`.
Dane serwera WEBFLEET i hasła pozostają poza zmiennymi `VITE_*`.

Mapa pokazuje poprawne GPS i osobne znaczniki pojazdów, bez grupowania.
Znacznik używa lokalnego zdjęcia lub ikony samochodu, z oznaczeniem statusu.
Kliknięcie nakładających się znaczników otwiera wybór konkretnego pojazdu;
klawiaturą można wybrać każdy znacznik osobno. Kliknięcie pokazuje mały podgląd;
wybór na liście przybliża pozycję i pokazuje ten sam podgląd. „Cała flota” dopasowuje
widok. Jasny/ciemny motyw zmienia styl mapy; Mapbox jest ładowany osobnym chunkiem.
Podczas edycji układu gesty mapy są wyłączone, aby chwytać cały kafelek.
Kontener reaguje na zmianę rozmiaru. Brak tokenu, WebGL lub błąd mapy nie blokuje
listy. Atrybucja Mapbox pozostaje widoczna. Dostawca map otrzymuje obszar widoku
przy pobieraniu map; użycie z lokalizacjami floty zostało zaakceptowane przez PO.

## Reset hasła — SCRUM-44

Na ekranie logowania „Nie pamiętam hasła” prosi o login i pokazuje neutralne
potwierdzenie. Link ze skrzynki otwiera osobny formularz hasła (minimum 12 znaków).
Po sukcesie token jest usuwany z adresu i trzeba zalogować się ponownie.
Administrator musi wcześniej przypisać danej osobie jej e-mail (`set-email`);
konfiguracja skrzynki nadawcy nie zastępuje adresów użytkowników.

## Panel pojazdu i dzienny widok przejazdów — SCRUM-25

Kliknięcie pojazdu na mapie lub na liście przy mapie pokazuje małą kartę
z nazwą, zdjęciem/ikoną, statusem, lokalizacją i czasem pomiaru. Podgląd nie jest
modalny: mapa pozostaje dostępna. Prędkość w km/h jest widoczna tylko dla
pojazdu w ruchu ze świeżym pomiarem; brak odczytu nie jest traktowany jako zero.
Stare pomiary mają etykietę Ostatnia lokalizacja. Krzyżyk, Escape w podglądzie
lub kliknięcie tła mapy zamyka kartę i usuwa zaznaczenie.

Frontend jest przygotowany na opcjonalne pola `make`, `model` oraz
`position_address`. Obecne API ich nie zwraca; podgląd używa nazwy pojazdu
i jawnej informacji o braku danych. Adres będzie wyświetlany po dostarczeniu
go z API razem z poprawną pozycją GPS. Nie ma nowych wywołań geokodowania.
`speed_kmh` pozostaje obecnie null zgodnie z kontraktem integracji.

Dopiero Szczegóły otwierają większe okienko z nazwą, rejestracją, statusem
i lokalnym zdjęciem (albo ikoną samochodu). Cztery zakładki
to Pojazd, Kierowca, Przegląd i Podróże. Strzałki, Home i End przełączają
zakładki; Escape zamyka panel i przywraca fokus. Panel jest wspólny dla Mapy
i kafelka mapy na Pulpicie, poza przewijaną zawartością widgetu.

W „Ostatnich przejazdach” i „Podróżach” działa wspólny wybór dnia:
Dzisiaj, Wczoraj lub konkretna data. Dni są liczone w Europe/Warsaw,
również przy zmianie czasu. Wybory względne podążają za północą, a własna
data pozostaje stała. Filtr nie dopuszcza dni przyszłych ani niepoprawnych.
Widoki mają osobny, niezapisywany wybór dnia.

Ten przyrost przygotowuje wygląd i zakładki. Ich treść oraz historia tras
i postojów czekają na dalsze ustalenia. Nie pobiera ani nie zapisuje historii
WEBFLEET i nie dodaje danych demonstracyjnych. Nagłówek pojazdu korzysta
z istniejącego API floty. Kierowcy nadal będą wprowadzani ręcznie.


## Pojazdy i personalizacja — SCRUM-45 / SCRUM-46

„Pojazdy” (`#vehicles`) pokazują dane API w kafelkach, ze wspólnymi filtrami
nazwy/rejestracji i statusu oraz paginacją. Domyślny kafelek ma 320 × 440 px.
„Edytuj układ” udostępnia zakres Wszystkie pojazdy lub Zaznaczone.
Wybór zakresu jest w nagłówku obok Zapisz/Anuluj, a poniżej są akcje
zaznaczania i lista rozmiarów (Małe, Standardowe, Duże, Własny rozmiar).
Edycja nie rozwija dodatkowego panelu nad galerią. Kliknięcie
kafelka/checkbox zaznacza go i podświetla; wybór pozostaje podczas zmiany strony
i filtrów. Można rozciągnąć narożnik wybranej grupy albo zmienić rozmiar
suwakami/presetami. Suwak zmienia jeden wymiar, preset wyrównuje oba.
Wszystkie pojazdy obejmuje całą flotę, również poza stroną i filtrami.
Minimum 280 × 420 px zostawia miejsce na zdjęcie,
status, przebieg, kierowcę i czas pomiaru. Strzałki na uchwycie zmieniają rozmiar,
a Enter otwiera suwaki. Zapis/Anuluj dotyczą wyłącznie tego widoku.

Szerokości nie rozciągają się automatycznie do całego wiersza. Mniejszy ekran
ogranicza tylko wyświetlanie szerokości, zachowując rozmiar zapisany przez
użytkownika. Układ jest zapisywany lokalnie i osobno dla kont aplikacji.
Odczyt starszych rozmiarów jest zachowany; nowy zapis v2 obejmuje domyślny
rozmiar floty oraz indywidualne nadpisania.

Wspólny `ListPagination` jest na dole listy, po prawej: 10/25/50/100 elementów,
zakres wyników i strony. W galerii znajduje się pod ostatnim rzędem kafelków,
w widgetach jest poza przewijaną treścią. Limit jest wspólny dla galerii,
tabeli i listy przy mapie, zapamiętany lokalnie dla konta. Zmiana limitu wraca
na stronę 1 i nie ogranicza pojazdów z GPS wyświetlanych na mapie.

Ikona aparatu dodaje, zastępuje lub usuwa zdjęcie, wspólne dla kafelka i mapy.
JPG/PNG/WebP do 10 MB są lokalnie zmniejszane do 1024 px, ponownie kodowane bez
metadanych i zapisane w IndexedDB dla danego konta. Zdjęcia zapisują się od razu,
niezależnie od szkicu układu. Nie trafiają do API ani Mapbox i nie są jeszcze
współdzielone z zespołem. Usunięcie danych przeglądarki usuwa lokalne zdjęcia.
Błąd zdjęcia przywraca ikonę samochodu; brak miejsca pozwala użyć zdjęcia w sesji.

Ustawienia są osobną stroną z podziałem konfiguracji. Wygląd i tło zapisują się
od razu. Widoczność modułów podczas edycji Pulpitu pozostaje szkicem do zatwierdzenia
na Pulpicie. Reset ustawień przywraca wygląd oraz układy Pulpitu i Mapy;
rozmiary Pojazdów resetuje się osobno podczas edycji tej sekcji.
