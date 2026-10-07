# Struktura startowa

Katalogi odpowiadają trzem funkcjom z README. Pliki źródłowe są celowo puste;
`.gitkeep` pozwala zapisać pusty katalog w Git. Nie ma jeszcze konfiguracji
uruchomienia, zależności, bazy, testów ani automatyzacji.

```text
frontend/
  index.html
  src/
    main.tsx
    app/                 App.tsx, styles.css
    features/
      fleet/             FleetPage.tsx — lista i mapa
      trips/             HistoryPage.tsx — historia i ewidencja
      analytics/         AnalyticsPage.tsx — analityka i alerty
    shared/
      api/               wspólny klient API i typy, później
      components/        wspólne komponenty, później
backend/
  app/
    main.py
    core/config.py
    db/                  modele i połączenie, później
    modules/
      fleet/router.py
      trips/router.py
      analytics/router.py
    integrations/webfleet/client.py
  migrations/            migracje, później
  tests/                 testy, później
contracts/               wspólny kontrakt API, później
docs/                    dokumentacja projektu
infra/vps/               instrukcja przygotowania VPS i publiczne klucze
.github/                 szablon PR i wskazówki do przeglądu
```

Frontend planujemy w React i TypeScript, backend w Python i FastAPI,
a bazę w PostgreSQL. Dodawanie konfiguracji i kodu należy do kolejnych zadań.
Zasady gałęzi i przeglądu opisuje [CONTRIBUTING.md](../CONTRIBUTING.md).
