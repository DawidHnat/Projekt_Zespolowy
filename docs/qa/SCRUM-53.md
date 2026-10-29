# SCRUM-53 — kartoteka kierowców

Gałąź opiera się na API i migracji SCRUM-52 (PR #50). Nie ma nowej migracji,
importu kierowców ani fikcyjnych rekordów w aplikacji. Syntetyczne profile
są wyłącznie w opt-in fixture dedykowanej lokalnej bazie E2E.

## Zachowanie

- Lista/kafelki: kontakt, ręczne kategorie, status, pierwszy pojazd + liczba
  pozostałych; pełna lista20 aut ma +19, przejście do stron historii.
- Wspólne filtry q, aktywność, przypisania i kategorie/brak kategorii;
  stabilne sorty nazw/pojazdów oraz oddzielny własny porządek.
- Cztery moduły pokazują agregaty całego wyniku filtrów. Ocena zgodności
  kategorii jest jawnie niewdrożona, nie ma pozornej liczby zero.
- Admin/editor ręcznie tworzy i edytuje osoby, dodaje/kończy przypisania.
  Viewer ma odczyt; API nadal odrzuca zapis niezależnie od kontrolek UI.
- Formularz pokazuje błędy przy polach. Błąd zapisu i 409 zachowują szkic;
  przy równoległym zapisie użytkownik odczytuje bieżące dane i świadomie
  ponawia swój formularz. Nie ma automatycznego nadpisywania.
- Dezaktywacja kończy aktywne przypisania, zachowuje historię; ponowna
  aktywacja nie odtwarza przypisań. Poprzednie przejazdy nie zmieniają osoby.
- Osobny lokalny układ konta/przeglądarki: Zapisz/Anuluj/Reset, moduły,
  rozmiary wszystkich lub zaznaczonych kart, klawiatura i uchwyt pointer,
  porządek przez przeciąganie albo Wyżej/Niżej. Pozostałe strony zachowują
  swoje preferencje. Wszystkie moduły można ukryć i ponownie włączyć.
- W localStorage są wyłącznie preferencje i UUID porządku (do 2000);
  kontakt, frazy wyszukiwania, formularz i odpowiedzi API pozostają w pamięci.
  Wylogowanie/wygaśnięcie sesji usuwa panel, formularz i filtry osoby.

## Automatyczne dowody

`npm test`, `npm run build`, pełna regresja `npm run test:e2e` z izolowanym
PostgreSQL; Ruff check/format i pytest również z PostgreSQL. Nowe scenariusze
w `frontend/e2e/drivers.spec.ts` obejmują:

1. Walidację, zapis, duplikat identyfikatora i ponowienie po 503.
2. Równoległą edycję 409, zachowany szkic, Escape i powrót fokusu.
3. +19 dla 20 aut, kolejną stronę, zakończenie i nowe przypisanie, dezaktywację.
4. Wyszukiwanie kontaktu/pojazdu, cały wynik filtrów, strony i viewer 403.
5. Axe oraz klawiaturę listy/kart/panelu w jasnym klasycznym i ciemnym szkle,
   komputer 1440 i telefon 390, szkic porządku/rozmiaru i brak zmiany innych preferencji.
6. Zmianę rozmiaru wybranej karty (suwak/pointer), ukrycie wszystkich modułów,
   odzyskanie Reset i izolację konta po wygaśnięciu sesji.

Backend bada porządek przed paginacją, brak duplikatów/obcych osób, agregaty
braku kategorii, limit 2000 i walidację telefonu. Istniejące kontrakty i testy
migracji/równoległych zapisów SCRUM-52 pozostają częścią pełnego zestawu.
Przykład żądania POST search jest w kanonicznym contracts/api-design.json;
formalny odbiór kontraktu pozostaje w SCRUM-36/108.

## Niezależny odbiór SCRUM-54

Na konkretnym SHA i środowisku tester sprawdza także Safari, dotykowe gesty,
długie nazwiska/kontakty, wiele kategorii, retry kategorii i listy, nested panel
pojazdu i focus po jego zamknięciu, offline/backoff oraz zachowanie filtrów
po edycji. Playwright Chromium/axe nie zastępują tego odbioru ani czytnika ekranu.
Wynik zapisać z SHA, środowiskiem i PASS/FAIL/BLOCKED. Review i merge są osobne.

Dopuszczenie rzeczywistych danych i polityki są w SCRUM-94/48. Egzekwowanie zgodności
kategorii należy do SCRUM-70; import historii i identyfikacja historyczna do SCRUM-24.
Nie wykonywano migracji VPS ani wywołań żywego WEBFLEET/SMTP.
