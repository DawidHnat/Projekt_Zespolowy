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

Wyszukiwanie zachowuje pełny Unicode casefold starego filtra Pythona, także
Straße/STRASSE, ligatury, grecką sigmę, tureckie İ, Cherokee i polskie litery.
Prywatne pochodne search_name/search_number/search_license_plate są aktualizowane
wraz z pojazdem; SQL filtruje te kolumny literalnym LIKE z escapowaniem `%`, `_`
i znaku escape. Nie ma odczytu całej floty ani filtrowania w Pythonie. Parametr
z NUL zwraca pusty wynik (tekst PostgreSQL nie może zawierać NUL), bez błędu bazy.
Wcześniejsza różnica LOWER/casefold z wersji draft została usunięta.

Migracja0006_fleet_search przelicza istniejące rekordy w partiach500 po UUID.
Nie zmienia UUID, nazw, identyfikatorów źródła ani ręcznych driver_id; downgrade
usuwa wyłącznie odtwarzalne pochodne. Test PostgreSQL potwierdza backfill Unicode
oraz round trip bez zmiany własności danych. Normalne zapisy ORM (w tym sync)
przeliczają pola, a bulk insert ma jawne domyślne wartości pochodne. Nowy kod
zapisujący bezpośrednie UPDATE SQL musi utrzymywać te same pochodne.

Rollout wymaga zwykłego odebranego okna migracji: zatrzymaj API/worker, wykonaj
migrację nowym kodem, uruchom tę samą wersję i odbierz filtry. Nie mieszaj starego
writera z nowymi pochodnymi. Przy rollbacku do poprzedniej wersji w tym samym
oknie cofnij wyłącznie tę migrację do0005, następnie uruchom stary kod; ponowny
upgrade odtworzy pochodne z aktualnych faktów. Nie usuwa się pojazdów/adnotacji.
Po zmianie wersji Unicode Pythona należy ponownie ocenić/backfillować pochodne.
VPS i żadne rzeczywiste dane nie były zmieniane w ramach tej weryfikacji.

Baza PR została ujednolicona z SCRUM-108 / PR45; kolejne przyrosty zawierają
wymagane security, contract i E2E gates. Należy scalać po niezależnym review
w kolejności zależności i przestawić na main po odbiorze poprzednika.

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
Porównanie odtwarza poprzednie trzy pełne SELECT i serializacje; baseline wybiera
oryginalne kolumny bez nowych pochodnych, aby nie zawyżać kosztu starej wersji. To pomiar
lokalny, nie deklaracja SLA ani pełny benchmark obciążeniowy SCRUM-104.

| Pojazdy | Pełne rekordy poprzednio | Pełne rekordy teraz | Markery | Wiersze agregatów | Poprzednio ms | Teraz ms |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 300 | 25 | 100 | 3 | 4.58 | 3.24 |
| 1 000 | 3 000 | 25 | 1 000 | 3 | 43.22 | 7.70 |
| 10 000 | 30 000 | 25 | 10 000 | 3 | 552.57 | 67.06 |

Pełne EXPLAIN (ANALYZE, BUFFERS) pięciu zapytań dla każdej skali są w
[SCRUM-97-plans.json](SCRUM-97-plans.json). Istniejące indeksy: source_account,
unikalny (source_account, external_uid), PK measurements.vehicle_id oraz PK
powiązań. Dla jednego konta obejmującego prawie całą syntetyczną bazę planner
wybiera także skany sekwencyjne i hash join; jest to oczekiwane. Top-N sort listy
zwraca tylko 25 rekordów, ale musi przejrzeć dopasowaną flotę. Brak uzasadnienia
dla Redis ani nowego indeksu w tym pomiarze. Duże OFFSET i pełna mapa nadal mają
koszt zależny od liczby pojazdów; dalsze wymagania SLA należą do SCRUM-104.

Weryfikacja developerska:150 pytest PASS (w tym PostgreSQL i pełny round trip
migracji), ruff check i format --check PASS. Testy obejmują m.in. 10 001 pojazdów,
stabilne strony, faktyczną liczbę ładowanych obiektów, statusy, filtry literalne,
(0,0), brak pomiaru, future/stale i degraded. Wymagane niezależne review oraz QA na SHA PR; sam pomiar nie zamyka zadania.
Pełne E2E po migracji i zmianie zapytań:32/32 PASS desktop/mobile, w tym kontrakty,
polling, szkic i axe. Format odpowiedzi pozostaje zgodny z generowanymi DTO.
