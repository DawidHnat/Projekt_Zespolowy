# Jira → gałąź → CI → przegląd → merge

Każdy członek zespołu pracuje na własnej gałęzi powiązanej z zadaniem projektu
**SCRUM**. Po pushu CI testuje zmianę, a automatyzacja tworzy PR. Płatny przegląd
przez API AI oraz automatyczne scalanie pozostają wyłączone do decyzji zespołu.
Codzienny przebieg pracy i polecenia są w [CONTRIBUTING.md](../CONTRIBUTING.md).

## Co działa po scaleniu konfiguracji do main

1. `CI` uruchamia się na **push** i **pull_request**. Zapisuje commit gałęzi
   oraz aktualny commit gałęzi głównej. Testuje robocze połączenie obu wersji,
   bez wysyłania dodatkowego commita. Konflikt powoduje błąd CI.
2. Po zakończeniu CI `PR automation` uruchamia się z zaufanej gałęzi głównej.
   Dla gałęzi `feat/SCRUM-123-opis` (także `fix/docs/chore/refactor/test`)
   tworzy PR do gałęzi głównej, jeśli jeszcze go nie ma. Błąd CI pozostawia PR
   otwarty z informacją o wymaganej poprawce.
3. Domyślnie automat informuje, że API AI jest wyłączone. Po jego aktywacji
   pobiera diff przez API GitHuba, wysyła go do wybranego modelu i zapisuje
   komentarz oraz kontrolę **AI review**. Nie uruchamia kodu z PR z sekretami.
4. Automat może wykonać merge commit wyłącznie po przejściu wszystkich bramek
   poniżej. Pozostałe PR-y przegląda i scala człowiek. Jira nie jest modyfikowana
   automatycznie — zadanie zamyka jego właściciel.

Merge commit zachowuje autorów oryginalnych commitów. Ma to znaczenie w zadaniu
kursowym, którego kryterium obejmuje `git shortlog -sn --all`. PR utworzony
przez bota i scalony metodą squash mógłby przypisać nowy commit botowi.
Ręczny squash jest opcją przy świadomym zachowaniu autorstwa; automat go nie używa.

