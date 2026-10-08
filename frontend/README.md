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
`npm run dev -- --port 5174`. Nie są potrzebne `.env`, konta ani VPS.

```bash
npm test              # migracja, zapis i ograniczenia układu
npm run typecheck     # sprawdzenie typów
npm run build         # typecheck oraz build do dist/
npm run preview       # podgląd zbudowanego frontendu na 127.0.0.1:4173
```

## Co już działa

- Pulpit oraz sekcje: Mapa, Serwis, Ewidencja przebiegu, Kierowcy,
  Karty paliwowe i Alerty.
- Osobny widok Mapy z listą pojazdów obok (pod mapą na małym ekranie).
  Nowe sekcje poza Mapą są pustymi widokami planowanych funkcji.
- Sześć niezależnych kafelków ze stanami oczekiwania na dane.
- Motyw jasny, ciemny i zgodny z systemem; pięć akcentów i własny kolor.
- Włączanie i ukrywanie modułów, wyszukiwanie po nazwie modułu.
- Edytor Pulpitu i Mapy: chwytanie całego kafelka, podgląd miejsca upuszczenia,
  płynne przesuwanie sąsiednich kart, rozciąganie i ustawienia rozmiaru.
- Niezależne Zapisz/Anuluj oraz układy telefonu i komputera dla obu widoków.
- Opcjonalne szkło z połyskiem na kartach, przyciskach i nawigacji oraz styl klasyczny.
- Tło domyślne, galeria i własny obraz, z wyciszeniem i rozmyciem w obu stylach.
- Zapamiętywanie ustawień na urządzeniu i przywracanie domyślnych.
- Ustawienia aplikacji pod kołem zębatym, dostępne w każdej sekcji;
  panel obsługuje Tab i Escape.
- Lokalna czcionka Inter i ikony Lucide, bez pobierania fontu z Google.

Mapa jest ilustracją. Dane WEBFLEET, logowanie, edycja przejazdów, właściwe
wykresy powstaną osobno.
Wyszukiwarka szuka nazw modułów, nie pojazdów.

## Edycja Pulpitu i Mapy

Na Pulpicie lub Mapie kliknij „Edytuj układ”. Chwyć dowolną część kafelka
poza przyciskami i polami formularzy. Podświetlony obrys pokazuje docelowe
miejsce, a sąsiednie kafelki robią przestrzeń. Prawy dolny narożnik zmienia
rozmiar. Ikona ustawień otwiera suwaki i presety, a na Pulpicie także ukrywanie.
Uchwyt z kropkami obsługuje strzałki oraz Shift + strzałki;
Enter otwiera ustawienia. „Zapisz układ” zatwierdza, „Anuluj” odrzuca szkic.

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

W „Ustawieniach” → „Tło przestrzeni” wybierz „Galeria” albo „Własne”. Galeria zawiera miasto,
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
