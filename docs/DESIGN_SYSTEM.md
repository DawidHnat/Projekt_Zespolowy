# Wygląd i moduły Fleet-Flow

Pierwsza implementacja (SCRUM-38) ustala wygląd dashboardu inspirowany
referencją zespołu. Przyjęto Inter, jasne tło, niebieski akcent i turkusowy
kolor statusu sukcesu. Motyw i akcent są niezależne od zawartości kafelków.

## Wspólne tokeny

Źródło: `frontend/src/app/tokens.css`. Używaj zmiennych CSS zamiast
wpisywania kolorów w komponentach. Motyw zmienia `data-theme` elementu
`html`, a akcent zmienia zmienne `--accent` i `--accent-on`.

| Token | Motyw jasny | Motyw ciemny | Zastosowanie |
| --- | --- | --- | --- |
| `--background` | `#f3f7fb` | `#0b121e` | tło aplikacji |
| `--surface` | `#ffffff` | `#131e2e` | karty i panel |
| `--text` | `#192a42` | `#e7eef8` | główna treść |
| `--muted` | `#596b80` | `#a1b1c6` | opisy |
| `--border` | `#e3ebf3` | `#253247` | podziały i obramowania |
| `--accent` | `#1479e8` domyślnie | kolor użytkownika | aktywne elementy |
| `--success` | `#10725f` | jaśniejszy turkus | stan poprawny |

`--accent-on` wybiera czarny lub biały tekst zgodnie z luminancją akcentu.
Nie używaj akcentu jako jedynego znaczenia błędu lub sukcesu. Status ma też
opis i ikonę. Kolor tekstu na dodatkowych tłach wymaga sprawdzenia kontrastu.

Font Inter jest dostarczany lokalnie z pakietu npm. Wielkości, odstępy,
siatka i responsywność są we wspólnych arkuszach `app/`. Promień karty
wynosi 12 px w stylu klasycznym i 18 px w stylu szkła. Kafelki układają się
w siatce 12 kolumn, poniżej 720 px szerokości kontenera w jednej.
Przyciski zachowują ten sam rozmiar i promień w obu materiałach: nawigacja
14 px, zwykłe przyciski 12 px. Materiał zmienia ich powierzchnię.
Nowy wariant komponentu dopisuj wspólnie, zamiast kopiować style do modułu.

## Komponenty i rejestr

- `Brand` składa wybrany przez zespół monogram FF ze strzałką i napis
  „Fleet Flow”. Jeden plik `frontend/public/brand/fleet-flow-mark.svg` służy
  jako znak w nawigacji i favicon. SVG ma przezroczyste tło, a w ciemnym
  motywie rozjaśnia najciemniejsze fragmenty. Napis korzysta z lokalnego
  Inter; `Fleet` używa `--text`, a `Flow` tokenu `--brand-wordmark`.
  Kolory marki są stałe i niezależne od personalizacji `--accent`.
  Nie dodawaj tła ani efektów szkła do samego znaku.
- `WidgetFrame` zapewnia tytuł, ikonę, obramowanie i przewijalną zawartość.
  Kontrolki edycji należą do `DashboardGrid`, nie do modułów domeny.
- `EmptyState` zapewnia spójny stan oczekiwania na dane.
- `features/dashboard/model/widget-registry.ts` łączy ID modułu, tytuł,
  ikonę, komponent i grupy modelu układu. Strona ustawień korzysta z tego samego rejestru.

Dodanie modułu:

1. Uzgodnij zakres w Jirze i utwórz komponent w odpowiednim module domeny.
2. Dodaj trwałe ID w `widget-types.ts` i definicję w `widget-registry.ts`.
3. Użyj `WidgetFrame` i wspólnych tokenów. W `widget-layout.ts` dodaj moduł
   do Pulpitu oraz domyślne rozmiary dla obu profili. W `widget-sizing.ts`
   ustal budżet minimalnej szerokości i wysokości treści. Komponent
   dostosowuje zawartość do szerokości kontenera, nie tylko okna przeglądarki.
4. Obsłuż brak danych, ładowanie i błąd, gdy moduł otrzyma API.
5. Sprawdź jasny i ciemny motyw, wybrany akcent, mały ekran i klawiaturę.

ID istniejących modułów nie zmieniaj bez migracji preferencji. Kafelki należą
do `fleet`, `trips` lub `analytics`; dashboard odpowiada za ich kompozycję.
Wywołania API korzystają ze wspólnego klienta `shared/api/client.ts`, bez sekretów
WEBFLEET w przeglądarce. Przy równoległej pracy uzgodnij zmiany rejestru
i arkusza stylów z osobą pracującą w tych samych plikach.

