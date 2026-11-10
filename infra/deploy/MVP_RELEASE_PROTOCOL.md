# Protokół odbioru wydania MVP na VPS — SCRUM-18

## Cel, zakres i właściciel

Dawid Hnat odpowiada za jeden wspólny protokół wydania MVP na VPS. Bieżący
sprint, przypisanie i status zadania odczytujemy z Jiry; wcześniejszy opis
„Plan: Sprint 3” jest historyczny. Działające SSH potwierdza wyłącznie dostęp
administracyjny zgodnie z SCRUM-12, a nie wdrożenie ani odbiór aplikacji.

Protokół dotyczy jednego, niezmiennego wydania. Każdy zapis wyniku musi odnosić
się do konkretnego commita i środowiska. Nie oznaczamy testów ani kontroli jako
zaliczonych na podstawie planu, deklaracji autora, starego wyniku ani samego
zielonego CI.

## Zasady dowodów i statusów

Każda kontrola ma osobny wiersz w śladzie wydania zawierający wszystkie pola:

| Kontrola | Wymagany zakres | SHA i digest | Środowisko | Czas UTC | Dowód / link | Oczekiwany wynik | Rzeczywisty wynik | Status | Wykonawca | Niezależny odbiorca |
|---|---|---|---|---|---|---|---|---|---|---|
| `<ID i nazwa kontroli>` | `<zakres, zadanie i zależności>` | `<pełny SHA; digest artefaktu lub BLOCKED>` | `<host / środowisko / baza>` | `<YYYY-MM-DDThh:mm:ssZ>` | `<link lub lokalizacja bez danych klientów>` | `<konkretne kryterium>` | `<zaobserwowany wynik>` | `PASS / FAIL / BLOCKED` | `<osoba>` | `<inna osoba albo BLOCKED>` |

Wiersz bez dowodu albo bez wymaganego SHA, środowiska, czasu UTC, wykonawcy
lub odbiorcy ma status `BLOCKED`. Rzeczywisty wynik niezgodny z oczekiwanym ma
status `FAIL`. `PASS` wymaga kompletnego, odtwarzalnego dowodu i niezależnego
odbioru. P0 nie może przejść na podstawie deklaracji autora ani wyłącznie
zielonego CI.

Dowody nie mogą zawierać sekretów, prywatnych kluczy, haseł, tokenów ani danych
klientów. Link do runu CI jest dowodem wyniku CI, ale nie zastępuje testu na
docelowym VPS, sprawdzenia recovery, niezależnego review ani odbioru QA.

## Bramy odbioru

Kontrole poniżej wykonujemy dla tego samego wydania. Numery SCRUM odnoszą się
do wymagań i zależności; bieżące statusy sprawdzamy w Jirze. Jeżeli kontrola
nie ma jeszcze zatwierdzonego zakresu lub dowodu, wpisujemy `BLOCKED` — nie
zakładamy, że jest ukończona.

| ID | Kontrola i wymagany zakres | Warunek PASS |
|---|---|---|
| P0-01 | PR-y zawarte w wydaniu, niezależne review, `Required CI` i kontrole 95/101 | Każdy PR ma formalny approval niezależnej osoby. Dokładny SHA wydania ma zielone `Required CI`; właściwe kontrole security gates (95) i macierz kontroli (101) mają własne dowody. Brak review lub wymaganej ochrony `main` to `BLOCKED`, nie PASS. |
| P0-02 | E2E 83 po zależności 26 | Końcowy E2E jest powtórzony na docelowej bazie `main` po spełnieniu zależności 26. Zapis zawiera dokładny SHA aplikacji, identyfikację bazy/środowiska bez sekretów i wynik. |
| P0-03 | Auth/session QA 56 oraz fleet/map/cache QA 23 | Odbiory potwierdzają swój zatwierdzony zakres i ograniczenia. Nie zastępują regresji ani demo całego przyrostu w 17. |
| P0-04 | Pre-deploy recovery i migracje: 84 | Istnieje aktualna, zaszyfrowana kopia poza VPS oraz udokumentowany i wykonany test odtworzenia z tej kopii; potwierdzono miejsce na dysku, zatwierdzony plan migracji i rollbacku, zgodność starej i nowej aplikacji oraz brak sekretów w artefakcie. Lokalny dump lub test lokalnego odtworzenia nie dowodzi recovery po utracie VPS. |
| P0-05 | Pochodzenie wydania: 100 | SHA wydania jest dokładny. Digest artefaktu jest niezmienny i sprawdzony end-to-end od builda do wdrożenia. Jeśli implementacja lub dowód zgodności digestu nie istnieje, wpisujemy `BLOCKED` — nie wywodzimy digestu z samego SHA ani nie deklarujemy zgodności. |
| P0-06 | Uruchomiona aplikacja i stan danych | Potwierdzono zatwierdzoną wersję React/FastAPI/PostgreSQL, wynik migracji, liveness i readiness, połączenie z DB oraz bezpieczne logi. Poprzednia wersja i wykonalna procedura rollbacku są dostępne. |
| P0-07 | Edge i HTTPS: 67/96 | Na docelowym adresie sprawdzono właściwą domenę i certyfikat, `Secure`/`HttpOnly` cookies, dozwolony Origin, nagłówki i zachowanie klienta przez zaufany reverse proxy. HSTS włącza się dopiero po potwierdzonym docelowym HTTPS. |
| P0-08 | Post-deploy smoke na zatwierdzonym koncie i środowisku | Sprawdzono kolejno login → lista/mapa albo jawny fallback → szczegóły → logout, odpowiedzi API, stan DB, wiek pomiarów, `last_success_at` źródła i brak regresji 5xx. Dowód używa wyłącznie zatwierdzonego konta/środowiska i nie ujawnia danych klientów. Każda awaria blokuje odbiór oraz wymaga zapisania reakcji i decyzji o rollbacku. |
| P0-09 | Zakres użycia: syntetyczny albo realna flota | Przed oceną wydania jawnie zapisano, czy jest ono wyłącznie syntetycznym demo, czy dopuszcza realną flotę. Dla wydania wyłącznie syntetycznego P0-09 ma `PASS` tylko wtedy, gdy ślad potwierdza użycie wyłącznie danych syntetycznych, brak żywego WEBFLEET i brak wysyłki SMTP; warunki 94/48/64 są oznaczone jako poza zakresem tego wydania i pozostają osobną bramą przed użyciem realnej floty. Dla wydania obejmującego realną flotę wymagane są zatwierdzone decyzje 94, egzekwowanie właściwego zakresu dostępu 48 i odrębnie autoryzowany operacyjny odbiór sync 64; brak któregokolwiek dowodu to `BLOCKED` i blokuje takie wdrożenie. Demo syntetyczne jawnie opisuje ograniczenia i nie jest odbiorem realnej floty. Żywego WEBFLEET ani wysyłki SMTP nie uruchamiamy bez osobnego, wyraźnego polecenia. |
| P0-10 | Operacyjne zamknięcie: 99/87 | Operator potwierdził monitoring i alarmowanie (99), stan recovery i kontrolę po wdrożeniu. Dokumentacja wskazuje adres, wersję i instrukcję odtworzenia; ślad wydania został zapisany zgodnie z 87. |
| P0-11 | Regresja i odbiór całego przyrostu: 17 | Końcowa regresja/demo obejmuje cały zatwierdzony przyrost, a QA i review są udokumentowane. Częściowy PR nie zamyka nadrzędnej Story. |

