# Definition of Done — Fleet-Flow

Zadanie implementacyjne jest **Gotowe**, gdy cały jego zakres został
zrecenzowany i scalony do `main` po przejściu wymaganego CI. Marcel prowadzi
ręczny odbiór wspólnej wersji w osobnym zadaniu na koniec sprintu, przed
Sprint Review. Zasady odbioru sprintu opisuje
[SCRUM-153](https://fleet-flow.atlassian.net/browse/SCRUM-153).

## Ukończenie zadania implementacyjnego

| Warunek | Jedno sprawdzenie / dowód | Kto i kiedy sprawdza |
| --- | --- | --- |
| Cały zakres zadania jest dostarczony i zrecenzowany. | PR wskazuje kryteria zadania, zakres zmiany i dowody wymaganych sprawdzeń. | **człowiek** — reviewer potwierdza zakres i wyniki przed **Approved**. |
| Zmiana trafiła do `main` przez PR z zatwierdzeniem innego developera. | PR ma co najmniej jedno aktualne **Approved** i stan **Merged**. | **warunek odbioru** — niezależny reviewer sprawdza ostatnią zmianę; właściciel potwierdza egzekwowanie PR i approval w aktualnych ustawieniach ochrony `main`. |
| Obowiązkowe CI przeszło dla ostatniej wersji PR. | Wszystkie wymagane kontrole w sekcji Checks są zielone; zatwierdzenie starszego commita nie wystarcza. | **pipeline** — `Required CI` odrzuca failure/skipped zależności; **warunek odbioru** — reviewer sprawdza listę wymaganych kontekstów w aktualnych ustawieniach ochrony `main` i zapisuje dowód. |
| Zmieniony frontend przechodzi testy i budowę. | `npm --prefix frontend test && npm --prefix frontend run build` kończy się kodem `0`. | **pipeline** — `Frontend build`, przy każdym PR i pushu do main: npm test, typecheck i build. |
| Zmieniony backend przechodzi kontrole kodu i testy bez żywych integracji. | W aktywnym środowisku Pythona: `cd backend && ruff check . && ruff format --check . && pytest` kończy się kodem `0`; CI dostarcza osobną bazę testową. | **pipeline** — `Backend (3.12)`, `Backend (3.13)`, `Backend (3.15)` i `Lint`: pytest z izolowaną bazą, Ruff check i format --check; bez żywego WEBFLEET/SMTP. |
| Frontend przechodzi automatyczną regresję przeglądarkową. | `Critical browser flows` albo oba joby `Critical browser flows (desktop)` i `Critical browser flows (mobile)` są zielone dla aktualnego SHA, zależnie od wersji workflow. | **pipeline** — oba profile muszą się wykonać. |
| Repozytorium nie zawiera sekretów ani danych klientów. | Przegląd zakładki Files changed potwierdza brak prywatnych kluczy, haseł, rzeczywistych `.env` i danych floty; sekrety wdrożenia pozostają w GitHub Actions. | **człowiek** — niezależny reviewer (Dawid Hnat lub Jakub Nazarewicz) przed approval sprawdza Files changed; developer sprawdza zakres przed push. Nie jest to deklaracja automatycznego skanera sekretów. |
| Dokumentacja odpowiada dostarczonej zmianie. | Zmienione instrukcje, zakres funkcji i kontrakty są aktualne. | **człowiek** — autor aktualizuje dokumentację, reviewer sprawdza ją razem z PR. |
| Zmiana schematu lub wdrożenia ma sprawdzone odtworzenie. | W PR/Jirze jest wynik próby przywrócenia kopii albo powrotu do wcześniejszego wydania, odpowiednio do zmiany. | **człowiek** — Dawid Hnat przed wdrożeniem zmian schematu/infrastruktury zapisuje próbę restore/rollback; Marcel w odbiorze sprawdza dowód i ograniczenia. |

## Ochrona gałęzi

Polityka projektu wymaga ochrony `main`: PR, co najmniej jedno aktualne
niezależne zatwierdzenie i zielone wymagane CI również dla administratorów.
Bezpośredni push do `main`, force push, usuwanie gałęzi i pominięcie
wymaganych kontroli są zabronione. Właściciel potwierdza rzeczywistą
konfigurację przy odbiorze (data, osoba, wymagane konteksty i dowód
w Jira/PR). Brak dostępu do ustawień lub rozbieżność oznacza BLOCKED;
sam dokument i szablon PR nie egzekwują tych wymagań.

## Odbiór i status zadania

Drugi developer wykonuje review. Autor może wykonać ręczne sprawdzenie
i zapisać w PR scenariusz, środowisko oraz wynik. Jeśli kryteria danego
zadania wymagają dodatkowego odbioru przed merge, wynik zapisujemy w PR
lub Jirze. Scalenie kompletnego PR do `main` po aktualnym **Approved**
i zielonym wymaganym CI kończy zadanie.
Reguła Jira **SCRUM: merge PR do main → Gotowe** odwzorowuje tę decyzję dla
klucza w gałęzi. Jej stan połączenia i testu jest w
[SCRUM-151](https://fleet-flow.atlassian.net/browse/SCRUM-151).

Automatyzacja dotyczy zadań i podzadań, z pominięciem Story i epików.
Nie zamyka innych zgłoszeń tylko dlatego, że są wspomniane w opisie PR.
Przed merge częściowego przyrostu wydzielamy jego własne zadanie i klucz.
Dużą Story zamykamy po spełnieniu jej pełnego zakresu; epik po zakresie epiku.
Merge do gałęzi zależności wymaga jeszcze dostarczenia do `main`.

Zadania opisujące sam odbiór lub inne działania bez kodu zamykamy po
dostarczeniu wyniku zgodnego z kryteriami. Błąd wykryty w regresji otrzymuje
własne zgłoszenie, priorytet i PR poprawki. Jego naprawa kończy się po retestach.

## QA sprintu i odbiór wydania

Na każdy sprint planujemy jedno zadanie ręcznej regresji dla Marcela.
Pod koniec sprintu Marcel sprawdza zmiany na wspólnym wydaniu. Dla zmian
Marcela scenariusz wykonuje inna osoba z zespołu. Zadanie QA ma status
**Testowanie** podczas odbioru. Wynik zawiera zakres, scenariusze,
PASS/FAIL/BLOCKED, SHA i środowisko. Korzystamy z istniejącej karty, jeśli
obejmuje potrzebny zakres. Oddzielny odbiór modułu, wdrożenia lub całego MVP
realizujemy według jego kryteriów.

Wdrożenie i regresja pozostają częścią odbioru modułu/wydania. Ich wynik
nie jest automatycznie potwierdzany przez status Gotowe zadania kodu.

| Warunek wydania | Dowód i odpowiedzialność |
| --- | --- |
| Aplikacja działa przez HTTPS na wspólnym serwerze. | QA sprawdza uzgodnione scenariusze modułu na uprawnionym koncie i zapisuje wynik; PO prezentuje zakres na Review. |
| Serwer udostępnia właściwy commit main. | `Post-deploy smoke` sprawdza SHA przebiegu w HTTP i HTTPS; PO przed oddaniem porównuje wdrożenie z aktualnym `origin/main`. |
| Backend i baza są gotowe. | `Post-deploy smoke` wymaga HTTP 200 z HTTPS `/api/health/ready`. |
| Regresja modułu ma jawny wynik i błędy. | QA zapisuje wynik w osobnym zadaniu; brakujący scenariusz pozostaje otwarty lub BLOCKED. |
| Awaria deployment/smoke ma obsługę. | Właściciel wdrożenia prowadzi zadanie naprawcze lub rollback i ponownie sprawdza wynik. |

Wymagania oddania kursowego, protokoły Review i wcześniejsze wyniki zachowują
własne kryteria. Zmiana statusów nie dopisuje historycznych PASS ani nie
potwierdza zaległych odbiorów.

## Bramy jakości Sprintu 2

Historia weryfikacji ochrony i wdrożenia jest udokumentowana w SCRUM-140
oraz w [ewidencji oddania](docs/COURSE_READINESS.md). Nie zastępuje
aktualnego odczytu ustawień ochrony. `Post-deploy smoke` jest kontrolą
wdrożenia po pushu do main; nie wymagamy go dla PR, jeśli workflow
pomija deployment zgodnie z warunkiem uruchomienia.
[Bieżące dowody i braki oddania](docs/COURSE_READINESS.md).

## SCRUM-101 — bezpieczeństwo przyrostu (ASVS 5.0.0)

Dla zmian w obszarze auth, sesji, uprawnień i danych zapisujemy
konkretne wymagania OWASP ASVS **v5.0.0** (identyfikatory `v5.0.0-X.Y.Z`),
wersję/commit testu, środowisko oraz wynik PASS/FAIL/BLOCKED lub umotywowane N/A.
Macierz i aktualne luki: [SCRUM-101](docs/security/SCRUM-101-ASVS-5.0.0-L2.md).
Nie oznaczamy pełnej zgodności ASVS L2 na podstawie wybranych kontroli.
Przed merge niezależny reviewer sprawdza wyniki regresji zmienianych kontroli
oraz testów migracji i odtworzenia, gdy dotyczą zmiany. Błędy krytyczne
i wysokie dotyczące zmiany zamykamy albo zapisujemy jawną decyzję PO o ryzyku.
Dodatkowy ręczny odbiór przed merge wynika z kryteriów zadania. Przekrojowa
regresja bezpieczeństwa ma osobne zadanie QA. Dowody nie mogą zawierać
sekretów ani danych klientów.


## SCRUM-121 — dowody i bramy bezpieczeństwa PR

Poniższe wymagania uzupełniają SCRUM-101. Stosujemy je
proporcjonalnie do zakresu zmiany, bez deklarowania pełnej
zgodności z OWASP ASVS L2.

### Zależność SCRUM-120 i zakres przyrostu

Bramy dowodowe dotyczą zmian w auth, sesjach,
uprawnieniach i danych. Nie stanowią zatwierdzenia
kompletnej macierzy ASVS L2 ani potwierdzenia PASS
bez wymaganych dowodów.

Pełny odbiór SCRUM-121 wymaga rozstrzygnięcia
zależności od SCRUM-120 oraz potwierdzenia zakresu
przez PO i niezależnego reviewera.

Jeżeli dostarczamy tylko częściowy przyrost,
wydzielamy go pod osobnym kluczem Jira w nazwie
gałęzi zgodnie z SCRUM-151. Zadanie obejmujące
pozostały zakres pozostaje otwarte.

Bieżące statusy PR-ów, wyniki CI, blokady i decyzje
zapisujemy w Jira lub opisie właściwego PR,
a nie w Definition of Done.

### Obowiązkowe bramy przed merge — bez N/A

Dla każdego PR obowiązują niezależny review i sprawdzenie aktualnego
SHA, rzeczywistej ochrony gałęzi oraz wszystkich jobów wymaganych
przez ustawienia i agregator `Required CI`. Dla każdego obowiązkowego
checka wpisujemy nazwę, wynik, link do jobu lub review i aktualny
head SHA (oraz testowany merge SHA, jeżeli inny).

Zgodnie z workflow CI zestaw obejmuje `Required CI`, `Lint`,
`Backend (3.12)`, `Backend (3.13)`, `Backend (3.15)`, `Frontend build`, `Backend image`,
`Dependency security`, `Source security`, `Secret security`,
`Markdown links` oraz `Critical browser flows` dla obu profili
(w jednym jobie lub osobnych jobach z nazwą profilu).

Nie oznaczamy obowiązkowych jobów N/A. Failure, skipped albo brak
aktualnego dowodu blokują merge. Zmiana nazw jobów wymaga sprawdzenia
agregatora i rzeczywistych kontekstów ochrony main. Checklistę traktujemy
jako zapis dowodów, a nie mechanizm egzekwowania.

### Zakres kontroli i wyjątki

- PR wskazuje konkretne identyfikatory OWASP ASVS v5.0.0
  z macierzy SCRUM-101/SCRUM-120, których dotyczy zmiana.
- Dla każdej kontroli zależnej od zakresu zapisujemy PASS, FAIL,
  BLOCKED albo N/A tylko jeżeli nie dotyczy zmiany, z uzasadnieniem
  i osobą akceptującą wyjątek. Brak dowodu nie jest N/A.
- Wynik zawiera SHA badanego commita, środowisko,
  scenariusz, datę, wykonawcę i link do dowodu.
- PASS z przeglądu kodu odróżniamy od PASS testu.
  Historycznych wyników nie przenosimy na nowy SHA
  bez ponownej weryfikacji.
- Otwarta lub niepełna macierz SCRUM-120 nie pozwala
  deklarować pełnego odbioru ASVS L2.

### Scenariusze bezpieczeństwa

Dla zmienionych obszarów wymagamy odpowiednich
testów pozytywnych i negatywnych:

- logowanie, wylogowanie, reset hasła, wygaśnięcie
  i odwołanie sesji;
- role admin/editor/viewer, autoryzacja obiektów,
  izolacja kont i danych (IDOR);
- Origin/CSRF przy zapisach oraz osobno CORS,
  w tym allowlista i preflight;
- walidacja danych, limity i błędy 401/403/409/422;
- ustawienia cookie, w tym Secure, HttpOnly,
  SameSite i wymagany prefiks nazwy;
- timeout bezczynności i absolutny limit sesji,
  jeśli dotyczą zmiany.

Brak testu oznaczamy BLOCKED lub NOT RUN z przyczyną,
a nie PASS. Nie testujemy żywego WEBFLEET ani SMTP
bez osobnej zgody i uzgodnionego zakresu.

### Migracje, rollback i decyzje o ryzyku

Przy zmianie schematu, sesji, cookie lub wdrożenia
PR zawiera:

- identyfikator i wynik migracji oraz środowisko;
- plan powrotu do poprzedniej wersji;
- dowód testu restore/rollback albo wyraźny BLOCKED;
- ograniczenia odwracalności i wpływ na istniejące dane;
- właściciela decyzji, jeśli rollback nie jest bezpieczny.

Istotne otwarte FAIL/BLOCKED wymagają naprawy przed merge.

Przyjęcie ryzyka wysokiego lub krytycznego wymaga
jawnej decyzji Product Ownera (PO), zgodnie z SCRUM-101.
Autor PR i reviewer nie mogą samodzielnie zastąpić
decyzji PO.

Decyzję zapisujemy w powiązanym zadaniu Jira i linkujemy
w PR. Wymagane dane: ID ASVS, opis i poziom ryzyka,
uzasadnienie odstępstwa, środki kompensujące, właściciel,
termin ponownej oceny, data oraz osoba zatwierdzająca.

Ryzyka niższe akceptuje PO lub osoba z udokumentowanym
upoważnieniem PO. Decyzja także wymaga zapisu w Jira.

Brak decyzji pozostawia BLOCKED. Przyjęcie ryzyka
nie zmienia FAIL na PASS i nie zastępuje testów,
niezależnego review ani formalnego odbioru.

### Niezależna weryfikacja

Reviewer inny niż autor sprawdza zakres ASVS,
dowody dla aktualnego SHA, wyjątki, brak sekretów,
migracje oraz ograniczenia rollbacku.
Wymagane kontrole CI muszą być zielone.
QA zapisuje własny wynik, jeśli wymaga tego zadanie.
Regresja przekrojowa sprintu pozostaje osobna.
