# Review PR i odbiory DoD — SCRUM-65

Właściciel: Jakub Czaja (PO). [Zadanie](https://fleet-flow.atlassian.net/browse/SCRUM-65).
Stan bazowy: **10.11.2026, 08:20 Europe/Warsaw**. To pomiar przed połową
Sprintu 2, a nie zapis przyszłego spotkania ani wynik jego retrospektywy.

## Uzgodniony rytm

10.11 PO potwierdził, że zespół uzgodnił codzienny przegląd otwartych PR-ów
i pierwszą odpowiedź do 24 godzin w dniach dostępności. Dokładnej godziny
spotkania nie ustalono w tym zapisie. Dostępność i zgłaszanie nieobecności
określa [kontrakt zespołu](../TEAM_CONTRACT.md).

1. PO przegląda kolejkę w każdym dniu pracy: właściciel, rzeczywisty klucz
   Jiry w opisie i gałęzi, recenzent inny niż autor, aktualny head i CI.
2. Recenzent zapisuje wynik: Approved, Changes requested albo komentarz
   z konkretnym zakresem i następnym krokiem. Prośba o review nie jest review.
   Autor odpowiada na uwagi na tej samej gałęzi; nowy head wymaga ponownej kontroli.
3. Przed otwieraniem kolejnej Story domykamy rozpoczętą. QA zapisuje scenariusze,
   wyniki PASS/FAIL/BLOCKED, wykonawcę, datę, środowisko i SHA. PO sprawdza
   komplet [DoD](../DEFINITION_OF_DONE.md), nie tylko status rodzica.
4. Merge kieruje przyrost do Testowania. Gotowe wymaga rzeczywistego odbioru
   i zgodnego wdrożenia. Wyjątek PO jest jawnym wyjątkiem, nie pełnym DoD.
5. Każdy zapisuje rzeczywisty czas analizy, implementacji, review i QA pod
   własnym kontem w Jirze: start, czas i wynik. Status W toku nie jest stoperem.

## Rzeczywiste autorstwo i review

Odczyt GitHuba obejmuje 72 PR-y, w tym 57 scalonych. Poniższe przykłady mają
klucze Jiry w opisach i gałęziach. Wskazane Approved dotyczą końcowego head
odpowiedniego PR-a. Każdy recenzent jest inną osobą niż autor.

| Osoba / konto | Własny scalony PR | Review cudzego scalonego PR |
| --- | --- | --- |
| Jakub Czaja / jczaja51 | [#55 — SCRUM-67](https://github.com/DawidHnat/Projekt_Zespolowy/pull/55), 06.11 | [#28 — SCRUM-37](https://github.com/DawidHnat/Projekt_Zespolowy/pull/28), autor mglowacki0; Approved 26.10 |
| Dawid Hnat / DawidHnat | [#60 — SCRUM-18](https://github.com/DawidHnat/Projekt_Zespolowy/pull/60), 06.11 | [#22 — SCRUM-34](https://github.com/DawidHnat/Projekt_Zespolowy/pull/22), autor jczaja51; Approved 20.10 |
| Jakub Nazarewicz / jnazarewiczs | [#61 — SCRUM-5](https://github.com/DawidHnat/Projekt_Zespolowy/pull/61), 06.11 | [#55 — SCRUM-67](https://github.com/DawidHnat/Projekt_Zespolowy/pull/55), autor jczaja51; Approved 06.11 |
| Marcel Głowacki / mglowacki0 | [#28 — SCRUM-37](https://github.com/DawidHnat/Projekt_Zespolowy/pull/28), 26.10 | [#29 — SCRUM-34](https://github.com/DawidHnat/Projekt_Zespolowy/pull/29), autor jczaja51; Approved 06.11 |

**4/4 osób spełnia warunek własnego scalonego PR i review cudzego.**
Nie zmieniano autorstwa ani historii. To nie usuwa historycznych braków review
innych PR-ów, braków QA ani niezgodnego commita z PR #54.

## Pomiar kolejki

Metryka liczy formalne review osoby innej niż autor, według `reviews` GitHuba.
Nie liczy próśb o review i nie udaje pomiaru pierwszego komentarza/odpowiedzi.
Próg 24 h jest surowym czasem kalendarzowym od `createdAt`, bez korekty
o nieobecności, weekendy i czas wyjścia z draftu. Służy do wskazania kolejki
do sprawdzenia, nie stanowi samodzielnego dowodu naruszenia uzgodnionego rytmu.

- Otwarte: **12**, w tym **1 draft** (#66).
- Zwykłe PR-y bez pierwszego formalnego review: **6** (#67–72).
- Zwykłe PR-y bez pierwszego review od ponad 24 h: **2** (#67, #68).
- Wraz z osobno oznaczonym dowodem celowo czerwonego CI #24: **3** ponad 24 h.
- #69–72 nie miały review, lecz od ich otwarcia upłynęło mniej niż 24 h.

| PR / zadanie | Stan przy pomiarze | Następny krok i właściciel |
| --- | --- | --- |
| [#67 / SCRUM-22](https://github.com/DawidHnat/Projekt_Zespolowy/pull/67) | Brak review, ponad 24 h | Jakub Nazarewicz: review head 5392b69; potem QA Marcela |
| [#68 / SCRUM-56](https://github.com/DawidHnat/Projekt_Zespolowy/pull/68) | Brak review, ponad 24 h | Dawid / Marcel: review b769217 i końcowy odbiór logowania; sam dokument nie zastąpi review auth |
| [#69 / SCRUM-20](https://github.com/DawidHnat/Projekt_Zespolowy/pull/69) | Brak review, poniżej 24 h | Nazarewicz / Marcel: review aa5821b i QA filtrów/stanu offline |
| [#70 / SCRUM-38](https://github.com/DawidHnat/Projekt_Zespolowy/pull/70) | Brak review, poniżej 24 h | Nazarewicz / Marcel: review 287e0bb i QA układu przy zmianie okna |
| [#71 / SCRUM-45](https://github.com/DawidHnat/Projekt_Zespolowy/pull/71) | Brak review, poniżej 24 h | Nazarewicz / Marcel: review c4a0b35, QA mobilnych wymiarów i zdjęć |
| [#72 / SCRUM-46](https://github.com/DawidHnat/Projekt_Zespolowy/pull/72) | Brak review, poniżej 24 h; baza #71 | Nazarewicz / Marcel: review 2877897; najpierw #71, potem baza main i ponowne CI |
| [#31 / SCRUM-49](https://github.com/DawidHnat/Projekt_Zespolowy/pull/31) | Marcel Approved dla obecnego head | PO i QA: sprawdzić komplet kryteriów; approval nie oznacza automatycznie gotowości do merge |
| [#52 / SCRUM-112](https://github.com/DawidHnat/Projekt_Zespolowy/pull/52) | Marcel Approved dla obecnego head | PO / Dawid: domknąć wymagane decyzje i zakres odbioru |
| [#53 / SCRUM-78](https://github.com/DawidHnat/Projekt_Zespolowy/pull/53) | Changes requested | Marcel: poprawić wskazaną regresję deploy; potem ponowne review |
| [#65 / SCRUM-15](https://github.com/DawidHnat/Projekt_Zespolowy/pull/65) | Changes requested | Dawid: poprawić limit źródła po ponowieniach, ponowne review |
| [#66 / SCRUM-22](https://github.com/DawidHnat/Projekt_Zespolowy/pull/66) | Draft, Changes requested | Dawid: poprawić konfigurację domyślnej częstotliwości, potem ready/review |
| [#24 / SCRUM-18](https://github.com/DawidHnat/Projekt_Zespolowy/pull/24) | Celowo czerwony dowód CI; bez review | Zachować jako dowód, nie scalać; wyłączony ze zwykłej kolejki |

Wszyscy autorzy są wskazani przez GitHub; wszystkie otwarte PR-y mają klucz
SCRUM w opisie i gałęzi. Każdy zwykły PR gotowy do review ma obecnie wskazanego
recenzenta innego niż autor. Draft #66 czeka na poprawkę autora.
Ten dokument nie jest wykonaniem review wymienionych zmian ani wysłaniem wiadomości.

## Pomiar pełnego DoD historyjek Sprintu 1

Zakres pomiaru: trzy historyjki produktu prezentowane na Review Sprintu 1,
nie wszystkie zadania techniczne ani liczniki statusów w zamkniętym sprincie.
Odczyt 10.11: **0/3 z potwierdzonym kompletem dowodów DoD**. Wszystkie trzy
rodzice mają administracyjny status Gotowe; poniższych braków nie usunięto
przez samą zmianę statusu ani zamknięcie sprintu.

| Story | Dowody i brak do potwierdzenia pełnego DoD | Właściciel następnego kroku |
| --- | --- | --- |
| [SCRUM-16](https://fleet-flow.atlassian.net/browse/SCRUM-16) — logowanie | PR #10 scalony bez Approved. [SCRUM-56](https://fleet-flow.atlassian.net/browse/SCRUM-56) zawiera testy autora/agenta i częściowy raport Marcela; pozostają niezależny przegląd implementacji auth i końcowy QA, w tym izolowany FF-QA-031. Pakiet #68 jest otwarty. | Dawid: rzeczywisty przegląd auth. Marcel: końcowy odbiór na wskazanym SHA. PO: zebranie dowodów, bez dopisywania historycznego approval. |
| [SCRUM-5](https://fleet-flow.atlassian.net/browse/SCRUM-5) — lista/mapa | #61 ma review i merge, lecz [SCRUM-23](https://fleet-flow.atlassian.net/browse/SCRUM-23) pozostaje W toku z częściowym odbiorem bez ustalonego SHA i scenariuszami BLOCKED. Otwarte poprawki listy/mapy/UI czekają na review/QA. | Nazarewicz: review wskazanych poprawek. Marcel: pełny retest kryteriów i raport SHA/PASS/FAIL/BLOCKED. |
| [SCRUM-15](https://fleet-flow.atlassian.net/browse/SCRUM-15) — synchronizacja | [SCRUM-64](https://fleet-flow.atlassian.net/browse/SCRUM-64) nadal wymaga operacyjnego odbioru po backupie i odtworzeniu, canary, cykli oraz QA. #65 ma Changes requested. Historyczne #11/#36 nie mają zapisanych reviews. | Dawid: backup/recovery i usunięcie uwag #65, potem autoryzowany canary; Marcel: niezależny odbiór. Bez uruchamiania żywego źródła w tym audycie. |

Wspólne wdrożenie sprawdzono bez logowania i danych floty: po `git fetch origin`
wersja strony HTTPS i strony HTTP serwera to **5b5fceb**, zgodna z `origin/main`;
`https://fleet-flow.pl/api/health/ready` odpowiada `200`, `{"status":"ok"}`.
To potwierdza wersję/gotowość, nie komplet QA powyższych Story.

## Kolejny pomiar i zakończenie działania

PO powtarza ten sam pomiar w połowie Sprintu 2 (około 11.11, w uzgodnionym
dniu dostępności) i zapisuje datę, surową kolejkę oraz dowody DoD. Wynik z 10.11
jest punktem odniesienia. Na retro Sprintu 2 zespół porównuje wyniki i decyduje,
czy utrzymać rytm. Nie zapisano jeszcze, że te przyszłe czynności się odbyły.

Ponowny odczyt GitHuba, bez zmieniania zdalnych danych:

```bash
gh pr list --repo DawidHnat/Projekt_Zespolowy --state all --limit 200 \
  --json number,url,state,isDraft,createdAt,headRefName,headRefOid,author,reviews,reviewRequests,body
```

Należy sprawdzić, czy limit objął całość (w tym pomiarze 72 < 200), odrzucić
własne review autora, osobno wykazać drafty i dowody testowe, a dla każdego
Approved porównać `reviews[].commit.oid` z `headRefOid`. Obliczyć wiek PR-ów
bez review względem zapisanego czasu pomiaru. Komentarze nie są objęte tą metryką.
Stan historyjek i raportów QA czytamy w Jirze, nie wnioskujemy go z listy PR-ów.

Do zamknięcia SCRUM-65 pozostają odbiór tej dokumentacji przez inną osobę,
scalenie PR, doprowadzenie jednej rozpoczętej Story do pełnego DoD oraz
pomiar w połowie sprintu. Ocena skuteczności wraca na retro Sprintu 2.
