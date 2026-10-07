# Frontend Fleet-Flow

React + TypeScript + Vite. Trzy obszary odpowiadają funkcjom z głównego README:

- `src/features/fleet/` — lista, filtrowanie, szczegóły i mapa;
- `src/features/trips/` — historia przejazdów, cel i opis;
- `src/features/analytics/` — zestawienia i alerty;
- `src/app/` — routing, dostawcy kontekstu i wspólne style;
- `src/shared/api/` — klient HTTP, zapytania i typy wygenerowane z OpenAPI;
- `src/shared/components/` — elementy współdzielone przez widoki;
- `src/shared/lib/` — małe funkcje niezależne od obszaru produktu;
- `src/test/` — testy rzeczywistych przepływów użytkownika z kontrolowanymi odpowiedziami HTTP.

## Uruchomienie

Wymagany Node.js 22 (co najmniej 22.12). Uruchom backend zgodnie z instrukcją
w głównym README, a następnie:

```bash
cd frontend
npm ci
npm run dev
```

Adres: http://127.0.0.1:5173. Vite przekazuje `/api` i `/health` do backendu.
`API_PROXY_TARGET` jest ustawieniem serwera Vite, domyślnie `http://127.0.0.1:8000`.
Praca przez kontenery jest opisana w głównym README.

Konfigurację ustaw w `.env` w **głównym katalogu projektu**, zgodnie z głównym
README. Vite odczytuje tam `VITE_MAPBOX_TOKEN` i `API_PROXY_TARGET`; nie korzysta
z osobnego `frontend/.env`. Przeglądarka otrzymuje wyłącznie zmienne `VITE_*`.

Frontend korzysta z odpowiedzi backendu. Tryb demonstracyjny jest oznaczony
w interfejsie; nie jest lokalnym zestawem fikcyjnych „danych na żywo”. Zapisywanie
celu i opisu przejazdu wysyła `PATCH` do backendu i odświeża historię.

## Mapa i sekrety

Mapa działa po ustawieniu **publicznego** `VITE_MAPBOX_TOKEN` w głównym `.env`
lub środowisku budowania. Token jest widoczny w przeglądarce: użyj uprawnień
do odczytu map i ogranicz dozwolone adresy URL w panelu Mapbox. Bez tokenu
lista działa normalnie, a obszar mapy pokazuje jej niedostępność. Nie wpisuj
kluczy WEBFLEET ani haseł do zmiennych z prefiksem `VITE_`.

Mapbox ładowany jest dopiero wtedy, gdy mapa jest skonfigurowana. Każdy obszar
ma oddzielny moduł ładowany przy wejściu na jego stronę. Dane HTTP mają wspólną
pamięć podręczną TanStack Query; wyszukiwanie listy opóźnia zapytanie o 250 ms.

## Kontrola jakości i kontrakt

```bash
npm run api:generate
npm run typecheck
npm run lint
npm run format:check
npm test
npm run build
```

`api:generate` czyta `../contracts/openapi.json`. Nie zmieniaj ręcznie
`src/shared/api/generated.ts`; zmień model backendu, wyeksportuj OpenAPI,
a następnie wygeneruj typy. Własne aliasy umieszczaj w `types.ts`.

`npm run format` stosuje wspólny styl zapisu. Przed wysłaniem zmian uruchom
formatowanie i sprawdzenie jakości dla zmienionego obszaru.

`npm run preview` służy do sprawdzenia plików wynikowych, nie jest serwerem
produkcyjnym. W docelowym wdrożeniu reverse proxy musi obsługiwać `/api`
i przekierowywać ścieżki React Router do `index.html`.
