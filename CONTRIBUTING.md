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
6. Drugi developer sprawdza zmianę, a QA potwierdza kryteria, jeśli dotyczy
   zachowania aplikacji. Poprawki trafiają na tę samą gałąź.
7. Po przeglądzie scal PR, zachowując autorstwo commitów, i dodaj link w Jirze.
   Ustaw **Done** dopiero po spełnieniu wszystkich kryteriów zadania oraz odbiorze
   QA. Scalenie częściowego przyrostu nie zamyka całej Story.
   Nie wysyłaj zmian bezpośrednio na `main`.

Sekrety, klucze prywatne i `.env` pozostają poza repozytorium. Przed pushem
sprawdzamy zakres zmian; nowe zachowanie sprawdzamy odpowiednimi testami.
CI sprawdza backend i frontend. Automatyczne PR-y, płatny przegląd API AI
i automerge nie są skonfigurowane.

## Zależne zadania

Gdy następne zadanie wymaga kodu z PR oczekującego na review, utwórz gałąź
z gałęzi tego PR. PR kieruj tymczasowo do bezpośredniej gałęzi bazowej i wskaż
zależność w opisie. Po sprawdzeniu i scaleniu poprzednika przestaw bazę na
`main`. Każda gałąź ma własny klucz zadania i własne nowe commity. Takie PR-y
sprawdzamy i scalamy od najstarszej zależności. Nie omija to review ani QA.

Frontend sprawdzamy poleceniami `npm test` i `npm run build` w `frontend/`.
Zmiany wyglądu wymagają sprawdzenia w przeglądarce na komputerze i małym ekranie.
Uzgodnienia UI opisuje [system wyglądu](docs/DESIGN_SYSTEM.md).

## Sprawdzanie linków Markdown

Aby sprawdzić lokalne linki w dokumentacji, uruchom z głównego katalogu repozytorium:

    python scripts/check_markdown_links.py

Aby uruchomić testy skryptu:

    python -m unittest discover -s tests -p "test_markdown_links.py" -v

Skrypt pomija linki zewnętrzne, odnośniki do nagłówków i przykłady
w blokach kodu. Brakujący plik powoduje zakończenie z kodem błędu 1.

Kontrola uruchamia się automatycznie w GitHub Actions.
