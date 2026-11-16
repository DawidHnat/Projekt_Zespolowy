# Review Sprintu 2 — scenariusz i karta protokołu

**Spotkanie i pełne DoD Story jeszcze niepotwierdzone.** PO potwierdził ten
stan 12.11.2026. Przygotowanie techniczne: SCRUM-127; odbiór: SCRUM-141;
organizacja spotkań i start S3: [SCRUM-142](https://fleet-flow.atlassian.net/browse/SCRUM-142).
Serwer: <https://fleet-flow.pl/>, wersja HTTP: <http://57.129.179.53/>.

## Przed spotkaniem

1. PO wybiera **całą Story faktycznie należącą do Sprintu 2**. Odczyt Jiry
   12.11 wskazuje SCRUM-84 (backup poza VPS) i SCRUM-91 (preferencje między
   urządzeniami), obie Do zrobienia. SCRUM-38/45/46 i SCRUM-127 są Zadaniami.
   Nie zmieniamy typów ani historii sprintów dla statystyki.
2. W SCRUM-141 zebrać wszystkie AC i 12 warunków [DoD](../DEFINITION_OF_DONE.md):
   wykonawca, data, SHA, środowisko, link oraz PASS/FAIL/BLOCKED. Developer
   dostarcza implementację; niezależny reviewer ocenia kod; Marcel odbiera QA;
   PO potwierdza zakres. Testy autora nie są odbiorem innej osoby.
3. Dawid potwierdza wdrożenie tego SHA, readiness oraz wynik smoke. Dla
   SCRUM-84 potrzebna jest uzgodniona decyzja storage i prawdziwy recovery;
   kopia na tym samym VPS lub sam runbook nie zamyka Story.
4. Przygotować uprawnione konto i bezpieczny scenariusz. Dane syntetyczne
   pozostają w izolacji; nie publikować danych floty. Bez testów żywego
   WEBFLEET/SMTP bez osobnego polecenia.

## Pokaz według potrzeby użytkownika

| Wybrana Story | Co pokazać | Dowód końca |
| --- | --- | --- |
| SCRUM-91: użytkownik wraca do swojego widoku w innej przeglądarce | Na dwóch niezależnych kontekstach zalogować to samo konto; zmienić i zapisać układ/filtry, odczytać na drugim; pokazać Anuluj, konflikt i błąd zapisu, izolację drugiego konta oraz świadomą migrację localStorage. | Wszystkie AC, wersjonowanie i backendowe preferencje, niezależne QA Marcela. Sam zapis lokalny nie spełnia tego zakresu. |
| SCRUM-84: administrator odzyskuje usługę po utracie VPS | Pokazać dowód harmonogramu i szyfrowanej kopii off-site oraz odtworzenie wydania, bazy i plików w izolacji, bez ujawniania danych. | Zatwierdzone storage/koszt/RPO/RTO, prawdziwy protokół recovery i QA. |
| Bramy jakości — dowód techniczny wspierający pokaz | Wersja serwera, ostatni main-run, testy/lint/deployment/smoke dla jednego SHA; czerwone #77/#78 z pominiętym deploymentem. | Dowody SCRUM-127/140. Nie zastępują odebranej Story. |

Wystarczy jedna pełna odebrana Story S2; pozostałe prace rozliczyć jawnie.
Pokaz dashboardu może uzupełnić Review, ale nie zastąpić wyboru Story.

## Karta do wypełnienia po rzeczywistym Review

| Pole | Wpis po wykonaniu |
| --- | --- |
| Data i uczestnicy | Do uzupełnienia przez PO |
| Story i potrzeba użytkownika | Klucz, pełny uzgodniony zakres |
| SHA, serwer i run wdrożenia | Konkretna pokazana wersja |
| AC oraz pełne DoD | Link do macierzy SCRUM-141 i raportu niezależnego QA |
| Wynik pokazu | Wykonane scenariusze i rzeczywisty rezultat |
| Feedback | Konkretne uwagi; przy braku uwag zapisać taki rzeczywisty wynik |
| Decyzje i dalsze zgłoszenia | Zaakceptowany zakres, błędy i właściciele |

Po Review zespół uzupełnia [retro S2](retro/sprint-2.md): co dobrze/źle,
stan działań S1, nowe uzgodnione działanie i właściciel. PO rozlicza otwarte
prace, kończy S2 i rozpoczyna istniejący S3 z celem i SCRUM-128/129.
[Instrukcja oddania](SPRINT_2_SUBMISSION.md) pozostaje szkicem do tego czasu.
