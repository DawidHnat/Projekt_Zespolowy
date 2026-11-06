# SCRUM-98 — odświeżanie floty

Gałąź bazuje na SCRUM-83 / PR37 (i pośrednio SCRUM-26 / PR30).
Po scaleniu poprzedników należy przestawić bazę PR na main i ponowić wymagane CI.

Polling listy/mapy/summary używa pojedynczego timeoutu uruchamianego po zakończeniu
poprzedniego zestawu. Ręczne Ponów kolejkowane podczas żądania wykonuje najwyżej
jeden kolejny zestaw. Ukrycie karty lub offline usuwa timer i anuluje aktywne
żądania. Powrót do widocznej karty/online wykonuje odświeżenie bez czekania.
Błędy wydłużają odstęp 120/240/300 s, sukces przywraca 60 s. Ręczne Ponów omija
odstęp. Cleanup usuwa listenery, timer i anuluje żądania; zakończenie starego
żądania nie aktualizuje stanu nowej generacji filtra/konta.

Szczegóły mają osobny cykl zależny od wybranego ID, nie od obiektu listy.
Zmiana rozmiaru/strony listy nie ponawia szczegółów. Odświeżenie szczegółów tego
samego pojazdu zachowuje zamontowany edytor i jego szkic. Błąd przejściowy nie
zamyka panelu; 404 usuwa niedostępny wybór, 401 korzysta ze wspólnego wygaśnięcia
sesji. Provider jest kluczowany kontem: poprzedni wybór, wyniki, filtry i cykle
nie przechodzą do kolejnego konta. Rozmiar strony odczytywany jest dla nowego ID.

Weryfikacja developerska 28.10.2026, Node 22.18.0, PostgreSQL 17, syntetyczne API:

* `npm test`: 47 PASS, w tym deterministyczne testy braku nakładania, anulowania,
  wznowienia, backoffu, ręcznego retry i cleanup generacji.
* `npm run build`: PASS; istniejące ostrzeżenie rozmiaru chunku Mapbox.
* `npm run test:e2e`: 26/26 PASS, desktop 1440×1000 oraz mobile 390×844.
* Nowe E2E sprawdzają zdarzenia visibility/offline/online ze sterowanym zegarem,
  zachowanie niezapisanego celu po odświeżeniu, brak dodatkowego GET szczegółów
  po zmianie page_size i reset stanu po wylogowaniu/zalogowaniu inną rolą.
* Scenariusze visibility/online sterują właściwościami środowiska w przeglądarce;
  nie są dowodem rzeczywistego zawieszenia karty przez system operacyjny.
* Żadne wywołanie WEBFLEET/SMTP nie jest wykonywane; ruch zewnętrzny E2E blokuje.

Odbiór: inny developer reviewuje PR, QA zapisuje SHA i wynik rzeczywistego
przełączania kart oraz sieci w docelowej przeglądarce (w tym Safari). Wymagane
CI i niezależny odbiór pozostają warunkiem Done.
