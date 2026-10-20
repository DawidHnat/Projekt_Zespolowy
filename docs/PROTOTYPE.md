# Prototyp Sprintu 1

Źródło: [Fleet-Flow — Sprint 1 / klikalny prototyp MVP](https://www.figma.com/design/4EFjRAUbCoTjemZpQRVDu9).
Strona: **Sprint 1 — klikalny prototyp**. Prototyp powstał 20 października 2026.

W trybie prezentacji wybierz przepływ z lewego panelu. Przyciski i znaczniki
przełączają połączone ekrany. Dane logowania, pojazdy, pomiary, godziny
i mapa są przykładowe; prototyp nie łączy się z API ani bazą danych.
Pola pokazują przygotowane stany, bez wpisywania prawdziwego hasła.

## Powiązanie z historyjkami

| Story | Nazwany przepływ | Początek w prezentacji | Ekran w edytorze |
| --- | --- | --- | --- |
| [SCRUM-16](https://fleet-flow.atlassian.net/browse/SCRUM-16) | S1 / Logowanie → Pulpit → Wylogowanie | [Logowanie](https://www.figma.com/proto/4EFjRAUbCoTjemZpQRVDu9?node-id=2-46&starting-point-node-id=2%3A46) | [01 Logowanie](https://www.figma.com/design/4EFjRAUbCoTjemZpQRVDu9?node-id=2-46) |
| [SCRUM-5](https://fleet-flow.atlassian.net/browse/SCRUM-5) | S1 / Lista i mapa floty | [Lista i mapa](https://www.figma.com/proto/4EFjRAUbCoTjemZpQRVDu9?node-id=2-49&starting-point-node-id=2%3A49) | [04 Lista pojazdów](https://www.figma.com/design/4EFjRAUbCoTjemZpQRVDu9?node-id=2-49) |
| [SCRUM-15](https://fleet-flow.atlassian.net/browse/SCRUM-15) | S1 / Aktualność danych → Awaria źródła → Odzyskane połączenie | [Aktualność danych](https://www.figma.com/proto/4EFjRAUbCoTjemZpQRVDu9?node-id=2-53&starting-point-node-id=2%3A53) | [08 Nieaktualne dane](https://www.figma.com/design/4EFjRAUbCoTjemZpQRVDu9?node-id=2-53) |

W opisach Story należy zachować te same nazwy przepływów i odnośniki.
Sam prototyp nie potwierdza odbioru implementacji ani kryteriów technicznych
API, uprawnień, sesji czy synchronizacji.

## Scenariusze przeglądu

1. **Logowanie:** na ekranie 01 kliknij „Zaloguj się”, obejrzyj Pulpit,
   następnie kliknij „Wyloguj”. Wariant „Błąd logowania” pokazuje komunikat
   i powrót przez „Popraw dane”.
2. **Lista i mapa:** na ekranie 04 kliknij wyszukiwanie, aby zobaczyć
   przygotowany wynik FF001; „Pokaż mapę” zachowuje ten wynik. Wyczyść
   wyszukiwanie, wybierz FF001 albo FF002 ze znacznika lub listy i wróć do mapy.
   „Wszystkie statusy” pokazuje przygotowany filtr „W ruchu”; jego mapa
   zachowuje ten sam jeden pojazd. Wyczyść filtr, aby wrócić do całej floty.
   FF003 pozostaje na liście z jawnym brakiem GPS i pomiarów.
3. **Aktualność:** na ekranie 08 sprawdź ostatni poprawny odczyt 09:10
   i ostrzeżenie. Kliknij „Odśwież dane”: ekran synchronizacji po 0,8 s
   przechodzi do odczytu 09:41. Kliknięcie ostrzeżenia pokazuje wariant
   niedostępnego źródła; „Spróbuj ponownie” prowadzi przez synchronizację
   do odzyskanego połączenia.
4. Z listy przepływów uruchom warianty „Pusta flota”, „Awaria bez danych”
   oraz „Brak GPS”.

## Ekrany

| Nr | Ekran | Identyfikator Figmy |
| --- | --- | --- |
| 01 | Logowanie | `2:46` |
| 02 | Błąd logowania | `2:47` |
| 03 | Pulpit / dane aktualne | `2:48` |
| 04 | Lista pojazdów | `2:49` |
| 05 | Wynik wyszukiwania | `2:50` |
| 06 | Mapa floty | `2:51` |
| 07 | Wybrany pojazd / FF001 | `2:52` |
| 08 | Nieaktualne dane | `2:53` |
| 09 | Synchronizacja | `2:54` |
| 10 | Po odświeżeniu | `2:55` |
| 11 | Pusta flota | `2:56` |
| 12 | Awaria bez danych | `2:57` |
| 13 | Pojazd bez GPS | `2:58` |
| 14 | Wybrany pojazd / FF002 | `4:206` |
| 15 | Filtr statusu / W ruchu | `9:227` |
| 16 | Mapa / wynik wyszukiwania | `9:284` |
| 17 | Mapa / filtr W ruchu | `9:357` |
| 18 | Awaria / ostatni poprawny odczyt | `9:433` |

## Wygląd i dostęp

Plik zawiera edytowalne warstwy, Inter, wspólne zmienne kolorów,
komponenty przycisków, pól, statusów i znak z repozytorium.
Wygląd odpowiada jasnemu motywowi opisanemu w [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md).
Mapa jest ilustracją wektorową, a nie obrazem z danymi klienta.

Właścicielem pliku jest konto `j.czaja.568` użyte do połączenia Figmy.
Udostępnienie prowadzącemu zostało odłożone do otrzymania jego adresu
e-mail. Przed oddaniem właściciel powinien nadać mu **Can view**
i sprawdzić dostęp z jego konta. Weryfikacja Figma Education jest osobnym
procesem i nie zastępuje udostępnienia pliku.