## Preferencje i dostępność

`app/preference-model.ts` waliduje `theme`, `accent`, `material`, `background`,
`visibleWidgets` i `layouts`. Hook `app/preferences.ts` zapisuje je w
`fleet-flow.dashboard.v2` w localStorage; odczyt starszego klucza v1 zachowuje
motyw, akcent i widoczność. Są to preferencje przeglądarki bez synchronizacji
pomiędzy urządzeniami. Zablokowany zapis działa w pamięci sesji.
Nieznane ID, duplikaty i niepoprawne rozmiary są odrzucane lub ograniczane.
Ukrycie wszystkich modułów jest dozwolone; można je ponownie włączyć.

### Nawigacja i strony

`app/navigation.ts` jest rejestrem sekcji aplikacji: Pulpit, Mapa, Pojazdy, Serwis,
Ewidencja przebiegu, Kierowcy, Karty paliwowe, Alerty i Ustawienia. Nowa strona ma trwałe
ID, polski tytuł, ikonę i opis. `WorkspacePage` zapewnia wspólny pusty widok
sekcji planowanych. Logikę tych funkcji dodajemy w osobnych zadaniach.
Nawigacja pobiera oznaczenie „Planowane” z obecności `placeholder` w rejestrze;
to samo oznaczenie jest na stronie sekcji. Po implementacji usuń `placeholder`
i podłącz rzeczywisty widok. Nie zmieniaj przy tym trwałego ID sekcji.
Ustawienia, galeria pojazdów i dodawanie zdjęć jawnie informują o zapisie
tylko na urządzeniu i w danej przeglądarce. Zdjęcia pojazdów są dodatkowo
rozdzielone według konta, a preferencje dashboardu i jego tło należą do
przeglądarki. Nie obiecuj synchronizacji między urządzeniami (SCRUM-91).

Rejestr stron jest niezależny od `SectionId` i grup zapisanych w preferencjach układu.
Stare grupy `fleet`, `trips`, `analytics` pozostają w modelu, aby zachować
wcześniejsze zapisy. Ich linki prowadzą odpowiednio do Mapy, Ewidencji
przebiegu i Pulpitu. Link `#dashboard` nadal otwiera Pulpit.

`FleetMapPage` korzysta ze wspólnego `DashboardGrid`, z własną grupą `map`.
Domyślnie mapa zajmuje osiem kolumn, a boczny wariant listy pojazdów cztery.
Poniżej 720 px szerokości kontenera lista przechodzi pod mapę. Rejestr
widgetów może wskazać `presentations` dla konkretnej grupy: w Mapie pojazdy
mają boczną listę i własne minimum szerokości, a na Pulpicie nadal tabelę.
Ten widok pozostaje niezależny od ukrywania kafelków na Pulpicie.
Starsze preferencje v2 otrzymują domyślną grupę `map` bez zmiany innych układów.
Mapa korzysta z Mapbox i chronionego GeoJSON API. Każdy pojazd ma osobny
znacznik HTML: zdjęcie lub ikonę samochodu, opis statusu i wyróżnienie wyboru.
Nie ma klastrów ani automatycznego grupowania. `VehicleMarkers` aktualizuje
istniejące znaczniki po trwałym ID, zachowując kamerę. Kliknięcie nakładających
się znaczników pozwala wybrać konkretny pojazd; klawiaturą każdy jest dostępny
osobno. Wybór na liście i mapie jest wspólny. Brak tokenu lub WebGL pozostawia
czytelną informację oraz działającą listę. Podczas edycji układu gesty mapy
są wyłączone, aby można było chwycić cały kafelek.

`app/components/AppSettingsPage.tsx` jest osobną stroną `#settings`, dostępną
pod kołem zębatym, także na telefonie. Kategorie Wygląd, Tło oraz Układ i moduły
korzystają ze wspólnych tokenów i komponentu `BackgroundPicker`. Motyw, materiał,
akcent i tło zmieniają się od razu. Widoczność widgetów podczas edycji Pulpitu
pozostaje jego szkicem. Edycja układu jest osobnym działaniem na Pulpicie, Mapie
i Pojazdach; przejście do ustawień zachowuje szkice w pamięci.

### Kafelki i zdjęcia pojazdów — SCRUM-45 i SCRUM-46

