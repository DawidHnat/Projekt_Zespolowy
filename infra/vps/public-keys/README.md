# Publiczne klucze SSH

Plik `<login-ssh>.pub` zawiera własny klucz publiczny danej osoby w formacie
OpenSSH. Obecnie przygotowano tylko klucz `jczaja51`; pozostałe osoby dostarczą
swoje klucze. Kluczy prywatnych, haseł i `.env` tutaj nie zapisujemy.

Weryfikacja formatu: `ssh-keygen -lf NAZWA.pub`. Klucze mają być potwierdzone
przez właścicieli przed instalacją na serwerze. Sama obecność pliku nie dowodzi
poprawnego logowania; każdy członek wykonuje własny test BatchMode.