CI na push jest konieczne: PR utworzony tokenem `GITHUB_TOKEN` zwykle nie
uruchamia kolejnego workflow na zdarzenie `pull_request`.
[Dokumentacja GitHub](https://docs.github.com/en/actions/how-tos/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow).
Automat tworzy PR dopiero po zakończeniu CI, więc przy większym projekcie trzeba
poczekać na kontrolę; ręczne utworzenie PR jest zawsze dostępne.

## Warunki automatycznego merge

Wszystkie warunki muszą być spełnione jednocześnie:

- API AI jest jawnie włączone, sekret istnieje, a wybrany model zwrócił
  kompletną, poprawną odpowiedź: `approve`, ryzyko `low`, bez uwag.
- PR ma 1–8 plików i najwyżej 200 dodanych/usuniętych linii. Wszystkie pliki to
  `.md` pod `docs/user/` albo `docs/guides/` lub `.css` pod `frontend/src/`.
- Diff jest kompletny. Automat sprawdza liczbę plików, długości hunków i liczbę
  zmienionych linii. Brak patcha, plik binarny, zmiana nazwy, częściowy diff
  lub przekroczenie limitu blokują automatyczne scalanie. Zmieniane pliki muszą
  mieć zwykły tryb Git `100644`; symlinki i pliki wykonywalne wymagają człowieka.
- Gałąź pochodzi z tego repozytorium, a CI uruchomił `jczaja51`, `DawidHnat`,
  `jnazarewiczs` lub `mglowacki0`. Autor PR to członek zespołu albo bot,
  który utworzył PR po pushu członka zespołu.
- CI jest zielone dla bieżącego commita PR i aktualnego commita `main`.
  Dowód z artefaktu jest przypisany do tego samego repozytorium i runu CI.
- GitHub potwierdza gotowość scalania. Nie ma trybu draft, etykiety
  `human-review` ani aktualnego **Changes requested** od człowieka.
- Tuż przed merge automat ponownie sprawdza commit PR, commit `main`, przeglądy
  i etykiety, bieżącą próbę oraz najnowszy run CI dla tego SHA. Wywołanie API
  zawiera dokładny SHA PR. GitHub egzekwuje istniejące
  reguły gałęzi; automat nie używa uprawnień administratora do ich omijania.

Zmiany aplikacji w `.py`, `.tsx` lub `.ts`, migracji, kontraktów API, zależności,
Azure, Docker, GitHub Actions, skryptów automatyzacji oraz dokumentów zasad
wymagają człowieka. Można rozszerzyć ten zakres po zdobyciu doświadczenia,
ale sama zmiana polityki zawsze jest PR-em do ręcznego przeglądu.

Przegląd AI obejmuje do 50 plików i 100 kB kompletnego diffu. Większa zmiana
nie jest obcinana do limitu; automat prosi o przegląd człowieka. Tekst diffu
może zawierać błędne lub złośliwe instrukcje, dlatego model nie ma narzędzi,
a jego decyzja nie może ominąć deterministycznych bramek w `policy.py`.
Jeśli API, JSON lub dowód CI zawiedzie, PR pozostaje otwarty.

## Jednorazowe ustawienia właściciela repozytorium

Dawid albo inna osoba z prawami administratora powinna po scaleniu tej podstawy:

1. W **Settings → Actions → General → Workflow permissions** zezwolić Actions
   na tworzenie pull requestów (**Allow GitHub Actions to create and approve
   pull requests**). Pliki workflow deklarują własny minimalny zakres uprawnień;
   CI ma tylko odczyt, automatyzacja ma zapisy PR/checków i prawo scalania.
2. Zezwolić na **Allow merge commits** w **Settings → General → Pull Requests**.
   Można włączyć automatyczne usuwanie scalonych gałęzi.
3. Utworzyć etykietę `human-review`. Dodanie jej do PR blokuje automat.
4. Jeśli używany plan udostępnia reguły dla prywatnych repozytoriów, ustawić
   ochronę `main`: PR zamiast bezpośrednich pushów, wymagane kontrole **Backend**,
   **Frontend**, **PostgreSQL migrations**, **Automation policy**, aktualna gałąź
   względem `main`, zakaz force push i usuwania gałęzi głównej.
   Stały wymóg zatwierdzenia każdego PR przez człowieka również blokuje
   automatyczne scalanie małych zmian, co może być świadomym wyborem zespołu.

GitHub udostępnia ochronę gałęzi prywatnych repozytoriów w planach Pro/Team
i odpowiednich planach Enterprise.
[Dokumentacja ochrony gałęzi](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
Nie zmieniamy planu ani prywatności repozytorium. Bez ochrony serwerowej zasady
w tym pliku obowiązują zespół, ale GitHub może dopuścić ręczny push na `main`.

## Opcjonalne API AI i koszt

**Ta konfiguracja nie wykonuje płatnych wywołań domyślnie.** CI i automatyczne
PR-y nie wymagają konta OpenAI API. Można poprosić Codex o przejrzenie konkretnego
PR w aplikacji w ramach posiadanego planu, a potem samemu scalić zmianę.
Taki przegląd nie uruchamia tego workflow i nie daje mu sygnału do automerge.

Gdy zespół zdecyduje się na automatyczny przegląd przez API, właściciel ustawia:

| Miejsce w Settings → Secrets and variables → Actions | Nazwa | Wartość |
| --- | --- | --- |
| **Repository secret** | `AI_REVIEW_API_KEY` | Klucz projektu OpenAI API |
| **Repository variable** | `AI_REVIEW_MODEL` | Wybrany model obsługujący Responses API i Structured Outputs |
| **Repository variable** | `AI_REVIEW_ENABLED` | Dokładnie `true`; brak lub inna wartość wyłącza API i automerge |

Najpierw ustaw budżet projektu i kontrolę zużycia w panelu dostawcy. Klucza
nie wklejamy do Jiry, Discorda, PR ani `.env.example`. Diff prywatnego repozytorium
jest przesyłany do dostawcy modelu; nie powinien zawierać sekretów ani danych
rzeczywistych klientów. Cena zależy od wybranego modelu i liczby tokenów diffu;
abonament aplikacji Codex/ChatGPT nie jest budżetem tego API.
[Cennik OpenAI API](https://openai.com/api/pricing/).
Workflow ustawia `store: false` i wymaga poprawnej odpowiedzi Structured Outputs.
[Dokumentacja interfejsu](https://developers.openai.com/api/docs/guides/structured-outputs).

GitHub Models nie jest używany: usługa została wycofana 30 lipca 2026 r.
[Informacja GitHub](https://docs.github.com/en/github-models).

Zmiana `AI_REVIEW_ENABLED` na `false` wyłącza kolejne wywołania i automatyczne
scalanie. Już rozpoczęty run można anulować w zakładce **Actions**. Brak klucza,
modelu lub poprawnej odpowiedzi nigdy nie uruchamia merge.

## Gdy automat zostawi otwarty PR

Przeczytaj komentarz **Przegląd AI** i wynik CI. Dla błędu testów wykonaj poprawkę
i push. Jeśli zmienił się `main`, połącz aktualny `origin/main` ze swoją gałęzią
i wykonaj push, żeby powstał nowy dowód CI. Dla zmian wymagających człowieka
poproś drugą osobę o sprawdzenie kryteriów akceptacji i scalanie na GitHubie.
Nie obniżaj progów polityki, żeby przepchnąć konkretny PR.