`VehicleCardsPage` korzysta z API i wspólnych kontrolek `FleetControls`.
Kafelki mają stały indywidualny rozmiar, minimum 280 × 420, domyślnie 320 × 440,
maksimum 720 × 720 px. Flex-wrap zmienia położenie wierszy, nie zapisane rozmiary.
`useCardResize` maluje tylko aktywny kafelek w klatkach animacji i zatwierdza
rozmiar do szkicu przy puszczeniu; cancel/lost pointer capture odrzuca gest.
Przy edycji zbiorowej reszta wybranej grupy otrzymuje rozmiar przy puszczeniu,
bez przeliczania całej galerii w każdej klatce.
Suwaki i strzałki zapewniają alternatywę dla przeciągania. CSS ogranicza szerokość
na telefonie bez nadpisywania rozmiaru użytkownika.

`VehiclePreferencesProvider` udostępnia zdjęcia i niezależny szkic rozmiarów.
Klucz localStorage `fleet-flow.vehicles.v2.<user-id>` oraz IndexedDB
`fleet-flow.vehicle-photos.v1` izolują preferencje kont. Wylogowanie zwalnia URL-e
obiektowe; podmiana i usunięcie zdjęcia też je zwalniają. Upload zapisuje się
od razu, niezależnie od Zapisz/Anuluj układu. Brak zapisu ma jawny stan sesji.

`vehicle-layout.ts` przechowuje domyślny rozmiar całej floty i nadpisania
poszczególnych pojazdów. Odczyt v1 zachowuje istniejące rozmiary; zapis v2
następuje dopiero po zatwierdzeniu. Operacje na szkicu są niemutowalne.
Tryb „Wszystkie pojazdy” obejmuje całą flotę, także poza stroną i filtrami,
oraz przyszłe pojazdy. Tryb „Zaznaczone” dotyczy trwałych ID, zachowuje wybór
podczas zmiany strony i filtrów. Zaznaczenia są tylko stanem edycji, nie zapisem.
Kliknięcie treści karty oraz checkbox zaznaczają; przyciski i linki zachowują
swoją funkcję. W trybie Wszystkie kliknięcie karty rozpoczyna wybór pojedynczy.
Otwarcie rozmiaru lub narożnik niezaznaczonej karty wybiera wyłącznie tę kartę;
zaznaczona karta zmienia wybraną grupę. Suwak i strzałka wyrównują jeden wymiar,
presety i narożnik oba. Dialog opisuje zakres i mieszane rozmiary.
Zapisz/Anuluj obejmują całość szkicu. Reset także wymaga zatwierdzenia.
`VehicleLayoutEditorControls` komponuje wspólne przyciski Zapisz/Anuluj z zakresem
edycji w nagłówku Pojazdów. Zaznaczanie i wybór rozmiaru pozostają w tym samym
nagłówku; nie rozwijaj osobnego panelu w filtrach nad galerią. Lista rozmiarów
oferuje presety oraz dialog własnego rozmiaru. Kontrolki zawijają się na telefonie.

### Wspólna paginacja list — SCRUM-46

`shared/components/ListPagination` jest niezależny od domeny. Przyjmuje stronę,
limit, liczbę wyników, stan ładowania i callbacki. Pokazuje zakres i wybór
10/25/50/100, także dla pustego wyniku i jednej strony. Kontrolki są na dole
po prawej, poza przewijaną zawartością; zawijają się w małym kontenerze.
W galerii paginacja jest w zwykłym przepływie pod ostatnim rzędem kafelków,
bez przyklejania do krawędzi okna ani nakładania na pojazdy.
Ładowanie blokuje kolejne żądania z kontrolek. Zakres nie przekracza liczby
wyników. `pagination-model.ts` ogranicza wartości zgodnie z limitem API.

`FleetProvider` dzieli limit między galerią, tabelą i listą Mapy. Zmiana limitu
wraca na stronę 1. Preferencja limitu jest lokalna dla konta pod kluczem
`fleet-flow.list-page-size.v1.<user-id>`; brak localStorage pozostawia stan sesji.
Filtrowanie i mapowanie floty pozostają niezależne od stronicowania listy.
`useWidgetMinimums` uwzględnia footer i pierwszy rekord, a dla pustej listy
mierzy komunikat zamiast rozciągniętego kontenera, aby uniknąć pętli wzrostu.
Nowe rzeczywiste listy powinny używać tego komponentu; puste sekcje planowane
nie otrzymują sztucznej paginacji.

