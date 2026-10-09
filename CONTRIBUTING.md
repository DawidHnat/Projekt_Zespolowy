# Współpraca

Na tym etapie przygotowujemy strukturę. Puste pliki pozostają puste, dopóki
osobne zadanie nie dotyczy implementacji. Zakres produktu i role są w README,
a ustalenia zespołu w TEAM_CONTRACT.md.

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
6. Drugi developer sprawdza zmianę, a QA potwierdza kryteria, jeśli dotyczy
   zachowania aplikacji. Poprawki trafiają na tę samą gałąź.
7. Po przeglądzie scal PR, zachowując autorstwo commitów. Następnie ustaw
   **Done** w Jirze i dodaj link do PR. Nie wysyłaj zmian bezpośrednio na `main`.

Sekrety, klucze prywatne i `.env` pozostają poza repozytorium. Przed pushem
sprawdzamy zakres zmian; testy i kontrole dodamy wraz z kodem, który sprawdzają.
Automatyczne PR-y, CI, przegląd API AI i automerge nie są obecnie skonfigurowane.

## Zależne zadania

Gdy następne zadanie wymaga kodu z PR oczekującego na review, utwórz gałąź
z gałęzi tego PR. PR kieruj tymczasowo do bezpośredniej gałęzi bazowej i wskaż
zależność w opisie. Po sprawdzeniu i scaleniu poprzednika przestaw bazę na
`main`. Każda gałąź ma własny klucz zadania i własne nowe commity. Takie PR-y
sprawdzamy i scalamy od najstarszej zależności. Nie omija to review ani QA.
