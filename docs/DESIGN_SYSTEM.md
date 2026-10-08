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
siatka i responsywność są we wspólnym `app/styles.css`; promień karty
wynosi 12 px. Kafelki układają się w siatce 12 kolumn, na telefonie w jednej.
Nowy wariant komponentu dopisuj wspólnie, zamiast kopiować style do modułu.

## Komponenty i rejestr

- `WidgetFrame` zapewnia tytuł, ikonę, obramowanie i przycisk ukrycia.
- `EmptyState` zapewnia spójny stan oczekiwania na dane.
- `features/dashboard/model/widget-registry.ts` łączy ID modułu, tytuł,
  ikonę, komponent i grupy nawigacji. Panel ustawień korzysta z tego samego rejestru.

Dodanie modułu:

1. Uzgodnij zakres w Jirze i utwórz komponent w odpowiednim module domeny.
2. Dodaj trwałe ID w `widget-types.ts` i definicję w `widget-registry.ts`.
3. Użyj `WidgetFrame` i wspólnych tokenów. Dobierz szerokość przez klasę
   `widget-slot-ID` w arkuszu aplikacji.
4. Obsłuż brak danych, ładowanie i błąd, gdy moduł otrzyma API.
5. Sprawdź jasny i ciemny motyw, wybrany akcent, mały ekran i klawiaturę.

ID istniejących modułów nie zmieniaj bez migracji preferencji. Kafelki należą
do `fleet`, `trips` lub `analytics`; dashboard odpowiada za ich kompozycję.
Wywołania API należy później wydzielić do wspólnego klienta, bez sekretów
WEBFLEET w przeglądarce. Przy równoległej pracy uzgodnij zmiany rejestru
i arkusza stylów z osobą pracującą w tych samych plikach.

## Preferencje i dostępność

`app/preferences.ts` przechowuje `theme`, `accent` i `visibleWidgets`
w kluczu `fleet-flow.dashboard.v1` w localStorage. Są to ustawienia
przeglądarki, bez synchronizacji pomiędzy urządzeniami. Ukrycie wszystkich
modułów jest dozwolone; użytkownik może je ponownie włączyć lub zresetować.
Zablokowany zapis działa w pamięci sesji i pokazuje odpowiedni komunikat.
Nieznane ID są odrzucane; nowy moduł jest dostępny w ustawieniach.

Motyw systemowy korzysta z
[`prefers-color-scheme`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-color-scheme)
i reaguje na jego zmianę. Właściwość
[`color-scheme`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/color-scheme)
dopasowuje natywne kontrolki do wybranego motywu.

Przyciski mają nazwy, elementy interaktywne widoczny fokus, panel używa
natywnego `dialog` z obsługą Escape i ograniczeniem fokusu. Zachowuj
`prefers-reduced-motion` i opisy tekstowe przy ikonach. Personalizacja na
tym etapie obejmuje motyw, kolory i widoczność; kolejność i rozmiar kafelków
będą osobnymi zadaniami.
