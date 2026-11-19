# Oddania 3.2 i 4.2 — stan 19.11.2026

**Wykonawca: agent Codex na polecenie Jakuba Czai (jczaja51).** Kod `cb634da0ece8cd93424bfc16a5185cf817a0cbb1`,
środowisko GitHub CI i publiczny serwer. [Surowy filtr, SHA, joby, needs i dowody
całej czwórki](course/2026-11-19/technical-evidence.json).
**Oba pełne oddania: BLOCKED**, a nie gotowe na podstawie samych szablonów.

## Wykonane i potwierdzone

- Main/HTTP/HTTPS: **cb634da**, readiness **200 / status ok**,
  [run 44386951054](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/44386951054)
  i wszystkie 10 jobów **SUCCESS**. Odczyt agenta 19.11 po świeżym fetch.
- Wymagane konteksty: **Required CI, Backend (3.13), Lint**. Ochrona została
  już rozszerzona; nie zlecamy tego ponownie. Dowód właściciela:
  [SCRUM-140/10320](https://fleet-flow.atlassian.net/browse/SCRUM-140?focusedCommentId=10320).
- Review auth i ocena restore 16/91 są **PASS** w
  [10324](https://fleet-flow.atlassian.net/browse/SCRUM-141?focusedCommentId=10324)
  i [10345](https://fleet-flow.atlassian.net/browse/SCRUM-141?focusedCommentId=10345).
  #97/#99/#113/#114/#116 i dalsze dostarczone integracje są w main.
- [Konflikt #62](https://github.com/DawidHnat/Projekt_Zespolowy/pull/62):
  `f646c82`, review Nazarewicza i [CI 42271127635](https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/42271127635)
  PASS; zachowano type=button oraz disabled po wcześniejszym #30.
- Review i retro S2 odbyły się **18.11 z całą czwórką**, potwierdził PO 19.11:
  [SCRUM-142/10347](https://fleet-flow.atlassian.net/browse/SCRUM-142?focusedCommentId=10347).
  Aktualizacja protokołów jest w [PR #123](https://github.com/DawidHnat/Projekt_Zespolowy/pull/123);
  PO opisał mapę/szczegóły/zdjęcia, style i kafelki, zapis, aktualizacje/statusy oraz
  login/logout; SHA pokazu nieustalone. Ocena 65: spotkania pomagały, codzienna
  kontrola bez nich była nieregularna. Nowe działanie z 19.11: Jakub codziennie
  sprawdza kolejkę i przypomina reviewerom.

| Osoba | Własny scalony PR | Rzeczywiste review innego autora na końcowym head |
| --- | --- | --- |
| Jakub Czaja / jczaja51 | [#55](https://github.com/DawidHnat/Projekt_Zespolowy/pull/55), `9cff7e9` | [#28](https://github.com/DawidHnat/Projekt_Zespolowy/pull/28), autor mglowacki0, Approved `5a4a5e6` |
| Dawid Hnat / DawidHnat | [#60](https://github.com/DawidHnat/Projekt_Zespolowy/pull/60), `cbd861c` | [#22](https://github.com/DawidHnat/Projekt_Zespolowy/pull/22), autor jczaja51, Approved `e736bd1` |
| Jakub Nazarewicz / jnazarewiczs | [#61](https://github.com/DawidHnat/Projekt_Zespolowy/pull/61), `81ffe1e` | [#55](https://github.com/DawidHnat/Projekt_Zespolowy/pull/55), autor jczaja51, Approved `9cff7e9` |
| Marcel Głowacki / mglowacki0 | [#28](https://github.com/DawidHnat/Projekt_Zespolowy/pull/28), `5a4a5e6` | [#29](https://github.com/DawidHnat/Projekt_Zespolowy/pull/29), autor jczaja51, Approved `d0fc9c7` |

**4/4 PASS** powyższych dowodów. Dokładne polecenie kursowe `--limit 100`
zwróciło **100 wierszy**, wszystkie key_in_body=true; szerszy odczyt obejmuje
**108 scalonych PR**. Wyniku ograniczonego do 100 nie przedstawiamy jako
pełnego inwentarza. Historyczne 3 niezgodne tematy i dawne nazwy gałęzi są
znanymi niezgodnościami. Zgodnie z PO 18.11 nie wykonywano ponownego audytu
tych wyjątków, daty ochrony ani kontaktu z prowadzącym; nie wpisano wyniku zero.

## Pełne odbiory i konkretne blokady

[Pełne 4 AC + 12 DoD S1 i S2](qa/SCRUM-141-current.md) zbierają już istniejące
dowody. Marcel kończy wskazane brakujące QA 16/91 na oznaczonym wydaniu:
cookie/odwołanie API, pełne kombinacje preferencji, dwie osoby i migracja.
Autor testów nie podpisuje tego za niego. Dwa syntetyczne konta to użytkownicy
jednej firmy, bez wielofirmowości. [Decyzja PO o zakresie przeglądarek](qa/browser-scope-20261119.md)
wyłącza obowiązkowe Safari; nie zalicza niewykonanej próby. Jakub przejmuje
wyłącznie próby wymagające Maca/Safari; pozostałe QA nadal wykonuje Marcel.

| Zakres | Co pozostaje / odpowiedzialny | Stan |
| --- | --- | --- |
| 3.2 — pełne S1 | Marcel końcowy QA + PO zakres; aktualne dokumenty przez niezależny review/CI/main; zachować pakiet jeszcze przy S2 active | BLOCKED |
| Integracje S2 | Dawid aktualny review #101/a8476ac (CI PASS), potem zwykły merge/deploy/smoke; następnie #110 z review i QA Marcela 54/33 | BLOCKED |
| SCRUM-46 | [#120](https://github.com/DawidHnat/Projekt_Zespolowy/pull/120), 58 unit/build i 6/6 E2E PASS; Nazarewicz aktualny review, CI/main. Szersze QA 23/40 osobno | BLOCKED review/main |
| Prywatność | [#121](https://github.com/DawidHnat/Projekt_Zespolowy/pull/121), arkusz uzupełniony: rzeczywiste dane jednej firmy, właściciel wskazany lokalnie, czwórka i pokaz prowadzącemu, użyczenie do końca lutego 2027 i plan usunięcia. Brak konsultacji i pozostałych procedur; Jakub koordynuje | BLOCKED |
| 65 / retro | Miary i rzeczywista ocena 65 zapisane; nowe działanie Jakuba z 19.11 uzgodnione. Pozostają pełny DoD jednej Story w 141 i review/main dokumentów | BLOCKED |
| 4.2 — finalne | Po rozliczeniu zakresu i spełnieniu warunków zamknąć S2 id=3, uruchomić istniejący S3 id=4, potwierdzić 128/129 i odświeżyć CI/deploy/smoke po ostatnim merge | BLOCKED |

**12 pozostałych otwartych S2:** 21, 23, 40, 46, 64, 65, 94, 101, 133, 141,
142, 143 — [właściciele i warunki w przygotowanym protokole #123](https://github.com/DawidHnat/Projekt_Zespolowy/pull/123).
**Osobno 84: Do zrobienia / końcowy S5 id=37**, #35/#105 DEFERRED.
Nie blokuje S2/64/133 ani 16/91. Kontrolowany live 64 zachowuje własne AC
i kopie/rollback 18; nie uruchamiano go w zbieraniu dowodów. #119/150 poza S2,
bez ponawiania odmówionej prośby o reviewera i bez dodawania warunku do S2.

## Kolejność oddania

1. Po pełnym S1 zachować kompletne **3.2** z aktualnym server/main, surowym
   filtrem PR, #62, retro S1, nazwą/celem aktywnego S2 i pełnym DoD 16.
2. Po pełnych warunkach S2 i faktycznym rozliczeniu zakresu przełączyć
   **istniejące** S2→S3; nie przenosić prac dla wyniku i nie antydatować.
3. Po ostatnim merge poczekać na CI/deploy/smoke i potwierdzić SHA, needs,
   DoD/retro na main, aktywny S3 oraz 128/129; wtedy finalne **4.2**.
   Za dokumentację nie powtarzamy całego QA: zachowujemy SHA testu,
   porównujemy kod i wykonujemy potrzebny smoke/retest.

Gotowe lokalne pliki o nazwach ODPOWIEDZ_3_2_JAKUB_CZAJA.md i
ODPOWIEDZ_4_2_JAKUB_CZAJA.md zawierają jawny status niekompletności do czasu
tych dowodów. Każdy członek wysyła własną odpowiedź samodzielnie;
agent nie przesyła ich w cudzym imieniu. 142/143 pozostają otwarte do końca.
