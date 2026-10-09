# Rozpoczęcie pracy

Repozytorium ma na razie puste pliki źródłowe. Nie ma jeszcze polecenia,
które uruchamia aplikację. Pracę lokalną można rozpocząć niezależnie od VPS.

## Każdy członek zespołu

1. Klonuje `https://github.com/DawidHnat/Projekt_Zespolowy` na własny komputer.
2. Ustawia w tym repozytorium własne `git config user.name` oraz
   `git config user.email` zgodne z kontem GitHub. Sprawdza `git config --get
   user.name` i `git config --get user.email` przed pierwszym commitem.
3. Wybiera przypisane zadanie z [podziału pracy](TASKS.md), czyta kryteria
   akceptacji i tworzy gałąź zgodnie z [CONTRIBUTING](../CONTRIBUTING.md).
4. Dostarcza Dawidowi własny publiczny klucz SSH `.pub` według
   [instrukcji VPS](../infra/vps/README.md). Prywatnego klucza nie przekazuje.
5. Po dodaniu klucza zapisuje własny test SSH z kodem wyjścia w
   [SCRUM-12](https://fleet-flow.atlassian.net/browse/SCRUM-12).

## Pierwszy PR z uruchamianiem — SCRUM-13, Jakub Czaja

Minimalna podstawa obejmuje konfigurację React i TypeScript, FastAPI,
PostgreSQL oraz wspólne polecenia uruchomienia. Kryteria tego etapu:

- wersje Node i Python oraz zależności zapisane w repozytorium, pliki blokad
  aktualizowane razem ze zmianą zależności;
- frontend wyświetla tylko ekran startowy, backend udostępnia sprawdzalny
  stan działania, baza uruchamia się lokalnie i ma migracje;
- instrukcja uruchomienia działa po świeżym klonowaniu na drugim komputerze;
- `.env.example` zawiera wyłącznie nazwy zmiennych i bezpieczne przykłady;
  rzeczywiste dane WEBFLEET pozostają w lokalnym `.env` backendu;
- GitHub Actions sprawdza build TypeScript oraz odpowiednie kontrole backendu;
- baza nasłuchuje lokalnie; dostęp do rzeczywistych danych floty pozostaje
  po stronie backendu i wymaga uwierzytelnienia aplikacji.

Dokładne wersje narzędzi ustalamy w tym PR. Nie trzeba instalować ich globalnie
na VPS, aby spełnić kryterium logowania SSH z zadania zespołowego.

## Prace równoległe

| Osoba | Pierwsze zadanie | Wynik |
| --- | --- | --- |
| Jakub Czaja | SCRUM-13 | Minimalne uruchomienie i CI, bez implementacji trzech funkcji |
| Dawid Hnat | SCRUM-36 oraz SCRUM-14 | Kontrakt API, model danych i sprawdzenie dostępnych danych WEBFLEET |
| Jakub Nazarewicz | SCRUM-35 | Szkice trzech widoków i przepływy użytkownika |
| Marcel Głowacki | SCRUM-37 | Plan QA i przypadki syntetyczne z oczekiwanymi wynikami |

Po uzgodnieniu kontraktu API i scaleniu podstawy można rozpocząć zadania
implementacji przypisane w Jirze. Kod i dokumentacja trafiają przez gałąź
zadania i PR. Automatyczne tworzenie PR, przegląd przez płatne API AI i
automatyczne scalanie wymagają osobnego przygotowania.
