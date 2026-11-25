
# Współpraca

`main` ma uruchamialny frontend, backend i konfigurację lokalnej bazy.
Pozostałe puste pliki pozostają
puste, dopóki osobne zadanie nie dotyczy implementacji. Zakres produktu
i role są w README, a ustalenia zespołu w TEAM_CONTRACT.md.

## Jedno zadanie — jedna gałąź — jeden PR

1. Wybierz zadanie w projekcie **SCRUM**, przypisz je sobie i ustal kryteria
   akceptacji. Przed pracą ustaw **In Progress**.
2. Pobierz aktualny `main` i utwórz gałąź z rzeczywistym kluczem zadania:

   ```bash
   git switch main
   git pull --ff-only
   git switch -c feat/SCRUM-123-krotki-opis
   ```

   Prefiksy: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`.
3. Zmieniaj pliki potrzebne do zadania. Uzgodnij wspólne API przed równoległą
   pracą frontendu i backendu. Każdy commituje pod własnym imieniem i adresem
   e-mail przypisanym do swojego konta GitHub.
4. Sprawdź `git diff` i `git status`, dodaj konkretne pliki, utwórz commit
   z kluczem zadania i wykonaj `git push -u origin NAZWA-GALEZI`.
5. Utwórz PR do `main` na GitHubie. Wpisz klucz SCRUM, opis zmiany i sposób
   sprawdzenia. Niedokończony PR oznacz jako draft.
6. Przed scaleniem drugi developer wykonuje review. Przed **Approved**
   sprawdza zakres zmiany względem kryteriów i wyniki wymaganych kontroli.
   Autor może dodatkowo sprawdzić zmianę ręcznie. Jeśli to zrobi, zapisuje
   w PR, co sprawdził, w jakim środowisku i z jakim wynikiem. Gdy kryteria
   zadania wymagają osobnego odbioru przed merge, dołącz jego wynik do PR.
   Poprawki trafiają na tę samą gałąź.
7. Gdy cały zakres zadania jest dostarczony, aktualne review jest zatwierdzone,
   a wymagane CI jest zielone, scal PR do `main`, zachowując autorstwo commitów.
   Zadanie implementacyjne przechodzi wtedy do **Gotowe**. Reguła Jira
   **SCRUM: merge PR do main → Gotowe** dotyczy zadań i podzadań wskazanych
   kluczem w gałęzi. Story i epiki zamykamy po ich pełnym zakresie.
   Stan połączenia i testu reguły śledzi
   [SCRUM-151](https://fleet-flow.atlassian.net/browse/SCRUM-151).
   Nie wysyłaj zmian bezpośrednio na `main`.

Na Planningu dodajemy do sprintu jedno zadanie przekrojowego QA. Marcel
prowadzi ręczny odbiór wspólnej wersji w końcówce sprintu, przed Sprint
Review. Status **Testowanie** służy osobnym zadaniom QA. Zadania odbioru
modułu lub wdrożenia wykonujemy zgodnie z ich kryteriami. Błąd znaleziony
w regresji otrzymuje zgłoszenie i PR poprawki. Wdrożenie i smoke sprawdza
pipeline. Awaria ma zadanie naprawcze.

Jeden klucz w gałęzi wskazuje zadanie w całości kończone przez PR. Częściowy
przyrost otrzymuje własne zadanie i klucz przed merge; nie zamyka pozostałego
zakresu, rodzica ani osobnego QA. Zadania bez kodu zamykamy po dostarczeniu
ich wyniku. Szczegóły: [Definition of Done](DEFINITION_OF_DONE.md).

Sekrety, klucze prywatne i `.env` pozostają poza repozytorium. Przed pushem
sprawdzamy zakres zmian; nowe zachowanie sprawdzamy odpowiednimi testami.
CI sprawdza backend i frontend. Automatyczne PR-y, płatny przegląd API AI
i automerge nie są skonfigurowane.

## Zależne zadania

Gdy następne zadanie wymaga kodu z PR oczekującego na review, utwórz gałąź
z gałęzi tego PR. PR kieruj tymczasowo do bezpośredniej gałęzi bazowej i wskaż
zależność w opisie. Po sprawdzeniu i scaleniu poprzednika przestaw bazę na
`main`. Każda gałąź ma własny klucz zadania i własne nowe commity. Takie PR-y
sprawdzamy i scalamy od najstarszej zależności. Każdy PR przechodzi niezależne
review i wymagane CI.

Przy odtwarzaniu dawnych zależności sprawdzamy obecność rzeczywistego
przyrostu w aktualnym `main`, nie sam status Merged. Źródłowe commity,
bazy, osobne PR-y i warunki odbioru opisuje
[rejestr integracji SCRUM-133](docs/integration/SCRUM-133.md).


Frontend sprawdzamy poleceniami `npm test` i `npm run build` w `frontend/`.
`npm run test:e2e` buduje frontend, a następnie uruchamia Playwright na
zbudowanych assetach z lokalnym backendem i dedykowaną bazą E2E.
Zmiany wyglądu można sprawdzić testem przeglądarkowym na komputerze i małym
ekranie. Scenariusze ręcznego odbioru planujemy w QA sprintu.
Uzgodnienia UI opisuje [system wyglądu](docs/DESIGN_SYSTEM.md).

## Sprawdzanie linków Markdown

Aby sprawdzić lokalne linki w dokumentacji, uruchom z głównego katalogu repozytorium:

    python scripts/check_markdown_links.py

Aby uruchomić testy skryptu, w tym dodatkowe testy regresyjne:

    python -m unittest discover -s tests -p "test_markdown_links*.py" -v

Skrypt pomija linki zewnętrzne, odnośniki do nagłówków i przykłady
w blokach kodu. Brakujący plik powoduje zakończenie z kodem błędu 1.

Kontrola uruchamia się automatycznie w GitHub Actions.

**W trakcie weryfikacji** obejmuje review i wymagane CI przed merge.
**Testowanie** służy osobnym zadaniom QA/regresji. Oba statusy należą do
kategorii W toku. Kryteria przejść, sposób zapisu błędów i rytm spotkań opisują
[zasady pracy Scrum](docs/SCRUM_WORKFLOW.md).