Wspólne `shared/media` waliduje format i limity obrazu oraz koduje go ponownie
bez metadanych. Zdjęcia pojazdów mają maksymalny bok 1024 px, tła 2560 px.
Mapa i karty używają tego samego URL-a blob; zdjęcia nie trafiają do dostawcy map
ani na serwer. Udostępnienie zdjęć zespołowi wymaga osobnego zadania backendu.
`vehicle-fallback.svg` i gradient karty zapewniają zastępczy wygląd, również po
błędzie odczytu obrazu. Nie zapisuj prawdziwych zdjęć lub pozycji klientów w repo.

### Edytowanie układu

Kwadratowy przycisk z kropkami (48 × 48 px, ikona Grip 24 px) na Pulpicie,
Mapie i Pojazdach otwiera szkic tego widoku. Nazwa „Edytuj układ” jest w
podpowiedzi oraz `aria-label`; powierzchnia korzysta ze wspólnego akcentu i materiału.
Cały kafelek można chwycić poza przyciskami, linkami i polami formularzy.
Narożnik rozciąga, a przycisk ustawień otwiera szerokość, wysokość i ukrycie
(ukrycie jest dostępne tylko na Pulpicie).
„Zapisz układ” zatwierdza szkic, „Anuluj” odrzuca kolejność, rozmiary i zmiany
widoczności wykonane podczas edycji. Wygląd (motyw, materiał, akcent, tło) działa
od razu. Reset w trybie edycji też wymaga zatwierdzenia układu.

`app/useLayoutEditor.ts` zarządza niezależnymi szkicami obu widoków.
`layout-draft.ts` tworzy szkic i zatwierdza wyłącznie wybrany widok do bieżących
preferencji. Zapis Mapy nie nadpisuje ustawień wyglądu ani szkicu Pulpitu.
`LayoutEditorControls` zastępuje przycisk edycji kontrolkami w nagłówku.
Slot ma tę samą szerokość i wysokość w obu trybach, także w mobilnym wierszu
akcji. Nie dodawaj osobnego pasa ani komunikatów w przepływie nad siatką:
wejście w edycję i zapis muszą zachować jej położenie. Informacja o profilu
ekranu pozostaje dostępna dla czytników ekranu.

Pulpit i Mapa mają osobne układy dla dużych i małych ekranów. Zmiana
na telefonie nie nadpisuje desktopu. Widoczność dotyczy kafelków Pulpitu;
ukryty kafelek zachowuje rozmiar. Tylko widoczny podzbiór jest zagęszczany,
co chroni zapisany widok przed zmianą pozycji po odświeżeniu.

Układ obsługuje `react-grid-layout` v2. Zapis używa 12 kolumn i logicznego
rzędu 18 px z przerwą 16 px, z dokładnością do połowy jednostki. Silnik
interakcji otrzymuje dwukrotnie gęstszą siatkę (24 kolumny i rząd 1 px),
co zachowuje geometrię starszych zapisów i zmniejsza skok wysokości do 17 px.
Model `widget-layout.ts` odpowiada za konwersję, walidację i kolizje.

`useGesturePaint` grupuje odświeżanie trzymanego kafelka w klatkach animacji.
RGL v2 przechowuje pikselową pozycję w refie i memoizuje kartę według komórek
siatki; zmiana tożsamości tylko aktywnego dziecka pozwala malować również
ruch wewnątrz komórki. Pozostałe dzieci i konfiguracja siatki pozostają
stabilne, a silnik nadal obsługuje pozycję, kolizje i przewijanie przy krawędzi.
Podgląd przeciągania wyznacza obrys po zagęszczeniu układu, zgodnie z miejscem
zatwierdzanym przy puszczeniu. Sąsiednie karty animują zmianę położenia;
trzymana karta porusza się bez przejścia CSS, aby nadążać za kursorem.

`widget-sizing.ts` przechowuje budżety treści, zależne od szerokości kafelka.
`useWidgetMinimums` mierzy naturalną zawartość `.widget-content-inner`,
nagłówek, a w tabeli nagłówki kolumn i pierwszy wiersz. Kolejne wiersze
pozostają przewijalne. Mapa korzysta z minimalnej wysokości płótna z CSS.
Pomiar może podnieść minimum, również ponad zwykły limit suwaka, gdy
pierwszy rekord jest wysoki. Pusty stan też mieści się w całości.

