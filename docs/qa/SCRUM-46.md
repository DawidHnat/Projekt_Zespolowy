# SCRUM-46 — edycja zbiorowa i wspólna paginacja

Odbiór techniczny **19.11.2026**, wykonawca: **agent Codex na polecenie
Jakuba Czai (jczaja51)**. Baza: `cb634da0ece8cd93424bfc16a5185cf817a0cbb1`.
Core #17 jest w main. #72 / `2877897` scalono tylko do gałęzi pośredniej:
sprawdzono brak jego testu, instrukcji i dopisku README w obecnym main.
Przeniesiono wyłącznie te trzy pliki przez cherry-pick z pochodzeniem;
**kod produktu bez zmian**. Zachowano autorstwo Jakuba Czai.

Test z 10.11 dostosowano do obecnych backendowych preferencji konta:
świadomy import v1, oczekiwanie na zakończony zapis API, zachowany filtr
po reload i rzeczywisty profil 390 px (bez powiększania go w teście).

## Wykonane scenariusze

Środowisko: macOS, Python 3.13, jednorazowy PostgreSQL 17 na localhost,
lokalny FastAPI oraz zbudowany frontend; Playwright Chromium desktop
1440×1000 i mobile 390×844. Dane i konta wyłącznie syntetyczne.

| Zakres | Oczekiwany i zaobserwowany rezultat | Wynik |
| --- | --- | --- |
| Zaznaczenie i filtry | Checkbox klawiaturą oraz kliknięcie treści; trwałe ID 1/11 zachowane między stronami i pod filtrem 26 | PASS, oba profile |
| Zaznaczone / obie osie / preset | Wspólna szerokość zachowuje różne wysokości 500/600; wspólna wysokość zachowuje szerokości; Duże zmienia oba wymiary, niezaznaczony 26 pozostaje bez zmian | PASS, oba profile |
| Wszystkie | Operacja przy filtrze obejmuje stronę niewidoczną i nowy pojazd 27; Anuluj cofa szkic, Zapisz zachowuje wspólny default | PASS, oba profile |
| Migracja i zdjęcie | Jawny import starego v1 zachowuje wymiary; zapis v2 jest zgodny z API konta; zdjęcie z IndexedDB nadal widoczne po reload | PASS, oba profile |
| 10/25/50/100 | Wspólny limit galerii, tabeli i listy mapy; zmiana limitu wraca na stronę 1, zakresy poprawne, pusta lista 0–0 i pojedyncza 1–1 blokują strzałki | PASS, oba profile |
| Mapa i konto | Dane GPS nie mają parametrów strony listy; inny użytkownik ma własny limit, ponowne logowanie przywraca zapis właściciela | PASS, oba profile |
| Mały ekran i oględziny | Zapisana szerokość zachowana mimo ograniczenia CSS; karta nie wychodzi poza ekran; obejrzano zrzuty dialogu mieszanych rozmiarów i paginacji | PASS, 390 px i desktop |

**Walidacja autora:** `npm test` **58/58 PASS**, `npm run build` **PASS**,
3 scenariusze × 2 profile **6/6 PASS**, bez pominięć. Znane ostrzeżenie
rozmiaru bundla Mapbox należy do SCRUM-129; nie wyciszano go.
Źródło testów: `frontend/e2e/bulk-layout.spec.ts`.

Test loguje się do rzeczywistego lokalnego API i zapisuje preferencje
w dedykowanej bazie E2E. Flota 26/27 jest kontrolowaną odpowiedzią API tylko
w przeglądarce; nie wstawiono jej do produktu. Ruch zewnętrzny jest blokowany.
Sprawdzono niepaginowane żądania mapy, **nie wykonano odbioru żywego renderera
Mapbox ani backendowej paginacji 26 zapisanych pojazdów**.

## Wspólny niezależny odbiór — bez dublowania 23/40

Review kodu testów i dokumentacji: **Jakub Nazarewicz**.
QA: **Marcel Głowacki**, wyniki tych samych scenariuszy w
[SCRUM-23](https://fleet-flow.atlassian.net/browse/SCRUM-23) i
[SCRUM-40](https://fleet-flow.atlassian.net/browse/SCRUM-40), stosownie do AC.
Osobno pozostaje kontrolowany backend i rzeczywista mapa z pełnym zbiorem GPS.
Autor testu nie podpisuje tego odbioru za QA.

W raporcie każdego wykonanego kroku zapisać wykonawcę, datę, SHA, środowisko,
dowód oraz PASS/FAIL/BLOCKED. Zmiana samej dokumentacji nie wymaga powtórki
wszystkich zaliczonych scenariuszy: porównać kod do testowanego SHA i zrobić
potrzebny smoke/retest. Zamknięcie implementacji SCRUM-46 wymaga jej własnego
zakresu, aktualnego niezależnego review i merge do main; szersza regresja
produktu zachowuje własne zadania i nie staje się nowym zakresem 46.

## Historia

10.11: #72 / `2877897`, 50 unit, 42 pełne E2E (w tym 6 tego zakresu) PASS.
To historyczna wersja i osobny wynik; liczb nie przypisano obecnemu SHA.
