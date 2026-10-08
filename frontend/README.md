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
npm run typecheck     # sprawdzenie typów
npm run build         # typecheck oraz build do dist/
npm run preview       # podgląd zbudowanego frontendu na 127.0.0.1:4173
```

## Co już działa

- Dashboard i nawigacja po grupach: Flota, Przejazdy, Analityka.
- Sześć niezależnych kafelków ze stanami oczekiwania na dane.
- Motyw jasny, ciemny i zgodny z systemem; pięć akcentów i własny kolor.
- Włączanie i ukrywanie modułów, wyszukiwanie po nazwie modułu.
- Zapamiętywanie ustawień na urządzeniu i przywracanie domyślnych.
- Układ na telefon i komputer; panel personalizacji obsługuje Tab i Escape.
- Lokalna czcionka Inter i ikony Lucide, bez pobierania fontu z Google.

Mapa jest ilustracją. Dane WEBFLEET, logowanie, edycja przejazdów, właściwe
wykresy oraz przeciąganie i zmiana rozmiarów kafelków powstaną osobno.
Wyszukiwarka szuka nazw modułów, nie pojazdów.

## Dalsza praca

Kolory i wspólne komponenty opisuje [system wyglądu](../docs/DESIGN_SYSTEM.md).
Kafelki funkcji znajdują się w `src/features/fleet`, `trips` i `analytics`.
Uzgodnij typy i odpowiedzi API z Dawidem przed podłączaniem danych.
Nie dodawaj sekretów do zmiennych `VITE_*`: trafiają one do przeglądarki.

Po zmianie uruchom build i sprawdź odpowiedni widok w przeglądarce. Zmiany
wprowadzamy gałęzią zadania i PR zgodnie z [CONTRIBUTING](../CONTRIBUTING.md).
