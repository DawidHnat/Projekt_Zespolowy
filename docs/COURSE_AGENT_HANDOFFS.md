# Oddania 3.2/4.2 — aktualne przekazanie 19.11.2026

Zebrał agent na polecenie **Jakuba Czai (jczaja51)**. Kod bazowy cb634da,
CI/deploy/smoke 44386951054 i publiczny SHA/readiness PASS.
[Macierz i pełne dowody](COURSE_READINESS.md), [AC/12 DoD](qa/SCRUM-141-current.md).

| Osoba | Wykonane / nie ponawiać jako brakujące | Konkretny następny krok |
| --- | --- | --- |
| Jakub Czaja | #101 odświeżony a8476ac, skanery/CI PASS; #120 testy 46, #121 arkusz prywatności, #122 macierz integracji; potwierdzenia PO zapisane | Ustalić administratora/konsultującego 113, zapewnić dostęp QA, zebrać kompletne 3.2 przed przełączeniem; po warunkach rozliczenia S2 uruchomić istniejący S3, finalne 4.2 |
| Dawid Hnat | Ochrona 3 checków, niezależny review auth i ocena restore 16/91 są PASS w 10324/10345; nie uruchamiać 84 jako nowej blokady | Aktualny review całego #101, odbiór obrazu/rolloutu; po bramkach merge/deploy/smoke; następnie #110 i jego migracja 0010/rollback. Kontrolowany live 64 na własnych AC i kopiach 18, nie pełny 84/S5 |
| Jakub Nazarewicz | #99 z poprawkami 144/145/146 dostarczony; autorstwo zachowane; testy i niezależne reviews są dowodem | Review #120/46 na aktualnym head, przekazanie 91 do końcowego QA; po #101 aktualny review #110 odpowiednio do zakresu. Plan/dostępność 129 potwierdzone przez PO, S3 nadal future |
| Marcel Głowacki | FF-QA-031 expiry 2/2 i Offline z zachowaniem szkicu są PASS w swoim zakresie; nie kopiować historycznych liczników na nowe SHA | Uzupełnić dokładnie brakujące AC/DoD 16/91, cookie/odwołanie API, dwa konta/migrację i backend po Offline. 23/40 korzystają ze wspólnych scenariuszy 46; QA alertów/kierowców 33/54 po dostarczeniu #110 |

Jedna firma i jedno API to zakres projektu; dwa konta syntetyczne są testem
izolacji użytkowników, nie wielofirmowości. [Safari poza obowiązkowym zakresem](qa/browser-scope-20261119.md)
decyzją PO; nie udajemy PASS niewykonanej próby. Autor zmian nie jest ich
niezależnym QA. Testów żywego SMTP/WEBFLEET nie uruchamia się przez ten pakiet.

Każdy wynik zawiera wykonawcę (agent/człowiek), datę, SHA, środowisko, dowód
i PASS/FAIL/BLOCKED. Prośba o dostępność reviewera #119/150 została odrzucona
przez PO; nie ponawiać i nie dodawać 150 do warunków S2. Backup #35/#105 i
pełny recovery pozostają DEFERRED do 84/S5. Żadnego automerge ani bypassu.
