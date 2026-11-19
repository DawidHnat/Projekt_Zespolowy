# SCRUM-94 — przegląd prywatności i pakiet decyzji

Wersja 3, **19.11.2026**; uzupełnienie odpowiedziami PO z pól 1–6. Wykonawca: **agent Codex na polecenie Jakuba Czai**.
Kod `cb634da0ece8cd93424bfc16a5185cf817a0cbb1`; środowisko: izolowany checkout,
statyczne porównanie wszystkich modeli/pól; bez rekordów klientów i zmian VPS.
**PASS części technicznej; BLOCKED pełnego odbioru 94/113** do decyzji
właściwego administratora i wymaganego screeningu.

[Krótki arkusz zatwierdzeń](SCRUM-113-decision-sheet.md) jest jednym miejscem
z następnymi decyzjami. Źródłem pozostaje [istniejący JSON](inventory.v1.json)
(wersja treści 3, historyczna nazwa pliku), 22 kategorie D01–D22, 11 przepływów,
6 grup dostawców i **18 decyzji P01–P18: 0 kompletnych APPROVED**. Częściowe
ustalenia P01/02/03/04/06/07/10/15 są w `reported_fact`; nie wpisano cudzych
podpisów i nie utworzono konkurencyjnego inwentarza.

PO doprecyzował 19.11: projekt używa **rzeczywistych danych jednej firmy i jednego
API WEBFLEET** za ustną zgodą właściciela, wyłącznie projektowo, z dostępem
czwórki i pokazem prowadzącemu. Podmiot i właściciel wskazani lokalnie poza
Git/Jira. Użyczenie do końca lutego 2027 r., potem koniec projektu i plan
usunięcia jego danych. **Nie było konsultacji DPO/prawnej.** To koryguje
wcześniejsze założenie syntetycznego demo; testy pozostają syntetyczne.
[ADR](../adr/SCRUM-94-data-isolation.md) i arkusz rozróżniają potwierdzone
ustalenia od nieprzekazanych procedur i wyniku screeningu; nie jest to audyt VPS.

## Rzeczywiste różnice po integracjach

Spis SCRUM-112 / PR #52 jest już na main (merge `4be4c5f`); dokumenty #58/#74
są również scalone. Ich dawne oczekiwanie na merge nie jest bieżącą blokadą.
Historia snapshotów z 29.10 jest zachowana; bieżące `schema_snapshots.main`
odnosi się do podanego wyżej SHA. Porównano **15 tabel**, bez usuniętych pól:

| Kategoria | Obecny kod względem pierwotnego spisu |
| --- | --- |
| D06 — kartoteka auta | Marka/model/rok/VIN, `locally_edited` i pochodne SQL `search_*` są w main. Ręczna edycja i źródło mają odrębne reguły; nowe pola nie zatwierdzają celu użycia. |
| D07 — pomiar | `speed_kmh` i `position_address` są zapisywane oraz udostępniane przez API. Dawny opis zawsze pustej prędkości nie jest aktualny. |
| D11/D12 — przejazdy/adnotacje | `trips` i `trip_annotations` są w main. Jest autor/data ostatniej zmiany, bez pełnej historii audytu; importer historii jest osobnym zakresem. |
| D17 — preferencje | Nowa tabela `account_preferences(user_id,module,value,version,updated_at)`: dashboard/vehicles, układ, filtry, sort i limit. Zawartość trafia do dumpu DB. Wygląd/obrazy nadal mają lokalne magazyny. |
| D08–D10/D15 — zależności | Rozszerzenia kierowców, `driver_categories`, `driver_assignments` i UI alertów są dopiero w otwartym #110 (`be609d7`), 17 tabel. #109/#111 Merged do zależności nie oznaczają dostarczenia do main. |
| D19/D20 — operacje | Bezpieczne zdarzenia synchronizacji są w main przez #107. Off-site #35/#105 i pełny recovery: **DEFERRED → SCRUM-84/S5**; obecne kopie/rollback SCRUM-18 pozostają odrębnym zakresem. |

## Kryteria SCRUM-94 i wynik