Jeden ResizeObserver grupuje pomiary w jednej klatce animacji. Podczas
gestu pomiary są wstrzymane; ograniczenie rozmiaru zależne od szerokości
działa w silniku, a pomiar treści odświeża się po puszczeniu kafelka.
Komponenty domeny są memoizowane. Kontrolki zajmują miejsce w nagłówku,
bez osobnego pasa zmniejszającego treść. Nie dodawaj zależności od
kontrolera edytora w komponentach domeny.

Uchwyt obsługuje strzałki (przesunięcie), Shift + strzałki (rozmiar) i Enter
(ustawienia). Ustawienia mają także suwaki, presety i przyciski kierunku.
Ruch ogłaszany jest przez region statusu. Dialogi używają natywnego fokusu
modalnego i Escape. `prefers-reduced-motion` wyłącza animację kafelków.

### Tło przestrzeni

Tło jest niezależne od `solid` / `glass`; karty w klasycznym materiale
pozostają nieprzezroczyste. `DashboardBackground` renderuje jedną nieruchomą,
dekoracyjną warstwę pod aplikacją, bez animacji i bez ingerencji w widgety.
`backgrounds.css` odpowiada za osłonę zgodną z motywem, rozmycie, kadrowanie
`cover` i czytelne powierzchnie nagłówka i etykiety wskaźników.
Nie stosuj efektów tła do zawartości kafelków. Tryby zwiększonego kontrastu,
forced-colors i ograniczenia przezroczystości wyłączają dekorację.
Przy własnym tle powierzchnie nawigacji i panelu szkła mają 90% wypełnienia,
a opisy używają tokenu `--wallpaper-muted` (`#53657a` w jasnym,
`#a1b1c6` w ciemnym), aby zachować czytelność również przy 0% osłony zdjęcia.

`background-model.ts` definiuje galerię, domyślne ustawienia i walidację
zakresów. Nowe preferencje mieszczą się w zapisie v2; starsze zapisy
otrzymują domyślne tło, zachowując układ. Nie przyjmuj adresów obrazów
z localStorage. Galeria korzysta z lokalnych zdjęć i gradientów CSS;
pochodzenie i prompty są w `frontend/public/backgrounds/README.md`.

`background-image.ts` dekoduje plik JPG/PNG/WebP, ogranicza rozmiar do 10 MB,
40 megapikseli i 2560 px na dłuższym boku. Canvas zapisuje nowy bitmapowy
obraz bez metadanych oryginału. Blob trafia do IndexedDB `fleet-flow.media.v1`,
do pojedynczego wpisu `custom`. URL obiektowy jest zwalniany po zmianie
obrazu lub odmontowaniu. Preferencje przechowują UUID, a nie obraz.

`useBackgroundImage` zarządza odtworzeniem, przygotowaniem i usunięciem
obrazu; `BackgroundPicker` odpowiada za wybór i kontrolki. Błąd dekodowania
nie usuwa wcześniejszego zdjęcia. Błąd zapisu pozwala używać nowego obrazu
w sesji. UUID zapobiega przywróceniu starszego zdjęcia po nieudanym zapisie.
Brak blobu pozostawia zwykłe tło i możliwość ponownego dodania obrazu.
Reset przywraca preferencje, a przycisk usuwania osobno kasuje zapisany blob.

### Szkło i czytelność

`data-material` przełącza `glass` / `solid`. Arkusz `app/glass.css` stosuje
przezroczystość i blur głównie w nawigacji, nagłówku i panelach. Połysk,
jasne krawędzie i delikatny cień obejmują też aktywną nawigację, przyciski
i kolorowe ikony. Karty mają
mocne tło, żeby dane pozostały czytelne. To efekt CSS inspirowany materiałami
Apple; nie implementacja natywnego Liquid Glass.

