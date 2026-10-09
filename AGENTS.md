# Fleet-Flow — instrukcje dla agentów

Przeczytaj README, CONTRIBUTING i opis zadania SCRUM, jeśli został podany.
Frontend ma dashboard React + TypeScript (SCRUM-38). Backend ma FastAPI,
PostgreSQL, migracje, logowanie, adapter WEBFLEET i API floty. Pozostałe puste
moduły należą do kolejnych zadań. Kierowcy są wprowadzani ręcznie.

- Puste pliki są celowe. Nie wypełniaj ich kodem, danymi demo ani konfiguracją
  uruchomienia w ramach zadania dotyczącego samej struktury.
- Kod, zależności, Docker, testy i CI dodawaj w osobnych zadaniach implementacji.
- Zachowuj moduły `fleet`, `trips`, `analytics` oraz osobny adapter WEBFLEET.
- Przed zmianą UI przeczytaj `docs/DESIGN_SYSTEM.md`. Używaj wspólnych tokenów
  i komponentów; nowe kafelki dodawaj do rejestru dashboardu.
- Po zmianie frontendu wykonaj `npm test` i `npm run build` w `frontend/` i sprawdź
  zachowanie zmienionego widoku w przeglądarce. Nie dodawaj fikcyjnych danych
  do produktu poza osobno uzgodnionym zadaniem.
- Pracuj na gałęzi zadania, np. `feat/SCRUM-123-krotki-opis`; zmiana trafia do PR
  i przeglądu, zgodnie z CONTRIBUTING.
- Nie umieszczaj sekretów, `.env`, kluczy prywatnych ani danych klientów w Git.
- Po zmianach integracji uruchom w `backend`: `ruff check .`,
  `ruff format --check .` i `pytest`. Testy używają fikcyjnych danych bez sekretów.
  Testy żywego API/SMTP wykonuj tylko na wyraźne polecenie, poza CI; nie publikuj
  danych klienta. Diagnostyka SMTP sprawdza logowanie i nie wysyła wiadomości.
- Konfigurację serwera zmieniaj tylko w zadaniach dotyczących infrastruktury.
- Nie włączaj płatnego API AI ani automatycznego scalania bez decyzji użytkownika.
