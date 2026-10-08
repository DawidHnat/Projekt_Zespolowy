# Fleet-Flow — instrukcje dla agentów

Przeczytaj README, CONTRIBUTING i opis zadania SCRUM, jeśli został podany.
Frontend zawiera lokalny szkielet dashboardu React + TypeScript (SCRUM-38).
Backend i pozostałe puste pliki funkcji nadal są strukturą do implementacji.

- Puste pliki są celowe. Nie wypełniaj ich kodem, danymi demo ani konfiguracją
  uruchomienia w ramach zadania dotyczącego samej struktury.
- Kod, zależności, Docker, testy i CI dodawaj w osobnych zadaniach implementacji.
- Zachowuj moduły `fleet`, `trips`, `analytics` oraz osobny adapter WEBFLEET.
- Przed zmianą UI przeczytaj `docs/DESIGN_SYSTEM.md`. Używaj wspólnych tokenów
  i komponentów; nowe kafelki dodawaj do rejestru dashboardu.
- Po zmianie frontendu wykonaj `npm run build` w `frontend/` i sprawdź
  zachowanie zmienionego widoku w przeglądarce. Nie dodawaj fikcyjnych danych
  do produktu poza osobno uzgodnionym zadaniem.
- Pracuj na gałęzi zadania, np. `feat/SCRUM-123-krotki-opis`; zmiana trafia do PR
  i przeglądu, zgodnie z CONTRIBUTING.
- Nie umieszczaj sekretów, `.env`, kluczy prywatnych ani danych klientów w Git.
- Konfigurację serwera zmieniaj tylko w zadaniach dotyczących infrastruktury.
- Nie włączaj płatnego API AI ani automatycznego scalania bez decyzji użytkownika.
