# Fleet-Flow — instrukcje dla agentów

Przeczytaj README, CONTRIBUTING i opis zadania SCRUM, jeśli został podany.
Backend ma adapter WEBFLEET i diagnostykę SMTP (SCRUM-14). Pozostałe puste pliki
modułów są strukturą do osobnych zadań. Adapter nie uruchamia serwera API.

- Puste pliki są celowe. Nie wypełniaj ich kodem, danymi demo ani konfiguracją
  uruchomienia w ramach zadania dotyczącego samej struktury.
- Kod, zależności, Docker, testy i CI dodawaj w osobnych zadaniach implementacji.
- Zachowuj moduły `fleet`, `trips`, `analytics` oraz osobny adapter WEBFLEET.
- Pracuj na gałęzi zadania, np. `feat/SCRUM-123-krotki-opis`; zmiana trafia do PR
  i przeglądu, zgodnie z CONTRIBUTING.
- Nie umieszczaj sekretów, `.env`, kluczy prywatnych ani danych klientów w Git.
- Po zmianach integracji uruchom w `backend`: `ruff check .`,
  `ruff format --check .` i `pytest`. Testy używają fikcyjnych danych bez sekretów.
  Testy żywego API/SMTP wykonuj tylko na wyraźne polecenie, poza CI; nie publikuj
  danych klienta. Diagnostyka SMTP sprawdza logowanie i nie wysyła wiadomości.
- Konfigurację serwera zmieniaj tylko w zadaniach dotyczących infrastruktury.
- Nie włączaj płatnego API AI ani automatycznego scalania bez decyzji użytkownika.
