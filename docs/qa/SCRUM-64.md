# SCRUM-64 - kontrolowane uruchomienie synchronizacji

Przyrost audytu: Compose respektuje `SYNC_ENABLED` z prywatnego `runtime.env`.
Domyślnie pozostaje false. Worker zapisuje zanonimizowany kod zdarzenia zamiast
połykać wyjątek; nieoczekiwany błąd importu oznacza cache jako degraded i zachowuje
ostatni sukces. Nie ma logowania wyjątków SQL/HTTP, identyfikatorów źródła ani GPS.
`python -m app.sync_control status` sprawdza wiek ostatniej udanej synchronizacji
(domyślnie 180 s), a `once` wykonuje pojedynczy import z dotychczasową blokadą
PostgreSQL i wspólnym limitem 60 s. Status nie odpytuje WEBFLEET.

## Przed canary

- Niezależny review, zielone CI, aktualny backup poza VPS i próba odtworzenia.
- Wyraźna zgoda na żywy import; prywatne poświadczenia w `DEV_RUNTIME_ENV` i na
  VPS. Nie zapisuj ich w Git, historii poleceń, logach ani dowodach QA.
- `WEBFLEET_ACCOUNT` identyfikuje tę samą organizację co cache aplikacji.
- Okno pracy operatora i osoba reagująca na błąd; zatrzymaj inne diagnostyki
  korzystające z tego konta. Interwał pozostaje 60 s.

## Canary i włączenie

1. Wdróż odebraną wersję z `SYNC_ENABLED=false` (scheduler nie startuje).
2. W katalogu wydania ustaw kontekst Compose jak w `infra/deploy/deploy.sh`.
   Uruchom w kontenerze API `python -m app.sync_control once`.
   Oczekiwane: kod 0 i `status=ok`. `busy`/`rate_limited` oznacza odczekanie
   pełnego interwału i ustalenie drugiego procesu, nigdy pętlę ponowień.
3. `python -m app.sync_control status`: kod 0, świeży `last_success_at`.
   Sprawdź zalogowaną listę/mapę i zgodność pól z SCRUM-14. Nie kopiuj realnych
   rekordów ani zrzutów mapy do publicznego PR. Pusta flota jest dopuszczalna
   tylko po potwierdzeniu uprawnień i rzeczywistego braku obiektów.
4. Prywatnie ustaw `SYNC_ENABLED=true` zarówno w źródle konfiguracji Actions,
   jak i na VPS, aby kolejny deploy nie cofnął zmiany. Odtwórz kontener API.
5. Obserwuj co najmniej trzy cykle po 60 s: rosnący `last_success_at`, ten sam
   UUID pojazdów, brak dodatkowych wywołań po otwarciu kilku sesji, brak zmian
   ręcznych kierowców. Zapisz czas, SHA, PASS/FAIL/BLOCKED bez treści floty.
6. Monitor uruchamia `status` co minutę i alarmuje po niezerowym kodzie
   (unavailable/degraded/stale/failed). Centralny odbiornik alarmów jest osobnym
   zadaniem; operator musi go wskazać przed pozostawieniem integracji bez nadzoru.

## Awaria i wycofanie

Wyłącz `SYNC_ENABLED` w obu źródłach konfiguracji i odtwórz API. Nie usuwaj
cache ani tabel. Sprawdź zachowanie ostatniego wyniku i jawny czas pomiaru.
Jeżeli zmieniono konto WEBFLEET, izolacja źródła może celowo dać 503 aż do
pierwszego sukcesu nowego konta. Nie obchodź jej kopiowaniem identyfikatorów.

Testy syntetyczne: ruff, pytest; PostgreSQL sprawdza advisory lock, limit i cache.
**Żywy canary i VPS nie zostały uruchomione w ramach przygotowania kodu.**
Nie zamykaj SCRUM-64 ani nadrzędnego SCRUM-15 przed rzeczywistym odbiorem.