P0 oznacza bramę obowiązkową dla odbioru wydania. Odbiór jest możliwy dopiero,
gdy wszystkie wymagane P0 mają `PASS`; wyjątek nie może ukryć `FAIL` ani
`BLOCKED`. Zakres syntetyczny nie jest wyjątkiem od tej reguły: dla P0-09
stanowi jawnie zdefiniowaną ścieżkę `PASS`, jeśli ograniczenie wyłącznie do
danych syntetycznych i wyłączenie integracji live mają dowody. Warunki 94/48/64
nie są wtedy wymaganymi kontrolami tego wydania, ale pozostają nierozstrzygnięte
przed jakimkolwiek użyciem realnej floty. Jeżeli zakres wydania obejmuje realną
flotę, brak dowodu któregokolwiek warunku P0-09 oznacza `BLOCKED` i blokuje
odbiór tego wdrożenia.

## Przebieg dla konkretnego wydania

1. Z Jiry ustal zakres, zależności, wykonawców i odbiorców; jawnie określ
   przeznaczenie wydania jako wyłącznie syntetyczne albo obejmujące realną flotę.
   Nie wyprowadzaj statusu sprintu z historycznej dokumentacji.
2. Wybierz dokładny SHA `main` i PR-y, które składają się na wydanie. Zapisz
   SHA, docelowe środowisko, identyfikator runu `Required CI` i digest artefaktu
   (albo jawny `BLOCKED`, jeśli digest nie jest weryfikowalny).
3. Przed wdrożeniem zamknij bramy review, QA, recovery, kompatybilności,
   migracji i planu rollbacku. Brakujący dowód zatrzymuje wydanie.
4. Wdróż wyłącznie zatwierdzony artefakt i wykonaj kontrole stanu aplikacji,
   bazy, HTTPS oraz smoke. Zapisz wyniki w wierszach powiązanych z tym samym
   SHA i środowiskiem.
5. Przy awarii oznacz właściwą kontrolę `FAIL`, zapisz reakcję, decyzję o
   rollbacku i wynik kontroli po przywróceniu. Nie przekształcaj awarii w PASS
   przez ponowne wdrożenie bez zachowania nieudanego wyniku.
6. Zapisz kompletny ślad wydania zgodnie z 87. Odbiór końcowy następuje dopiero
   po niezależnym review, QA, wymaganych P0 `PASS` oraz potwierdzeniu operatora.

## Odpowiedzialność i granice

SCRUM-18 odpowiada za wspólny odbiór wydania. Zakresy 84 (kopie/recovery),
100 (pochodzenie i digest/SBOM), 95 (security gates i rzeczywista ochrona
`main`), 101 (macierz kontroli), 67/96 (edge/HTTPS), 12 (SSH) i 17 (końcowa
regresja) pozostają odrębnymi zadaniami i zależnościami. SSH jest tylko
kontrolą dostępu, a nie dowodem wdrożenia. Wcześniejsze numery i oznaczenia
sprintów nie zastępują tego wykazu SCRUM.

Protokół zapisuje wymagania i sposób udowodnienia odbioru; sam w sobie nie
potwierdza, że którakolwiek kontrola została wykonana, usługa aktywowana ani
że wydanie jest odebrane.
