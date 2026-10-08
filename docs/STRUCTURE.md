# Struktura projektu

Frontend zawiera działający szkielet dashboardu. Moduły odpowiadają trzem
funkcjom z README. Backend oraz pliki stron `FleetPage.tsx`, `HistoryPage.tsx`
i `AnalyticsPage.tsx` pozostają celowo puste do kolejnych zadań.
`.gitkeep` pozwala zapisać pusty katalog w Git.

```text
frontend/
  package.json, package-lock.json, .nvmrc
  index.html, tsconfig.json, vite.config.ts
  src/
    main.tsx
    app/                 układ, rejestr stron, preferencje, tokeny i style
      components/        AppSettingsPanel: wygląd, tło i moduły Pulpitu
    features/
      dashboard/
        model/           identyfikatory, typy i rejestr modułów
        components/      siatka, edytor, tło i wybór obrazu
      fleet/
        components/      mapa, lista pojazdów i dedykowany FleetMapPage
        FleetPage.tsx    przyszły pełny widok floty
      trips/
        components/      kafelek ostatnich przejazdów
        HistoryPage.tsx  przyszła historia i ewidencja
      analytics/
        components/      wskaźniki, aktywność i wykorzystanie floty
        AnalyticsPage.tsx
    shared/
      api/               przyszły klient API i typy
      components/        WidgetFrame, EmptyState
backend/
  app/
    main.py
    core/config.py
    db/                  przyszłe modele i połączenie
    modules/
      fleet/router.py
      trips/router.py
      analytics/router.py
    integrations/webfleet/client.py
  migrations/            przyszłe migracje
  tests/                 przyszłe testy
contracts/               wspólny kontrakt API do uzgodnienia
docs/                    dokumentacja projektu i systemu wyglądu
infra/vps/               instrukcja VPS i publiczne klucze
.github/
  workflows/frontend.yml typecheck i build na PR oraz push do main
  PULL_REQUEST_TEMPLATE.md
```

Backend planujemy w Python i FastAPI, bazę w PostgreSQL. Dołączenie ich
konfiguracji i kodu należy do kolejnych zadań. Adapter WEBFLEET pozostaje
po stronie backendu; frontend nie otrzymuje jego sekretów.

Zasady gałęzi i przeglądu opisuje [CONTRIBUTING.md](../CONTRIBUTING.md),
a rozwijanie modułów i stylów [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).
