# Wkład zespołu w Sprint 3

Roboczy odczyt wykonano **27.11.2026 o 16:46:40 CET**. Jira podaje początek
20.11 o 07:15:30.480 CET i planowany koniec 27.11 o 23:59:59.999 CET.
Wersja końcowa wymaga odczytu rzeczywistego zamknięcia Sprintu 3.
[Tablica Jira](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1)

| Osoba | Login GitHub | Commity na `main` | Commity na gałęziach `origin` | PR do `main` | PR do gałęzi zależnych | Review cudzych PR-ów |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Jakub Czaja | `jczaja51` | 17 | 46 | 14 | 6 | 110 |
| Dawid Hnat | `DawidHnat` | 0 | 0 | 0 | 0 | 46 |
| Autor zapisany w Git jako DawidHnat | `dawidhstud` | 0 | 10 | 0 | 0 | 0 |
| Jakub Nazarewicz | `jnazarewiczs` | 0 | 13 | 0 | 1 | 12 |
| Marcel Głowacki | `mglowacki0` | 13 | 42 | 5 | 0 | 11 |

Commity bez merge są liczone po SHA i czasie commitu. Kolumna gałęzi `origin`
obejmuje również commity z `main`. PR liczy się w chwili scalenia, według
gałęzi docelowej. Wysłane review cudzych PR-ów liczą się niezależnie od
wyniku, w tym komentarze formalne i później odwołane przeglądy. Boty,
review w szkicu i konta spoza zespołu są wyłączone. GitHub powiązał próbki
autorstwa z kontami. Dziesięć commitów podpisanych w Git jako DawidHnat
GitHub przypisał do `dawidhstud`. Połączenie tych tożsamości w jednym
wierszu wymaga potwierdzenia Dawida. Odczyt `main` to `17ea095`.
[Przykładowy commit Czai](https://github.com/DawidHnat/Projekt_Zespolowy/commit/9892f87) ·
[Przykładowy commit Marcela](https://github.com/DawidHnat/Projekt_Zespolowy/commit/1e5c51d)

## Powtórzenie pomiaru

Wykonaj `git fetch --prune origin` w klonie zespołu. Ustaw w poniższym bloku
rzeczywisty czas graniczny w UTC, odczytany z Jira po zamknięciu Sprintu 3.
Skrypt używa adresu autora wyłącznie lokalnie do grupowania aliasów i
weryfikuje jego powiązanie z loginem przez API GitHub.

```bash
CUTOFF_UTC='2026-11-27T22:59:59.999+00:00' python3 - <<'PYTHON'
import json
import os
import subprocess
from collections import Counter
from datetime import datetime

start = datetime.fromisoformat("2026-11-20T06:15:30.480+00:00")
cutoff = datetime.fromisoformat(os.environ["CUTOFF_UTC"])
team = ("jczaja51", "DawidHnat", "dawidhstud", "jnazarewiczs", "mglowacki0")
identities = {}

def read(*args):
    return subprocess.check_output(args, text=True)

def in_window(value):
    return bool(value) and start <= datetime.fromisoformat(value) <= cutoff

def count_commits(ref):
    lines = read(
        "git", "log", "--no-merges", "--since-as-filter=2026-11-20T06:15:30Z",
        "--format=%H%x09%aN%x09%aE%x09%cI", ref,
    ).splitlines()
    counted = Counter()
    seen = set()
    for line in lines:
        sha, _, email, date = line.split("\t")
        if sha in seen or not in_window(date):
            continue
        seen.add(sha)
        key = email.casefold()
        if key not in identities:
            identities[key] = read(
                "gh", "api", f"repos/{{owner}}/{{repo}}/commits/{sha}",
                "--jq", ".author.login // \"\"",
            ).strip()
        counted[identities[key]] += 1
    return counted

main_commits = count_commits("origin/main")
all_commits = count_commits("--remotes=origin")
pulls = json.loads(read(
    "gh", "pr", "list", "--state", "all", "--search", "updated:>=2026-11-20",
    "--limit", "300", "--json", "number,author,baseRefName,mergedAt,reviews",
))
if len(pulls) == 300 or any(len(pr["reviews"]) >= 100 for pr in pulls):
    raise SystemExit("Uzupełnij strony wyników przed rozliczeniem.")

main_merges, dependent_merges, reviews = Counter(), Counter(), Counter()
for pr in pulls:
    author = (pr.get("author") or {}).get("login")
    if in_window(pr.get("mergedAt")):
        target = main_merges if pr["baseRefName"] == "main" else dependent_merges
        target[author] += 1
    for review in pr["reviews"]:
        reviewer = (review.get("author") or {}).get("login")
        if reviewer != author and review["state"] != "PENDING" and in_window(review.get("submittedAt")):
            reviews[reviewer] += 1

print(cutoff.isoformat())
for login in team:
    print(login, main_commits[login], all_commits[login], main_merges[login],
          dependent_merges[login], reviews[login], sep="\t")
PYTHON
```
