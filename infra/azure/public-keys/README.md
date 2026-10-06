# Publiczne klucze zespołu

W tym katalogu zapisujemy wyłącznie klucze **publiczne**, po potwierdzeniu
właściciela. Klucz prywatny zostaje na komputerze osoby, która go wygenerowała.

| Osoba | GitHub | Plik publicznego klucza |
| --- | --- | --- |
| Jakub Czaja | jczaja51 | jczaja51.pub |
| Dawid Hnat | DawidHnat | dawidhnat.pub |
| Jakub Nazarewicz | jnazarewiczs | jnazarewiczs.pub |
| Marcel Głowacki | mglowacki0 | mglowacki0.pub |

Brak pliku oznacza konto bez możliwości logowania, aż do dodania klucza.
Login Linux Dawida jest zapisany małymi literami: `dawidhnat`.

Każda osoba generuje klucz na swoim komputerze:

```bash
ssh-keygen -t ed25519 -a 64 -f ~/.ssh/fleet_flow_ed25519 -C "LOGIN_GITHUB@fleet-flow"
cat ~/.ssh/fleet_flow_ed25519.pub
```

W Windows PowerShell można użyć `$HOME/.ssh/fleet_flow_ed25519` i `Get-Content`
zamiast `cat`. Należy ustawić własną frazę zabezpieczającą klucz. Przekazujemy
administratorowi zawartość `.pub` oraz odcisk z
`ssh-keygen -lf ~/.ssh/fleet_flow_ed25519.pub`. Nie przekazujemy pliku bez `.pub`.

Administrator dodaje klucz przez `../add-ssh-key.py`, a jego właściciel sam
wykonuje test `ssh -o BatchMode=yes ... hostname; echo $?`.
