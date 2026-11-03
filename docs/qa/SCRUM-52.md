# SCRUM-52 — ręczna kartoteka i relacje wiele do wielu

Decyzja PO z 28.10.2026: wielu kierowców jednego pojazdu jednocześnie oraz
wiele pojazdów jednego kierowcy. Kierowcy, kontakt, kategorie i przypisania
powstają wyłącznie ręcznie. WEBFLEET nie zapisuje żadnej z tych tabel.

## API i zakres

- GET `/api/v1/drivers/categories`: wersjonowany katalog `pl-driving-categories-v1`.
- GET `/api/v1/drivers` i `/summary`: listy i agregaty w bieżącym źródle;
  filtry q, active, assigned, category, vehicle_id; stabilne sorty name_asc,
  name_desc, vehicles_asc, vehicles_desc i strony maksymalnie 100.
- POST `/api/v1/drivers/search`: ten sam odczyt i podsumowanie, z parametrami
  w JSON. Frontend używa tego wariantu przy wyszukiwaniu kontaktu, aby telefon
  lub e-mail nie trafiały do URL i logu żądań. Wymaga sesji i poprawnego Origin.
- POST `/api/v1/drivers`, GET/PATCH `/{id}`: kartoteka. Nowa osoba wymaga
  osobnych imienia/nazwiska i identyfikatora. Kontakt jest opcjonalny i może
  być współdzielony. Identyfikator jest unikalny w źródle, z Unicode casefold.
- GET/POST `/{id}/assignments`, PATCH `/{id}/assignments/{assignment_id}/close`:
  paginowana historia, nowe przypisanie od teraz i zamknięcie istniejącego.

Każda zmiana profilu lub relacji wymaga bieżącego `version`. Blokada wiersza
kierowcy oraz indeks aktywnej pary eliminują równoległe duplikaty; konflikt
zwraca 409. Blokady pojazdów mają wspólną kolejność. Różni kierowcy mogą
pozostawać przypisani do tego samego auta. Dezaktywacja zamyka aktywne relacje,
a ponowna aktywacja nie otwiera ich samoczynnie. Nie ma fizycznego usuwania.

Admin/editor zapisuje, viewer czyta. Serwer sprawdza rolę, Origin, źródło,
wersję oraz aktywność kierowcy/pojazdu przy nowym przypisaniu. Obce UUID nie
udostępniają rekordu. Pole source_account nie należy do wejścia API.

Lista zwraca pełną liczbę przypisanych aut i stabilny pierwszy pojazd,
a pełne relacje odczytuje się stronicowaną historią. Złączenie 1:wiele nie
powiela osób. Kategorie i pierwszy pojazd są pobierane zbiorczo dla strony.
Agregaty dotyczą całego wyniku filtrów. Ocena zgodności kategorii ma jawne
`not_evaluated` i null zamiast pozornego zera — należy do SCRUM-70.
Katalog jest danymi deklarowanymi ręcznie, nie dowodem prawa do prowadzenia.

API floty dodaje opcjonalne `driver_count` i `driver_preview` (do trzech osób).
Stare pole `driver` wskazuje osobę wyłącznie przy jednym przypisaniu.
Tabela i kafelki pokazują „N kierowców” oraz podgląd nazw; pełna kartoteka
frontendowa jest osobnym SCRUM-53. Nie zmieniono ID widgetów ani preferencji.

## Migracja 0008_manual_drivers

Poprzednik: 0007_user_roles. UUID, display_name i dotychczasowe powiązania
pozostają zachowane. Migracja nie dzieli arbitralnie nazwy na imię/nazwisko,
nie generuje identyfikatora osoby i nie zgaduje dat początku. `needs_completion`
wymaga ręcznego uzupełnienia starego profilu; `started_at=null` oznacza nieznaną
datę, a `recorded_at` jest czasem zapisania obserwowanego powiązania.

Źródło starego kierowcy ustalane jest tylko, jeżeli wszystkie powiązane auta
mają jedno źródło. Niejednoznaczne i niepowiązane osoby zachowują source_account
null i wymagają prywatnego wyjaśnienia przez operatora. Nie są ujawniane przez
nową kartotekę konkretnego źródła. Historyczne relacje są zachowane także dla
nich. Istniejący zakres widoczności nazwy kierowcy przy jego pojeździe pozostaje;
nie rozszerza to odczytu kontaktu ani profilu między źródłami.

Przed wdrożeniem: review, QA, odbiór zależności i sprawdzony backup. W oknie
infrastruktury zatrzymać API/worker/CLI zapisujące dane, wykonać standardowe
`python -m alembic upgrade head`, sprawdzić liczby i UUID w prywatnej konsoli,
uzupełnić niejednoznaczne stare rekordy po decyzji właściciela. Nie publikować
nazw, kontaktu, UUID rzeczywistych osób ani zapytań z nimi w dowodach QA.

Rollback aplikacji zachowuje rozszerzony schemat. DDL downgrade do
0007_user_roles jest dopuszczalny tylko, gdy nie powstały nowe profile,
kategorie ani historia, której stary schemat nie potrafi przedstawić. Migracja
przerywa taki downgrade transakcyjnie zamiast usuwać nowe dane. Testuje to
syntetyczny scenariusz upgrade/odmowa/downgrade. Nie wykonywano migracji VPS.

## Historia przejazdów i dalszy odbiór

Zmiana przypisania nie modyfikuje zapisanych faktów ani adnotacji przejazdu.
Importer SCRUM-24 ma korzystać z okresów historycznych i utrwalać identyfikację;
przy wielu osobach lub nieznanym początku nie wolno wybierać pierwszej osoby
jako kierowcy dawnego przejazdu. Pełny scenariusz historii odbiera się z 24/53/54.
Polityka dostępu i dopuszczenie rzeczywistych danych pozostają w SCRUM-94/48.

Testy: Ruff, pytest z izolowanym PostgreSQL, kanoniczne kontrakty i generacja TS,
frontend test/build oraz browser E2E. PostgreSQL bada odmowę utraty danych,
równoległe wersje i wielu kierowców oraz ponowną synchronizację bez nadpisania
lokalnych profili/relacji. Dane są syntetyczne; brak żywych WEBFLEET/SMTP.
Niezależny QA SCRUM-54 i review nadal wymagane.
