# Estymaty podzadań i kolejka QA

Stan dokumentacji: 25.10.2026. Zmiany w Jirze zapisano podczas przeglądu
24–25.10.2026; adnotacje estymat noszą datę rozpoczęcia przeglądu 24.10.

## Jak czytać punkty

W polu **Story point estimate** uzupełniono 30 podzadań w skali 1, 2, 3, 5, 8.
Każde ma uzasadnienie złożoności w opisie. To robocze szacunki całego zakresu,
do potwierdzenia przez wykonawców na Planningu, a nie zapis wspólnej sesji
Planning Poker, godziny ani pozostały czas pracy. Dla już ukończonych SCRUM-31/55
wyraźnie zaznaczono, że punkty dodano później.

Story zachowują swoje odrębne estymaty. Nie dodajemy punktów rodzica i dzieci
do jednej sumy; Sprint 1 i planowany Sprint 2 nadal mają po trzy Story i 21 SP.
Raport velocity Jiry nie uwzględnia estymat podzadań —
[dokumentacja Atlassian](https://support.atlassian.com/jira-software-cloud/docs/what-is-the-velocity-report/).
Zadania główne wspierające sprint, np. plan QA SCRUM-37 i integracyjny odbiór
SCRUM-63, pozostają bez dodatkowych SP. Suma dzieci nie zastępuje wyceny Story.

## Zapisane estymaty

| Podzadanie | SP | Uzasadnienie |
| --- | --- | --- |
| [SCRUM-19](https://fleet-flow.atlassian.net/browse/SCRUM-19) | 3 | chronione API, kontrakt pól i braków danych |
| [SCRUM-20](https://fleet-flow.atlassian.net/browse/SCRUM-20) | 3 | lista, wspólne filtry i stany API |
| [SCRUM-21](https://fleet-flow.atlassian.net/browse/SCRUM-21) | 5 | Mapbox, wybór pojazdu, nakładanie markerów i dostępność |
| [SCRUM-22](https://fleet-flow.atlassian.net/browse/SCRUM-22) | 3 | odświeżanie, cache i awarie źródła |
| [SCRUM-23](https://fleet-flow.atlassian.net/browse/SCRUM-23) | 3 | odbiór listy/mapy i przypadków brzegowych |
| [SCRUM-24](https://fleet-flow.atlassian.net/browse/SCRUM-24) | 5 | trwały import historii, idempotencja i granice dat |
| [SCRUM-25](https://fleet-flow.atlassian.net/browse/SCRUM-25) | 5 | szczegóły pojazdu, historia i formularze ręczne |
| [SCRUM-26](https://fleet-flow.atlassian.net/browse/SCRUM-26) | 3 | trwały zapis notatek, uprawnienia i konflikt edycji |
| [SCRUM-27](https://fleet-flow.atlassian.net/browse/SCRUM-27) | 2 | suma okresu i brakujące cele |
| [SCRUM-28](https://fleet-flow.atlassian.net/browse/SCRUM-28) | 3 | historia, trwałość notatek i dane ręczne pojazdu |
| [SCRUM-29](https://fleet-flow.atlassian.net/browse/SCRUM-29) | 3 | agregaty, miary i niepełne dane |
| [SCRUM-30](https://fleet-flow.atlassian.net/browse/SCRUM-30) | 3 | porównanie pojazdów, okresy i sortowanie |
| [SCRUM-31](https://fleet-flow.atlassian.net/browse/SCRUM-31) | 5 | reguły, deduplikacja, transakcje i granice dnia |
| [SCRUM-32](https://fleet-flow.atlassian.net/browse/SCRUM-32) | 3 | lista alertów i trwały odczyt użytkownika |
| [SCRUM-33](https://fleet-flow.atlassian.net/browse/SCRUM-33) | 3 | obliczenia, progi i regresja alertów |
| [SCRUM-38](https://fleet-flow.atlassian.net/browse/SCRUM-38) | 8 | modułowy dashboard, motywy, personalizacja i edytor układu |
| [SCRUM-39](https://fleet-flow.atlassian.net/browse/SCRUM-39) | 5 | FastAPI, PostgreSQL, migracje i CI |
| [SCRUM-40](https://fleet-flow.atlassian.net/browse/SCRUM-40) | 3 | odbiór motywów, układów i dostępności |
| [SCRUM-44](https://fleet-flow.atlassian.net/browse/SCRUM-44) | 5 | jednorazowy reset, limity i unieważnienie sesji |
| [SCRUM-45](https://fleet-flow.atlassian.net/browse/SCRUM-45) | 5 | zdjęcia, kafelki i strona ustawień |
| [SCRUM-46](https://fleet-flow.atlassian.net/browse/SCRUM-46) | 3 | zbiorowa edycja i wspólna paginacja |
| [SCRUM-51](https://fleet-flow.atlassian.net/browse/SCRUM-51) | 5 | ręczna kartoteka API, migracje i pierwszeństwo danych |
| [SCRUM-52](https://fleet-flow.atlassian.net/browse/SCRUM-52) | 5 | ręczne CRUD kierowców i transakcyjna historia przypisań |
| [SCRUM-53](https://fleet-flow.atlassian.net/browse/SCRUM-53) | 5 | formularze kierowców i integracja przypisań |
| [SCRUM-54](https://fleet-flow.atlassian.net/browse/SCRUM-54) | 3 | walidacja, role i historia przypisań |
| [SCRUM-55](https://fleet-flow.atlassian.net/browse/SCRUM-55) | 1 | struktura katalogów i zasady współpracy |
| [SCRUM-56](https://fleet-flow.atlassian.net/browse/SCRUM-56) | 3 | logowanie, sesje i reset z atrapą SMTP |
| [SCRUM-58](https://fleet-flow.atlassian.net/browse/SCRUM-58) | 5 | chronione pliki, walidacja uploadu i trwałe daty |
| [SCRUM-59](https://fleet-flow.atlassian.net/browse/SCRUM-59) | 5 | formularze dat i obsługa załączników |
| [SCRUM-60](https://fleet-flow.atlassian.net/browse/SCRUM-60) | 3 | limity plików, izolacja obiektów i strefy dat |

Poprawiono też nieaktualne odwołania w opisach: SCRUM-26/27 wskazują teraz
SCRUM-62, a SCRUM-29/30 — SCRUM-61. Hierarchia zgłoszeń była już poprawna.
Podzadania kierowców 52/53/54 opisują planowany Sprint 2 zamiast dawnego backlogu.

## Faza Testowanie

Kolejność kolumn: **Do zrobienia → W toku → W trakcie weryfikacji → Testowanie → Gotowe**.
Weryfikacja obejmuje review; Testowanie to kolejka niezależnego odbioru QA.
Przekazanie do tej kolumny nie jest wynikiem PASS ani dowodem ukończenia.

| Zgłoszenie | Zapisany etap | Odbiór |
| --- | --- | --- |
| SCRUM-13 — szkielet | Testowanie | Marcel w SCRUM-40 |
| SCRUM-16 — logowanie | Testowanie, nadal 5 SP | Marcel w SCRUM-56 |
| SCRUM-23 — lista/mapa | Testowanie, 3 SP | Marcel; najpierw scalone przyrosty, następnie retest SCRUM-51 |
| SCRUM-40 — szablon i układ | Testowanie, 3 SP | Marcel |
| SCRUM-56 — sesje/reset | Testowanie, 3 SP | Marcel; rzeczywista dostawa SMTP pozostaje osobnym nieuzgodnionym testem |

SCRUM-5 pozostaje W toku: ręczne metadane i pomiary SCRUM-51 nie są jeszcze
gotowe. Test części listy/mapy nie zamyka całej Story. SCRUM-15 pozostaje
W trakcie weryfikacji; potwierdzenie pól i jednostek źródła w SCRUM-14 jest
nadal potrzebne. Nie zmieniano istniejących statusów Done.

W widoku tablicy **Grupa → Subtask** widać punkty i statusy dzieci w osobnych
kolumnach. Widok bez grupowania pokazuje głównie rodziców, a ich dzieci
po rozwinięciu karty. Dlatego liczba kart w Testowaniu zależy od widoku.

## Najbliższa praca Marcela

1. Potwierdź plan i syntetyczne dane w SCRUM-37. Zapisz testowany SHA,
   środowisko, datę, przeglądarkę i rozmiar ekranu.
2. SCRUM-56: brak sesji, poprawne/błędne logowanie, wylogowanie, wygaśnięcie
   i cookies po HTTPS. Reset: neutralna odpowiedź, token wygasły/wykorzystany,
   limity i unieważnienie sesji, z atrapą SMTP.
3. SCRUM-40: czysty checkout, uruchomienie, motywy i style, zapis/anulowanie
   układu, klawiatura, Safari i mały ekran.
4. SCRUM-23: zgodność wyszukiwania i filtrów lista↔mapa, paginacja, wybór
   nakładających się markerów, pusty wynik, brak GPS, stare dane, błąd API,
   odzyskanie połączenia i zachowanie zaznaczenia. Dane SCRUM-51 odbierz
   osobno po implementacji; nie zastępuj ich fikcyjnymi wartościami.
5. Dla FAIL utwórz powiązane zgłoszenie z krokami odtworzenia i oczekiwanym
   wynikiem; po poprawce wykonaj retest. BLOCKED musi mieć konkretną przyczynę.
   Done wymaga spełnienia wszystkich kryteriów i braku błędów blokujących.

Szablon wiersza raportu, do wypełnienia dopiero po wykonaniu scenariusza:

| Scenariusz | Oczekiwany wynik | Faktyczny wynik | Status | Środowisko / SHA | Dowód / Bug |
| --- | --- | --- | --- | --- | --- |
| identyfikator i kroki | rezultat z kryterium | do wpisania | NIEWYKONANY | do wpisania | do wpisania |

Kontrola techniczna z przeglądu: HTTPS na VPS działa, a GET
`https://vps-9171bf52.vps.ovh.net/api/health/ready` zwrócił `{"status":"ok"}`
z kodem procesu 0. To sprawdzenie połączenia aplikacji z bazą, nie pełny
odbiór logowania, synchronizacji ani uprawnień. W tym przeglądzie nie wykonywano
funkcjonalnego QA ani żywego WEBFLEET/SMTP i nie zapisano fikcyjnych wyników PASS.

## Baza danych

**Pozostawiamy PostgreSQL.** Polecenie kursowe pozwala zespołowi wybrać stos;
nie wymaga MongoDB. Obecny kod ma PostgreSQL 17, SQLAlchemy, migracje Alembic
i testy PostgreSQL w CI. Model [danych](DATA_MODEL.md) wiąże pojazdy, kierowców,
pomiary, sesje i alerty; następne przyrosty dodadzą historię i notatki.

Klucze obce i ograniczenia unikalności już chronią relacje i duplikaty,
a worker korzysta z blokad doradczych PostgreSQL. Zmiana na MongoDB wymagałaby
przepisania tych mechanizmów, migracji i testów. Nie znaleziono wymagania
uzasadniającego taki koszt; pojemność i wydajność dla docelowej skali trzeba
ocenić na realnych pomiarach, nie na samej nazwie silnika.

Źródła kodu: `compose.local.yml`, `backend/app/core/models.py`,
`backend/app/modules/auth/models.py`, `backend/app/modules/fleet/sync.py`,
`backend/app/modules/analytics/models.py` oraz `backend/app/modules/analytics/service.py`.
Ograniczenia relacyjne: [dokumentacja PostgreSQL](https://www.postgresql.org/docs/17/ddl-constraints.html).

## Pozostałe otwarte sprawy

- Wykonać i udokumentować niezależne QA wskazane wyżej; sama kolumna nie zamyka odbioru.
- Potwierdzić robocze punkty i zakres na Planningu. Rozbudowane dzieci, zwłaszcza
  SCRUM-25/51, wymagają kontroli zakresu; nie uznajemy ich za małą pracę tylko dlatego,
  że Story zachowała wcześniejszą estymatę.
- Zatwierdzić i scalić PR dokumentacji #27 przez inną osobę; po scaleniu
  poczekać na wdrożenie i odświeżyć dowód zgodności serwera z origin/main.
- Udostępnienie Figmy/Jiry prowadzącemu pozostaje niepotwierdzone; PO odroczył
  ten krok do uzyskania danych prowadzącego.
- Przed implementacją przypisań kierowców ustalić regułę równoczesnych przypisań
  w SCRUM-52. Sprzeczny import kierowców z punktu 16 wymagań pozostaje do uzgodnienia;
  obowiązuje ręczne wprowadzanie kierowców.
