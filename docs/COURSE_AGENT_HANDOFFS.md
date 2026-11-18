# Polecenia dla agentów — domknięcie oddań 3.2 i 4.2

Stan 18.11.2026, [SCRUM-143](https://fleet-flow.atlassian.net/browse/SCRUM-143).
Poniższe teksty są gotowe do przekazania agentom właściwych osób; ich przygotowanie
nie oznacza wykonania pracy przez te osoby. Najpierw Dawid i Nazarewicz,
następnie końcowy odbiór Marcela; rzeczywiste Review/retro prowadzi PO po odbiorze.

## Dawid

```text
Repozytorium: https://github.com/DawidHnat/Projekt_Zespolowy
Cel: domknąć swój zakres do oddań Cursora 3.2 (S1) i 4.2 (S2).
Przeczytaj AGENTS.md, README, CONTRIBUTING, DEFINITION_OF_DONE.md oraz aktualne opisy i najnowsze komentarze wskazanych zadań. Zachowaj lokalne zmiany; pracuj na bieżącym main lub istniejącej gałęzi właściwego PR. Wyniki zapisuj z wykonawcą, datą, SHA, środowiskiem i PASS/FAIL/BLOCKED. Agent opisuje własne wykonanie wprost; nie przypisuj go człowiekowi.
Decyzja PO z 18.11: dawne niezgodne tematy commitów, nazwy gałęzi i kontakt z prowadzącym pomijamy w dalszej pracy. Zachowaj nowe commity poprawne, nie przepisuj historii. Bez automerge, żywego WEBFLEET/SMTP, sekretów i danych klientów. Dane testowe wyłącznie w izolacji. Nie twórz kolejnych zgłoszeń dla już istniejących zakresów.

Działasz dla Dawida Hnata — właściciela repozytorium i niezależnego reviewera. Wykonaj pracę i zapisz dowody, zamiast kończyć na planie.

1. PR #99 (SCRUM-91/144/145/146): sprawdź aktualny head i CI. Jakub Czaja dołożył 7f5aca0: właściciel lokalnej migracji powstaje przed GET; błąd/przerwanie odczytu A nie udostępnia importu B. Naprawiono też nawigację testu do Pulpitu i mobilne menu. Lokalnie: 55 testów frontendu, build, 193 backendowe z PostgreSQL i 84 E2E PASS; nowe regresje wcześniej 4/4 FAIL. Przejrzyj CAŁY końcowy diff, w tym Origin, wielkie liczby i izolację kont, i wykonaj rzeczywiste niezależne review. Przy poprawkach wymagane nowe CI.
2. Dawne Changes requested jczaja51 dotyczy 1aecb98. Autor dodatkowych poprawek nie zatwierdza własnego nowego kodu. Po Twoim niezależnym review rozlicz stare uwagi i nieaktualny stan review zgodnie z ochroną GitHub, z uzasadnieniem. Scalaj dopiero po spełnieniu wszystkich bramek, bez obejścia ochrony. Odbiór całej Story pozostaje u QA/PO.
3. SCRUM-140: konto jczaja51 nie ma admin/maintain. Na swoim koncie właściciela dodaj osobno wymagane Lint i Backend (3.13), pozostawiając Required CI oraz wszystkie dotychczasowe reguły, w tym aktualność gałęzi, niezależne zatwierdzenie i ochronę administratorów. Nie wymagaj deploy/smoke dla PR. Zapisz odczyt branches/main lub rules/branches/main i sprawdź blokadę czerwonych dowodów #77/#78; NIE SCALAJ #24/#77/#78.
4. SCRUM-16/56/141: wykonaj końcowy całościowy review bieżącego kodu logowania, sesji, logout/expiry, autoryzacji API/UI, cookie, Origin oraz czyszczenia stanu między kartami. Uwzględnij istniejące dowody expiry 2/2 i macierz ASVS; sam dokument ASVS nie zamyka review. Nie rozszerzaj czterech AC logowania o żywe doręczenie SMTP z osobnego SCRUM-44. Potwierdzone nowe błędy napraw przez właściwy PR.
5. Sprawdź lokalny dowód odtworzenia docs/qa/SCRUM-91-restore-20261118.md z PR #99: PostgreSQL 17.11, schema 0007, rollback przez 0006 do 0005, upgrade i restore odzyskują użytkownika oraz obie preferencje z wersjami/datami. Wykonawca to agent Jakuba Czai. Oceń przydatność do DoD i zapisz swój wynik; jeśli dowód wymaga uzupełnienia, wykonaj je wyłącznie w izolacji. Nie deklaruj na tej podstawie backupu off-site SCRUM-84.
6. Przejrzyj także bieżący PR #97 z dokumentacją oddania; nowe SHA wymaga Twojego review. Scal sprawdzone PR-y w kolejności pozwalającej rozwiązać ewentualne konflikty dokumentacji, poczekaj na deploy/smoke ostatniego main i potwierdź SHA HTTP + readiness HTTPS. Przekaż Marcelowi ostateczny SHA do odbioru.
7. Zapisz rezultat w SCRUM-140, SCRUM-56 i SCRUM-141: wymagane checki, wynik review auth/PR, ocena restore, ostatni main-run i wdrożenie. Oddziel wykonane od oczekujących. Nie potwierdzaj za zespół spotkań Review/retro.

Wynik końcowy: linki i jednoznaczna lista pozostałych blokad.
```

## Marcel

```text
Repozytorium: https://github.com/DawidHnat/Projekt_Zespolowy
Cel: domknąć swój zakres do oddań Cursora 3.2 (S1) i 4.2 (S2).
Przeczytaj AGENTS.md, README, CONTRIBUTING, DEFINITION_OF_DONE.md oraz aktualne opisy i najnowsze komentarze wskazanych zadań. Zachowaj lokalne zmiany; pracuj na bieżącym main lub istniejącej gałęzi właściwego PR. Wyniki zapisuj z wykonawcą, datą, SHA, środowiskiem i PASS/FAIL/BLOCKED. Agent opisuje własne wykonanie wprost; nie przypisuj go człowiekowi.
Decyzja PO z 18.11: dawne niezgodne tematy commitów, nazwy gałęzi i kontakt z prowadzącym pomijamy w dalszej pracy. Zachowaj nowe commity poprawne, nie przepisuj historii. Bez automerge, żywego WEBFLEET/SMTP, sekretów i danych klientów. Dane testowe wyłącznie w izolacji. Nie twórz kolejnych zgłoszeń dla już istniejących zakresów.

Działasz dla Marcela Głowackiego — niezależnego QA. Priorytet SCRUM-141: pełny odbiór SCRUM-16 z S1 i SCRUM-91 z S2.

1. Najpierw sprawdź, że poprawki PR #99 są scalone po niezależnym review i CI oraz wdrożone. Odbiór wydania wykonuj na pełnym SHA odpowiadającym HTTP data-build-sha i ostatniemu zielonemu main-run, z HTTPS readiness 200. Jeśli jeszcze czeka review/merge, nie odbieraj starego main jako poprawionego; przygotuj warunki i sprawdź dostęp do testów.
2. Użyj istniejących macierzy AC + 12 DoD z komentarzy 10254/10255 w SCRUM-141. Kontrolowane expiry FF-QA-031 jest już 2/2 PASS; Offline ma potwierdzony komunikat i zachowany szkic. Uwzględnij te dowody i ich SHA, nie przepisuj ich jako nowych prób ani nie oznaczaj jako niewykonanych.
3. SCRUM-16: zamknij brakujące próby cookie HttpOnly/Secure na końcowym HTTPS, Origin, odmowy starej sesji po logout i odpowiednie retesty. Powiąż pełny code review Dawida, dokumentację/odtworzenie i decyzję PO. Odbierz wszystkie cztery AC logowania. Szerszy SCRUM-56 i żywy SMTP z SCRUM-44 mogą pozostać otwarte osobno.
4. SCRUM-91: wykonaj procedurę A–E z docs/qa/SCRUM-91.md na dwóch niezależnych kontekstach tego samego konta oraz drugim uzgodnionym koncie. Sprawdź Pulpit/Pojazdy, rozmiary, filtry/sort/limit, Zapisz/Anuluj/Reset, konflikt i obie decyzje, Offline z późniejszym odczytem wartości/wersji API, migrację i izolację A→B. Dodano wariant pierwszego GET A z błędem lub przerwaniem: B nie dostaje importu A, a powrót na A pozwala na jego jawną migrację.
5. Potwierdź retest SCRUM-144/145/146 na finalnym wydaniu. Użyj istniejących testów API dla Origin i dużych liczb; bez rzeczywistych tokenów w raportach. Lokalne 84/84 E2E Jakuba Czai jest dowodem wykonawcy, nie Twoim nowym ręcznym testem.
6. Testy syntetyczne wykonuj w dedykowanej bazie fleet_flow_test_e2e. Na wspólnym serwerze korzystaj tylko z zatwierdzonych kont bez danych klientów; nie twórz tam fikcyjnych rekordów ani nie zmieniaj haseł współdzielonych kont. Przy braku dostępu wykonaj możliwy zakres w izolacji i opisz dokładny brak.
7. Zapisz pełne dwie decyzje odbioru w SCRUM-141 oraz wynik w SCRUM-56/SCRUM-91 i zgłoszeniach błędów. Każde kryterium: wykonawca, data, SHA, środowisko, wynik i dowód. Gdy wszystkie warunki spełniono, napisz to jednoznacznie; gdy brakuje jednego, wskaż konkretnie którego.

Wynik końcowy: S1 PASS/BLOCKED + braki; S2 PASS/BLOCKED + braki; osobny pozostały zakres SMTP. Nie wpisuj nieodbytego Review/retro i nie uruchamiaj S3.
```

## Jakub Nazarewicz

```text
Repozytorium: https://github.com/DawidHnat/Projekt_Zespolowy
Cel: domknąć swój zakres do oddań Cursora 3.2 (S1) i 4.2 (S2).
Przeczytaj AGENTS.md, README, CONTRIBUTING, DEFINITION_OF_DONE.md oraz aktualne opisy i najnowsze komentarze wskazanych zadań. Zachowaj lokalne zmiany; pracuj na bieżącym main lub istniejącej gałęzi właściwego PR. Wyniki zapisuj z wykonawcą, datą, SHA, środowiskiem i PASS/FAIL/BLOCKED. Agent opisuje własne wykonanie wprost; nie przypisuj go człowiekowi.
Decyzja PO z 18.11: dawne niezgodne tematy commitów, nazwy gałęzi i kontakt z prowadzącym pomijamy w dalszej pracy. Zachowaj nowe commity poprawne, nie przepisuj historii. Bez automerge, żywego WEBFLEET/SMTP, sekretów i danych klientów. Dane testowe wyłącznie w izolacji. Nie twórz kolejnych zgłoszeń dla już istniejących zakresów.

Działasz dla Jakuba Nazarewicza — właściciela SCRUM-91 i pierwotnego autora PR #99.

1. Pobierz aktualny PR #99, zamiast wracać do 1aecb98. Jakub Czaja dołożył commit 7f5aca0 i połączył main: właściciel importu jest wiązany przed GET, dodano 4 regresje błędu/przerwania A→B z powrotem do A, naprawiono przejście z Ustawień na Pulpit i logout mobile w teście. Lokalne wyniki: 55 testów frontendu, build, 193 backendowe z PostgreSQL i 84 E2E PASS; PR jest gotowy do review Dawida. Nie implementuj tych samych poprawek drugi raz.
2. Sprawdź bieżące CI i kompletność czterech AC SCRUM-91. Jeśli CI lub niezależny QA ujawni nową konkretną usterkę, popraw ten zakres na tej samej gałęzi, zachowując nowe poprawki Jakuba i oryginalne autorstwo. Frontend: npm test, npm run build i zachowanie w przeglądarce; backend: Ruff/format/pytest z PostgreSQL. Nie zwiększaj timeoutów dla ukrycia błędu i nie pomijaj testów.
3. Dopnij autorskie przekazanie w SCRUM-91: aktualny head/CI, link do niezależnego review Dawida, docs/qa/SCRUM-91.md i raport restore. Po merge podaj faktyczny main SHA i wdrożenie. Współpracuj z Dawidem w kolejności merge #99/#97; nie odbieraj ani nie zatwierdzaj własnego kodu.
4. Zapewnij Marcelowi powtarzalne warunki testu dwóch kontekstów i dwóch syntetycznych kont w izolacji. Jeśli serwer wymaga zatwierdzonych kont, ustal to bez publikowania haseł lub tworzenia fikcyjnych danych produktu. Nie zastępuj niezależnego QA własnym PASS.
5. Przygotuj krótki pokaz po odbiorze: zapisz układ/filtry w jednej przeglądarce → odtwórz w drugiej → pokaż Anuluj i konflikt. Zapis spotkania wykonuje PO po rzeczywistym Review.
6. SCRUM-129 pozostaje istniejącym wybitym oknem do zaplanowania w aktywnym S3 (frontend/vite.config.ts i VehicleMap.tsx). Do tych oddań nie trzeba teraz optymalizować całego bundla.

Wynik końcowy: aktualne przekazanie, linki PR/CI/QA i wyłącznie rzeczywiste pozostałe blokady.
```