| AC | Dowód / wykonawca / data | Status |
| --- | --- | --- |
| Cele, kategorie, przepływy, pola i podmioty | Agent 19.11: istniejący spis zaktualizowany, `technical_refresh` w JSON; właściciel i cel przekazani przez PO, pozostałe role dostawców/minimalne pola wymagają P01/P02 | PASS techniczny, BLOCKED decyzje |
| Zatwierdzona retencja/dostęp/prywatność/procedury | Częściowe ustalenia odbiorców, końca użyczenia i usunięcia zapisane; pozostałe procedury/wyjątki otwarte | BLOCKED — Jakub koordynuje pozostałe decyzje właściciela |
| Udokumentowany screening DPIA | PO potwierdził brak konsultacji; materiał wejściowy poniżej, brak wyniku i konsultującego | BLOCKED — Jakub Czaja wskazuje właściwego DPO/prawnika, administrator odbiera wynik |
| ADR organizacji i informowanie | PO 19.11 potwierdza jedną firmę/źródło i wskazał właściciela lokalnie; pozostałe P01/P07 i informowanie P09 otwarte | PASS zakres produktu, BLOCKED akceptacja danych |

## Materiał techniczny do screeningu DPIA

DPIA to ocena skutków przetwarzania dla ochrony danych: służy ocenie ryzyka
dla osób i potrzebnych zabezpieczeń przy określonym sposobie użycia.
Wymóg udokumentowanego screeningu jest zapisany w kryterium 3 SCRUM-94.
Arkusz poniżej przygotowuje wejście do oceny rzeczywistej floty zgłoszonej
przez PO. Tożsamość właściciela zapisano lokalnie; pozostałego kontekstu
i wyniku konsultacji nie uzupełnia agent z domysłu.