Brak obsługi backdrop-filter, ograniczenie przezroczystości, zwiększony
kontrast lub forced-colors przywracają pełne tło. Nie dodawaj kolejnych
warstw blur ani ciągłej animacji szkła. Kierunek projektu opiera się na
[wytycznych materiałów Apple](https://developer.apple.com/design/human-interface-guidelines/materials).

Motyw systemowy korzysta z
[`prefers-color-scheme`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-color-scheme)
i reaguje na jego zmianę. Właściwość
[`color-scheme`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/color-scheme)
dopasowuje natywne kontrolki do wybranego motywu.

Przyciski mają nazwy, elementy interaktywne widoczny fokus, dialogi rozmiaru i zdjęcia używają
natywnego `dialog` z obsługą Escape i ograniczeniem fokusu. Zachowuj
`prefers-reduced-motion` i opisy tekstowe przy ikonach. Po zmianie modelu
wykonaj `npm test`; testy sprawdzają migrację, granice układu, kolizje i
zapis z ukrytymi modułami. Po zmianie UI wykonaj build i sprawdzenie
przeglądarki na dużym i małym ekranie.

### Panel pojazdu i wybór dnia

`VehicleDetailsDialog` korzysta z natywnego `dialog` i wspólnej powierzchni
dialogów. Jest montowany raz w aplikacji, poza siatką i przewijanymi kartami.
`FleetProvider.select` wybiera pozycję i pokazuje niemodalny `VehicleMapPreview`.
`inspect` otwiera większy panel dopiero po kliknięciu Szczegóły.
Ładowanie innego pojazdu nie pokazuje danych poprzednika.
Zamknięcie zachowuje zaznaczenie na mapie, ale ponowne otwarcie zaczyna od
zakładki Pojazd. Zmiana filtrów zamyka panel.

Podgląd używa wspólnego zdjęcia, statusu i materiału. Model `vehicle-preview.ts`
obsługuje brak marki/modelu/adresu i nie pokazuje starej ani niepoprawnej
prędkości jako bieżącej. Opcjonalne `make`, `model`, `position_address` są
przygotowaniem frontendu do kolejnego przyrostu API, nie zmianą backendu.
Adres należy do pozycji pomiaru; bez poprawnego GPS nie jest prezentowany
jako lokalizacja pojazdu. Kliknięcie tła mapy usuwa wybór; Escape w karcie
i krzyżyk zamykają ją z przywróceniem fokusu do mapy. Po otwarciu karty
fokus umożliwia przejście Tab do zamknięcia i Szczegółów. Odświeżenie danych
tego samego pojazdu nie przenosi fokusu ponownie.

Karta jest w lewym dolnym rogu mapy, nad atrybucją. Zapytanie kontenerowe dla
niskiej mapy zmniejsza odstępy i czasowo ukrywa licznik/Cała flota, aby nie
nakładały się na podgląd. Długi tekst pozostaje dostępny przez przewijanie.
W edycji układu podgląd jest ukryty, aby nie blokował chwytania mapy.
Przy przybliżeniu kamera zostawia wybrany znacznik obok karty na szerokiej
mapie lub nad nią na wąskiej.

Zakładki mają powiązane `tab`/`tabpanel`, jeden element w kolejności Tab,
obsługę strzałek, Home i End. Nagłówek używa wspólnego `VehiclePhoto` i tokenów
statusu. Na telefonie ikony są nad etykietami, a kontrolki dnia zawijają się
bez poziomego przewijania. Zachowuj wspólne kolory motywu, materiał i fokus.

`TripDayPicker` jest wspólny dla kafelka przejazdów i zakładki Podróże.
Model `trip-day.ts` obsługuje dni kalendarzowe w Europe/Warsaw, a `useTripDay`
odświeża wybory Dzisiaj/Wczoraj po polskiej północy i powrocie do karty.
Natywne pole daty ma opis i ograniczenie do dzisiaj. Puste stany pozostają
jednoznaczne do czasu podłączenia rzeczywistej historii; nie pokazuj
przykładowych tras jako danych floty.

### Kontrast i fokus panelu (SCRUM-107)

Stopka wersji oraz opisy fallbacku mapy używają `--wallpaper-muted`, aby zachować
kontrast nad jasnym tłem. Panel pojazdu stosuje ten sam token dla opisów nad szkłem.
Aktywna zakładka ma tekst `--text` i podkreślenie `--accent`; jej czytelność nie
zależy od wybranego koloru akcentu. Jasny motyw używa ciemniejszych tokenów tekstowych: muted #596b80, success #10725f, warning #8f570b oraz danger #b83e57.
Dialog zawija Tab/Shift+Tab między widocznymi kontrolkami, a Escape zachowuje
potwierdzenie niezapisanego szkicu i przywraca fokus do otwarcia.

### Alerty dziennego dystansu — SCRUM-32

`AlertsPage` podłącza rzeczywistą listę i reguły; `alerts` nie ma już
`placeholder` ani oznaczenia Planowane. `AlertRows` rozróżnia odczyt tekstem,
nie samym kolorem. Formularz reguły i wybór pojazdu korzystają ze wspólnych
przycisków, tokenów i ListPagination, także wewnątrz formularza (type=button).
Istniejący widget `activity` pokazuje liczbę nieprzeczytanych dla konta oraz
trzy najnowsze alerty. Rejestr i ID układu pozostają zgodne ze starszym zapisem.
