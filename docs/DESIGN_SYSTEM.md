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
| `--muted` | `#63758a` | `#a1b1c6` | opisy |
| `--border` | `#e3ebf3` | `#253247` | podziały i obramowania |
| `--accent` | `#1479e8` domyślnie | kolor użytkownika | aktywne elementy |
| `--success` | `#138c76` | jaśniejszy turkus | stan poprawny |

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
  ikonę, komponent i grupy nawigacji. Panel ustawień korzysta z tego samego rejestru.

Dodanie modułu:

1. Uzgodnij zakres w Jirze i utwórz komponent w odpowiednim module domeny.
2. Dodaj trwałe ID w `widget-types.ts` i definicję w `widget-registry.ts`.
3. Użyj `WidgetFrame` i wspólnych tokenów. W `widget-layout.ts` dodaj grupy
   nawigacji oraz domyślne rozmiary dla obu profili. W `widget-sizing.ts`
   ustal budżet minimalnej szerokości i wysokości treści. Komponent
   dostosowuje zawartość do szerokości kontenera, nie tylko okna przeglądarki.
4. Obsłuż brak danych, ładowanie i błąd, gdy moduł otrzyma API.
5. Sprawdź jasny i ciemny motyw, wybrany akcent, mały ekran i klawiaturę.

ID istniejących modułów nie zmieniaj bez migracji preferencji. Kafelki należą
do `fleet`, `trips` lub `analytics`; dashboard odpowiada za ich kompozycję.
Wywołania API należy później wydzielić do wspólnego klienta, bez sekretów
WEBFLEET w przeglądarce. Przy równoległej pracy uzgodnij zmiany rejestru
i arkusza stylów z osobą pracującą w tych samych plikach.

## Preferencje i dostępność

`app/preference-model.ts` waliduje `theme`, `accent`, `material`,
`visibleWidgets` i `layouts`. Hook `app/preferences.ts` zapisuje je w
`fleet-flow.dashboard.v2` w localStorage; odczyt starszego klucza v1 zachowuje
motyw, akcent i widoczność. Są to preferencje przeglądarki bez synchronizacji
pomiędzy urządzeniami. Zablokowany zapis działa w pamięci sesji.
Nieznane ID, duplikaty i niepoprawne rozmiary są odrzucane lub ograniczane.
Ukrycie wszystkich modułów jest dozwolone; można je ponownie włączyć.

### Edytowanie układu

„Dopasuj widok” → „Edytuj układ” otwiera szkic. Uchwyt z kropkami przesuwa,
narożnik rozciąga, a przycisk ustawień otwiera szerokość, wysokość i ukrycie.
„Zapisz układ” zatwierdza szkic, „Anuluj” odrzuca kolejność, rozmiary i zmiany
widoczności wykonane podczas edycji. Wygląd (motyw, materiał, akcent) działa
od razu. Reset w trybie edycji też wymaga zatwierdzenia układu.

Każda grupa nawigacji ma osobny układ dla dużych i małych ekranów. Zmiana
na telefonie nie nadpisuje desktopu. Widoczność jest wspólna dla grup;
ukryty kafelek zachowuje rozmiar. Tylko widoczny podzbiór jest zagęszczany,
co chroni zapisany widok przed zmianą pozycji po odświeżeniu.

Układ obsługuje `react-grid-layout` v2. Zapis używa 12 kolumn i logicznego
rzędu 18 px z przerwą 16 px, z dokładnością do połowy jednostki. Silnik
interakcji otrzymuje dwukrotnie gęstszą siatkę (24 kolumny i rząd 1 px),
co zachowuje geometrię starszych zapisów i zmniejsza skok wysokości do 17 px.
Model `widget-layout.ts` odpowiada za konwersję, walidację i kolizje.

`widget-sizing.ts` przechowuje budżety treści, zależne od szerokości kafelka.
`useWidgetMinimums` mierzy naturalną zawartość `.widget-content-inner`,
nagłówek, a w tabeli nagłówki kolumn i pierwszy wiersz. Kolejne wiersze
pozostają przewijalne. Mapa korzysta z minimalnej wysokości płótna z CSS.
Pomiar może podnieść minimum, również ponad zwykły limit suwaka, gdy
pierwszy rekord jest wysoki. Pusty stan też mieści się w całości.

Jeden ResizeObserver grupuje pomiary w jednej klatce animacji. Podczas
gestu pomiary są wstrzymane; ograniczenie rozmiaru zależne od szerokości
działa w silniku, a pomiar treści odświeża się po puszczeniu uchwytu.
Komponenty domeny są memoizowane. Kontrolki zajmują miejsce w nagłówku,
bez osobnego pasa zmniejszającego treść. Nie dodawaj zależności od
kontrolera edytora w komponentach domeny.

Uchwyt obsługuje strzałki (przesunięcie), Shift + strzałki (rozmiar) i Enter
(ustawienia). Ustawienia mają także suwaki, presety i przyciski kierunku.
Ruch ogłaszany jest przez region statusu. Dialogi używają natywnego fokusu
modalnego i Escape. `prefers-reduced-motion` wyłącza animację kafelków.

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

Przyciski mają nazwy, elementy interaktywne widoczny fokus, panel używa
natywnego `dialog` z obsługą Escape i ograniczeniem fokusu. Zachowuj
`prefers-reduced-motion` i opisy tekstowe przy ikonach. Po zmianie modelu
wykonaj `npm test`; testy sprawdzają migrację, granice układu, kolizje i
zapis z ukrytymi modułami. Po zmianie UI wykonaj build i sprawdzenie
przeglądarki na dużym i małym ekranie.