[UODO — kiedy przeprowadzić ocenę skutków](https://uodo.gov.pl/pl/598/3617)
opisuje ocenę przed przetwarzaniem, kryteria ryzyka i znaczenie kontekstu.
Wykaz obejmuje m.in. lokalizację oraz zależność osoby od podmiotu oceniającego.
To powód do sprawdzenia zastosowania kryteriów, a nie gotowy wynik tej oceny.
[EROD 01/2020, wersja 2.0](https://www.edpb.europa.eu/system/files/documents/2021-03/edpb_guidelines_202001_connected_vehicles_v2.0_adopted_en.pdf)
jest dodatkowym materiałem o danych pojazdów i aplikacji mobilności; nie
zastępuje oceny konkretnego kontekstu pracowniczego i właściwych przepisów.

Poniższe ustalenia są analizą kodu, nie oświadczeniem firmy o sposobie użycia.
Nieznana skala lub brak funkcji w tym wydaniu nie oznaczają automatycznie NIE.

| Obszar do oceny | Fakty techniczne / niewiadome do rozstrzygnięcia |
| --- | --- |
| Obserwacja i lokalizacja | Kod przewiduje wspólne pobieranie ostatnich pozycji, czasy pomiarów i dane mapy. Trzeba ustalić cel, harmonogram i rzeczywiste monitorowanie. |
| Ocena zachowania / automatyczne decyzje | Są agregaty dystansu i alerty. Kod nie dowodzi wykorzystywania ich do oceny pracy ani decyzji wobec osób; to pytanie do administratora. |
| Dane o charakterze osobistym | Pozycja i czas mogą łączyć się z osobą przez przydział auta. Należy ocenić możliwość ujawnienia życia prywatnego oraz dane w wolnym tekście i obrazach. |
| Skala | Liczba kierowców/aut, częstotliwość, czas, obszar i okres przechowywania są niepotwierdzone. Brak danych uniemożliwia wniosek o małej skali. |
| Łączenie zbiorów | WEBFLEET, lokalny kierowca, przejazdy, adnotacje i alerty mają relacje. Związek konkretnego przejazdu z osobą może być niejednoznaczny; Trip nie ma snapshotu kierowcy. |
| Zależność osób | Niepotwierdzone: pracownicy, zleceniobiorcy, najemcy, pasażerowie i możliwość odmowy/wyłączenia. Nie utożsamiać dostępu do konta źródła ze zgodą tych osób. |
| Nowość i ingerencja | Ustalić faktyczny sposób wdrożenia, łączenia danych i wpływ na osoby; sam stos React/FastAPI nie rozstrzyga kryterium. |
| Wykonywanie praw | Brak odebranych procedur 110/111, niejednoznaczne przypisania i kopie wymagają ustalenia sposobu identyfikacji zakresu oraz realizacji żądań. |

Oceniający zapisuje: administrator i konsultujący, cel i kontekst, zakres
osób/pól/czasu, źródła, ocenę każdego właściwego kryterium, uzasadnienie
TAK/NIE/NIEUSTALONE, wymaganie pełnej DPIA lub dalszych wyjaśnień, właścicieli,
terminy oraz datę/wersję zatwierdzenia. Sam pusty podpis lub brak odpowiedzi
nie jest wynikiem screeningu. Status P10: **BLOCKED**.

## Konkretne ryzyka i dane wejściowe do decyzji

| Ustalenie w kodzie | Potrzebna decyzja i dowód wykonania |
| --- | --- |
| Wszystkie poprawnie zalogowane role mogą czytać flotę/GPS: [fleet router](../../backend/app/modules/fleet/router.py), [current_user](../../backend/app/modules/auth/service.py). User nie ma tenant_id. | P03/P07: zatwierdzona macierz biznesowa, w tym dostęp administratora IT; potem egzekwowanie i negatywne testy w SCRUM-48. |
| Ostatni pomiar jest nadpisywany, lecz alerty/dzienny dystans i kopie zachowują inne fakty: [modele](../../backend/app/core/models.py), [analityka](../../backend/app/modules/analytics/models.py). | P04/P06: osobna retencja każdej kategorii i kopii, bez utożsamiania nadpisania pomiaru z usunięciem wszystkich śladów. |
| 93 dni to limit pojedynczego zapytania przejazdów. Sesja/reset mają ważność; sprzątanie sesji/prób uruchamia udane logowanie. | Nie przedstawiać limitu odczytu ani ważności tokenu jako zatwierdzonej retencji i kompletnego joba czyszczenia. |
| Zdjęcia pozostają w IndexedDB, nazwa pliku do 120 znaków; logout odwołuje ObjectURL, nie wymazuje magazynu. | P15: zasady współdzielonego urządzenia i usuwania kopii lokalnych. Dane poglądowe bez osób/nazw klientów do testów, brak deklaracji pełnej anonimizacji zdjęć. |
| Mapbox SDK pobiera styl i dopasowuje kamerę do floty: [VehicleMap](../../frontend/src/features/fleet/components/VehicleMap.tsx). | P12: operator sprawdza żądania wyłącznie na syntetycznym scenariuszu, dane/telemetrię, kontrakt, odbiorców i transfery. Lokalne markery HTML nie są dowodem braku przetwarzania przez SDK. |
| Deploy tworzy lokalny pg_dump i testuje jego odtworzenie: [deploy.sh](../../infra/deploy/deploy.sh). | P06/P13: okres kopii, dostęp, niezależny storage, postępowanie po restore i ponownym imporcie; lokalny dump nie jest odebranym off-site recovery. |
| Narzędzia CI mają wybrane artefakty z retention-days: 7. | P14/P18: odrębnie objąć logi proxy/API, runner, artefakty, GitHub/Atlassian i urządzenia; 7 dni artefaktu nie jest globalną retencją. |

## Zatwierdzenie i odbiór

[Arkusz SCRUM-113](SCRUM-113-decision-sheet.md) grupuje wszystkie P01–P18,
konkretną decyzję, następny krok i odpowiedzialnych. Przed pełnym Done 94
nadal wymagane są rzeczywiste zatwierdzenia 113 i screening z AC.
Nie zmieniono tych kryteriów, nie wpisano fikcyjnej firmy, okresów ani podpisów.

Dawid Hnat wykonuje niezależny review techniczny aktualizacji 15 tabel i pól;
Marcel Głowacki może odebrać spójność materiału. Zielone CI i merge dokumentów
potwierdzają ich dostarczenie, lecz nie zastępują decyzji właściciela danych.
SCRUM-112 jest Gotowe; jego przyjęty spis zachowano i uaktualniono rzeczywiste różnice.
Retencja SCRUM-109, DSAR SCRUM-110 i usuwanie SCRUM-111 nie zostały uruchomione.
