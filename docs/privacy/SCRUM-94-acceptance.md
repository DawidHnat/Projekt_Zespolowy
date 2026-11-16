# SCRUM-94 — przegląd prywatności i pakiet decyzji

Wersja 1, 10.11.2026. Przygotowanie techniczne: Jakub Czaja z pomocą Codex.
[SCRUM-94](https://fleet-flow.atlassian.net/browse/SCRUM-94),
[inwentarz SCRUM-112](https://fleet-flow.atlassian.net/browse/SCRUM-112),
[zatwierdzenia SCRUM-113](https://fleet-flow.atlassian.net/browse/SCRUM-113).

**Stan: pakiet projektowy przygotowany do przeglądu technicznego.** PO potwierdził
10.11.2026: obecny projekt nie korzysta z rzeczywistych danych floty, a docelowy
produkt ma obsługiwać jedną firmę. Jest to deklaracja zakresu PO, nie wynik
audytu serwera lub źródła. Jedna organizacja jest ustaleniem produktowym;
nie potwierdza tożsamości przyszłego administratora ani jego polityki.

Dla obecnego zakresu syntetycznego nie tworzymy fikcyjnego screeningu firmy.
Zatwierdzenie polityki i wynik screeningu konkretnego użycia rzeczywistych
danych pozostają **BLOCKED przed takim wdrożeniem**. Dokument nie ustala
podstawy prawnej, okresów przechowywania ani administratora. Nie jest oceną
wykonaną przez DPO/prawnika i nie dopuszcza rzeczywistych danych do przetwarzania.

## Źródła i wynik przeglądu

Spis kategorii pozostaje w istniejącym
[PR #52](https://github.com/DawidHnat/Projekt_Zespolowy/pull/52):
[wersja 3ac3d3f](https://github.com/DawidHnat/Projekt_Zespolowy/blob/3ac3d3fd660ea7b306b1b18401db4361fcd0f416/docs/privacy/SCRUM-112-inventory.md)
i [rejestr JSON](https://github.com/DawidHnat/Projekt_Zespolowy/blob/3ac3d3fd660ea7b306b1b18401db4361fcd0f416/docs/privacy/inventory.v1.json).
Obejmuje 22 kategorie D01–D22, 11 przepływów F01–F11, 6 grup dostawców
i 18 decyzji P01–P18. Nie tworzymy drugiego konkurencyjnego inwentarza.
W odczytanym rejestrze wszystkie 18 decyzji polityki ma BLOCKED, bez osoby
zatwierdzającej i daty. Decyzje produktowe nie są zatwierdzeniem polityki GPS.
Dzisiejsze potwierdzenie jednej firmy jest nowym ustaleniem produktowym PO;
nie zmienia historycznych pól zatwierdzeń administratora w JSON.
PR #52 pozostaje otwarty i jest za `main` (BEHIND). Marcel zatwierdził
head 3ac3d3f 06.11; review techniczne Dawida jest nadal zamówione.
Nie opisujemy historycznego braku reviews jako aktualnego stanu tego PR-a.

Przegląd kodu dotyczy dokładnego `main`
[`5b5fcebebb8bcf980a555ccdd4a4b66425c35ed5`](https://github.com/DawidHnat/Projekt_Zespolowy/tree/5b5fcebebb8bcf980a555ccdd4a4b66425c35ed5),
a nie rzeczywistych rekordów ani konfiguracji dostawców. Stary spis wskazuje
`main` 4ce144e oraz odrębny stos przyrostów. Wymagana korekta interpretacji:

| Kategoria / stan | Wynik 10.11 i dowód |
| --- | --- |
| D11 — fakty przejazdów | `trips` jest już w main: id, vehicle_id, external_uid, start_at, end_at, distance_km. [Model](../../backend/app/modules/trips/models.py), [migracja 0005](../../backend/migrations/versions/0005_trip_annotations.py). Importer WEBFLEET historii nie wynika z obecności tabeli. |
| D12 — adnotacje i autor | `trip_annotations` jest już w main: trip_id, purpose, description, version, updated_by, updated_at. Są to ostatnia edycja i jej autor, nie pełna historia zmian. [API](../../backend/app/modules/trips/router.py). |
| Pozostałe tabele poprzedniego main | Wszystkie pola 12 tabel opisanych w `schema_snapshots.main` są zgodne z obecnym ORM. Razem obecny main ma 14 tabel. |
| Rozszerzeni kierowcy i przypisania | `driver_categories` i `driver_assignments` ze starego `review_stack` nie są tabelami obecnego main. Obecny Driver ma id/display_name/active, a Vehicle.driver_id jest pojedynczą lokalną relacją. Nie przypisujemy docelowej relacji wiele:wiele do tego wydania. |
| Funkcje planowane | Retencja SCRUM-109, eksport osoby SCRUM-110 i usuwanie SCRUM-111 nie stają się działającymi procedurami przez przyjęcie dokumentacji. |

Przeprowadzono statyczne porównanie pól wszystkich 14 modeli ORM z JSON:
12 wcześniejszych tabel bez zmian, dwie tabele przejazdów zgodne z opisem
starego review_stack, obecnie już w main. Nie importowano aplikacji, nie
łączono się z bazą i nie odczytywano danych klientów.

## Mapowanie kryteriów odbioru SCRUM-94

| Kryterium | Dostępny rezultat | Pozostaje do odbioru |
| --- | --- | --- |
| Cele, kategorie, przepływy i minimalne pola | Techniczny spis #52 i powyższa korekta wersji | Review aktualnego spisu przez Dawida; administrator/procesorzy, umowy i uzasadnienie minimalnych pól przez właściwy podmiot |
| Retencja, dostęp, użycie prywatne, DSAR/usunięcie/incydent/backup | Istnieją decyzje P01–P18 i poniższy arkusz przekazania | Faktyczne zatwierdzenia SCRUM-113; wszystkie okresy i wyjątki mają nadal BLOCKED |
| Screening DPIA | Poniższy materiał techniczny i źródła dla oceniającego | Wskazana właściwa osoba, kontekst firmy, podpisany wynik i dalsze kroki |
| Granica organizacji, informowanie i wersje | [ADR](../adr/SCRUM-94-data-isolation.md) scalony w #58; 10.11 PO potwierdził docelowo jedną firmę | Akceptacja przyszłego administratora P01/P07 oraz informacja dla osób P09 przed rzeczywistym użyciem; ustalenie produktu nie jest zatwierdzoną polityką firmy |

## Materiał techniczny do screeningu DPIA

DPIA to ocena skutków przetwarzania dla ochrony danych: służy ocenie ryzyka
dla osób i potrzebnych zabezpieczeń przy określonym sposobie użycia.
Wymóg udokumentowanego screeningu jest zapisany w kryterium 3 SCRUM-94.
Arkusz poniżej przygotowuje wejście do przyszłej oceny rzeczywistej floty;
nie wymaga wymyślania danych firmy na potrzeby demonstracji syntetycznej.

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

## Arkusz przekazania do SCRUM-113

Koordynator wszystkich otwartych ustaleń: **Jakub Czaja**. Osoba będąca
administratorem, DPO/prawnikiem i terminy decyzji pozostają **niewskazane**
w dostępnych dowodach. Właściciele techniczni poniżej nie zastępują akceptacji
właściwego administratora. Wszystkie pozycje mają obecnie status BLOCKED.

| Decyzje | Co trzeba dostarczyć do zatwierdzenia | Właściciel następnego kroku |
| --- | --- | --- |
| P01/P02 | Podmiot i rola administratora/procesorów, osoby uprawnione, cele i minimalne pola per D01–D22, podstawa potwierdzona przez właściwą osobę | PO uzyskuje dane od właściciela floty; właściwy administrator zatwierdza |
| P03/P07/P08 | Jedna organizacja jest ustaleniem PO z 10.11. Pozostają tożsamość firmy, kto widzi GPS, godziny/użycie prywatne i zachowanie przed/po wyłączeniu. Wiele organizacji wymaga osobnej zmiany zakresu i projektu izolacji. | PO i administrator; Dawid weryfikuje wykonalność |
| P04 | Dla każdej kategorii: początek liczenia, okres, zdarzenie końca, wyjątek/hold, działanie końcowe, aktywna baza/pliki/logi/przeglądarka/kopie | Administrator zatwierdza; Dawid mapuje na SCRUM-109 |
| P05/P17 | Weryfikacja osoby i autoryzacji, wiarygodne relacje kierowca–auto–czas, wyłączenie cudzych danych, manifest braków, wydanie i wygaśnięcie eksportu | Administrator i PO; backend/QA w SCRUM-110 |
| P06/P13 | Zakres usunięcia/anonimizacji, wyjątki, audyt bez danych treści, ponowny import, tombstone/ponowne zastosowanie po restore, termin wygaśnięcia kopii i recovery | Administrator zatwierdza; Dawid przygotowuje SCRUM-84/111 |
| P09/P15/P16 | Wersjonowana informacja dla osób: podmiot/kontakt, cele/podstawy, odbiorcy/transfery, retencja, prawa i skarga; lokalne urządzenia, obrazy, wolny tekst i przyszłe dokumenty/audyt | Administrator i PO; konsultacja prawna |
| P10 | Uzupełniony i zatwierdzony screening według powyższych pytań, dalsze działania i warunki ponownej oceny | PO wskazuje właściwego konsultującego; administrator odbiera |
| P11 | Uprawniony kontakt, kanał eskalacji i zastępstwo, triage, zabezpieczenie dowodów, ocena obowiązków i terminów, komunikacja oraz rejestr zdarzeń | Administrator i operator; PO koordynuje |
| P12/P14/P18 | Faktyczny ruch i umowy WEBFLEET/Mapbox/OVH/hostingu/storage/GitHub/Atlassian, dostęp i lokalizacja, powierzenie/transfery oraz rotacja wszystkich logów | Dawid zbiera dowody techniczne; administrator zatwierdza |

Nie podano domyślnych okresów „na wszelki wypadek”. Wynik decyzji ma prowadzić
do wersjonowanego zapisu: ID Pxx, zakres kategorii/wersji, wartości i wyjątki,
osoba/rola zatwierdzająca, data, dowód i termin kolejnego przeglądu.
Do tego czasu 109/110/111 nie otrzymują zatwierdzonego wejścia do implementacji.

## Odbiór dokumentacji i zadania

- Review techniczne: Dawid Hnat; niezależna kontrola dokumentacji/QA: Marcel
  Głowacki. Sprawdzić źródłowy SHA, 14 tabel i granicę faktów/propozycji.
- Potwierdzić komplet D01–D22/P01–P18, lokalne odnośniki oraz wymagane CI
  ostatniego commita. Nie oznaczać retencji, eksportu, usuwania lub izolacji
  jako wdrożonych tylko na podstawie tego PR.
- Koordynator zapisuje właściwe decyzje w SCRUM-113 i odnośnik w SCRUM-94.
  Niezależny odbiór i merge dokumentacji nie zastąpią brakujących akceptacji.
- Nowy zakres organizacji, cel, źródło, okres lub dostawca wymaga ponownej
  kontroli spisu oraz screeningu; dokument zachowuje historię wersji.

SCRUM-94 pozostaje W toku. Nie ustawiono Gotowe podzadań, nie odczytywano
sekretów, realnej floty, logów klientów ani skrzynek. Nie uruchomiono retencji,
DSAR, usuwania, żywego WEBFLEET/SMTP ani zmian usług.
