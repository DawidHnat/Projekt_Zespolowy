# Wkład zespołu w Sprint 3

Roboczy odczyt przed zjazdem. Raport końcowy przeliczamy na zjeździe **28.11.2026** po pobraniu aktualnych gałęzi repozytorium zespołu.

| Granica okna | Europe/Warsaw | UTC |
| --- | --- | --- |
| Start | 20.11.2026 07:15:30.480 CET | `2026-11-20T06:15:30.480Z` |
| Planowany koniec | 27.11.2026 23:59:59.999 CET | `2026-11-27T22:59:59.999Z` |

[Źródło terminów w Jirze](https://fleet-flow.atlassian.net/jira/software/projects/SCRUM/boards/1).
Wiersze poniżej odpowiadają odczytowi z **23.11.2026 21:17:52 CET**.

| Osoba | Login GitHub | Commity bez merge | Scalone PR-y | Przeglądy cudzych PR-ów |
| --- | --- | ---: | ---: | ---: |
| Jakub Czaja | `jczaja51` | 36 | 9 | 11 |
| Dawid Hnat | `DawidHnat` | 0 | 0 | 14 |
| Jakub Nazarewicz | `jnazarewiczs` | 0 | 0 | 0 |
| Marcel Głowacki | `mglowacki0` | 0 | 0 | 4 |

Commity liczymy raz według SHA, z opublikowanych gałęzi `origin`, według
czasu commitu. PR-y liczymy według czasu scalenia, także do gałęzi zależnych.
Każdy wysłany formalny review liczy się w oknie według `submitted_at`, jeśli
recenzent jest inną osobą niż autor PR-u. Wynik obejmuje wszystkie stany PR
i formalne review, w tym `COMMENTED` oraz review później wycofane. Pomija
oczekujące szkice review, konta spoza zespołu i boty.

## Powtórzenie pomiaru w klonie zespołu

```bash
git fetch --prune origin
gh pr list --state merged --search "merged:2026-11-20..2026-11-27" \
  --limit 100 --json number,author,headRefName
```

Ten blok wylicza trzy kolumny dla każdej osoby. Jego pierwsza linia wyniku
podaje czas odczytu albo koniec sprintu, jeśli pomiar odbywa się po zamknięciu
okna.

```bash
python3 - <<'PYTHON'
import json
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

start = datetime.fromisoformat("2026-11-20T06:15:30.480+00:00")
end = datetime.fromisoformat("2026-11-27T22:59:59.999+00:00")
cutoff = min(datetime.now(timezone.utc), end)
team = {
    "jczaja51": ("Jakub Czaja", "jczaja51"),
    "DawidHnat": ("Dawid Hnat", "DawidHnat"),
    "jnazarewiczs": ("Jakub Nazarewicz", "jnazarewiczs"),
    "mglowacki0": ("Marcel Głowacki", "mglowacki0"),
}

def read(*args):
    return subprocess.check_output(args, text=True)

def in_window(value):
    return bool(value) and start <= datetime.fromisoformat(value) <= cutoff

shortlog = read("git", "shortlog", "-sn", "--no-merges",
                "--since-as-filter=2026-11-20T06:15:31Z",
                f"--until={cutoff.isoformat(timespec='seconds')}", "--remotes=origin")
commits = {name: int(count) for count, name in (line.strip().split("\t", 1)
           for line in shortlog.splitlines())}
merged = json.loads(read("gh", "pr", "list", "--state", "merged",
                         "--search", "merged:2026-11-20..2026-11-27", "--limit", "100",
                         "--json", "number,author,headRefName,mergedAt"))
pulls = json.loads(read("gh", "pr", "list", "--state", "all", "--limit", "1000",
                        "--json", "number,author"))
if len(merged) == 100 or len(pulls) == 1000:
    raise SystemExit("Limit listy PR wymaga rozszerzenia zapytania.")

def reviews(pr):
    pages = json.loads(read("gh", "api",
                            f"repos/{{owner}}/{{repo}}/pulls/{pr['number']}/reviews",
                            "--paginate", "--slurp"))
    author = (pr.get("author") or {}).get("login")
    return Counter((review.get("user") or {}).get("login")
                   for page in pages for review in page
                   if in_window(review.get("submitted_at"))
                   and review.get("state") != "PENDING"
                   and (review.get("user") or {}).get("login") != author)

with ThreadPoolExecutor(max_workers=5) as pool:
    reviewed = sum(pool.map(reviews, pulls), Counter())
merged_count = Counter((pr.get("author") or {}).get("login") for pr in merged
                       if in_window(pr.get("mergedAt")))
print(cutoff.isoformat())
for login, names in team.items():
    print(login, sum(commits.get(name, 0) for name in names),
          merged_count[login], reviewed[login], sep="\t")
PYTHON
```
