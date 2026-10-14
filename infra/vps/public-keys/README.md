# Publiczne klucze SSH

Plik `<login-ssh>.pub` zawiera własny klucz publiczny danej osoby w formacie
OpenSSH. Wszystkie cztery klucze są dostępne i zostały zainstalowane na VPS
`57.129.179.53`. Trzy brakujące klucze przekazano i dodano 14 października 2026.
Kluczy prywatnych, haseł i `.env` tutaj nie zapisujemy.

| Osoba | Plik / login SSH | Odcisk ED25519 |
| --- | --- | --- |
| Jakub Czaja | `jczaja51.pub` / `jczaja51` | `SHA256:yFsoSo10hJcY0MHVYWaY7RjOabcGfz/gy56b1rYvkxg` |
| Dawid Hnat | `dawidhnat.pub` / `dawidhnat` | `SHA256:uy9vcswcpEfQ6+x1XvvKxK66FPmlCDbKJ8IXPEcJOUU` |
| Jakub Nazarewicz | `jnazarewiczs.pub` / `jnazarewiczs` | `SHA256:7IlQa0xVHwJelKOzZEq5b/PvoauQkI2hvN2a7p37iyc` |
| Marcel Głowacki | `mglowacki0.pub` / `mglowacki0` | `SHA256:ZbOT7DV0GN+UJLDORo9m9Hlwhq32+6BtfXSOua7IKKc` |

Login SSH Dawida zapisujemy małymi literami (`dawidhnat`); jego login GitHub
to `DawidHnat`.

Weryfikacja formatu: `ssh-keygen -lf NAZWA.pub`. Klucze mają być potwierdzone
przez właścicieli przed instalacją na serwerze. Sama obecność pliku nie dowodzi
poprawnego logowania; każdy członek wykonuje własny test BatchMode.
