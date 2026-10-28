# SCRUM-97 — zapytania floty

Lista wykonuje literalne wyszukiwanie, filtr statusu, COUNT i LIMIT/OFFSET w SQL.
Sortowanie `(name, id)` ma stabilny tie breaker. Tylko zwrócona strona przechodzi
przez serializer pojazdu. Summary wykonuje GROUP BY status, a mapa pobiera sześć
pól markerów, bez kierowcy, numerów, przebiegu i pełnych obiektów ORM. Mapa nadal
obejmuje wszystkie pasujące pozycje, niezależnie od paginacji listy. Usunięto
sztuczny błąd dla list przekraczających 10 000 pojazdów.

Granice czasu są wyznaczane raz na operację: dokładnie `stale_seconds` jest świeże,
dokładnie 300 s w przyszłość jest akceptowane. Brak pomiaru daje unknown, pomiar
bez daty offline. Nieaktualny poprawny GPS nadal trafia na mapę; brak GPS pozostaje
null, a (0,0) pozostaje prawidłową pozycją. Auth, izolacja konta, aktywność pojazdu
i source ok/degraded pozostają obsługiwane przed odpowiedzią.

Wyszukiwanie używa LOWER w PostgreSQL i dosłownego LIKE z escapowaniem `%`, `_`
i znaku escape. Test PostgreSQL potwierdza polskie litery ŁÓDŹ/łódź. Zmiana
semantyczna do jawnego review: PostgreSQL 17 LOWER nie wykonuje pełnego Unicode
casefold starego filtra Pythona (np. ß/ss). Nie dodano kosztownej normalizacji ani
zmiany bazy do wersji 18 w zadaniu wydajnościowym. Kontrakt formatu odpowiedzi
pozostaje taki sam. Źródło zachowania LOWER/casefold:
https://www.postgresql.org/docs/18/functions-string.html.

## Powtarzalny pomiar

W backend, po migracji **osobnej** lokalnej bazy `fleet_flow_test*`:

```sh
TEST_DATABASE_URL=postgresql+psycopg://.../fleet_flow_test_perf \
  python -m tools.benchmark_fleet_queries > benchmark.json
```

Skrypt odrzuca inne nazwy/hosty, wstawia wyłącznie syntetyczne rekordy i wycofuje
transakcję po każdej skali. Nie uruchamia migracji, czyszczenia ani integracji.
Wynik z 28.10.2026: lokalny PostgreSQL 17-alpine, Python 3.12, ciepły cache,
mediana 5 powtórzeń listy (25) + pełnej mapy + summary, bez HTTP/transportu.
Porównanie odtwarza poprzednie trzy pełne SELECT i serializacje. To pomiar
lokalny, nie deklaracja SLA ani pełny benchmark obciążeniowy SCRUM-104.

| Pojazdy | Poprzednio ORM | Teraz ORM | Markery | Wiersze agregatów | Poprzednio ms | Teraz ms |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 300 | 25 | 100 | 3 | 4.62 | 3.05 |
| 1 000 | 3 000 | 25 | 1 000 | 3 | 40.22 | 7.98 |
| 10 000 | 30 000 | 25 | 10 000 | 3 | 489.25 | 68.05 |

Pełne EXPLAIN (ANALYZE, BUFFERS) pięciu zapytań dla każdej skali są w
[SCRUM-97-plans.json](SCRUM-97-plans.json). Istniejące indeksy: source_account,
unikalny (source_account, external_uid), PK measurements.vehicle_id oraz PK
powiązań. Dla jednego konta obejmującego prawie całą syntetyczną bazę planner
wybiera także skany sekwencyjne i hash join; jest to oczekiwane. Top-N sort listy
zwraca tylko 25 rekordów, ale musi przejrzeć dopasowaną flotę. Brak uzasadnienia
dla Redis ani nowego indeksu w tym pomiarze. Duże OFFSET i pełna mapa nadal mają
koszt zależny od liczby pojazdów; dalsze wymagania SLA należą do SCRUM-104.

Weryfikacja developerska: 108 pytest PASS (w tym PostgreSQL i pełny round trip
migracji), ruff check i format --check PASS. Testy obejmują m.in. 10 001 pojazdów,
stabilne strony, faktyczną liczbę ładowanych obiektów, statusy, filtry literalne,
(0,0), brak pomiaru, future/stale i degraded. Wymagane niezależne review, decyzja
w sprawie różnicy Unicode oraz QA na SHA PR; sam pomiar nie zamyka zadania.
