# Prototyp Sprintu 1

Źródło: [Fleet-Flow — Sprint 1 / klikalny prototyp MVP](https://www.figma.com/design/4EFjRAUbCoTjemZpQRVDu9).
Strona: **Sprint 1 — klikalny prototyp**. Prototyp powstał 20 października 2026.
21 października dopasowano go do wybranego przez PO szklanego widoku aplikacji
z tapetą miasta. Aktywna strona ma 25 ekranów; wcześniejsze 18 zachowano
wraz z przepływami na stronie **Archiwum - prototyp przed dopasowaniem 21.10.2026**.

W trybie prezentacji wybierz przepływ z lewego panelu. Przyciski i znaczniki
przełączają połączone ekrany. Dane logowania, pojazdy, pomiary, godziny
i mapa są przykładowe; prototyp nie łączy się z API ani bazą danych.
Pola pokazują przygotowane stany, bez wpisywania prawdziwego hasła.

21.10.2026 po zmianie wyglądu sprawdzono rzeczywiste kliknięcia w prezentacji:
logowanie i wylogowanie, kafelki → wyszukiwanie → mapa → pełna flota,
wybór FF002 oraz nieaktualność → awaria → ponowienie → synchronizacja
→ odczyt 09:41. Wyszukiwanie i filtr „W ruchu” pozostają zachowane również
przy przełączaniu Pojazdy/Mapa boczną nawigacją. Sprawdzono wejście do Ustawień,
wejście i anulowanie edycji układu oraz przewijanie Pulpitu do dolnych modułów.
Kontrola struktury wykazała osiem początków przepływów, 318 elementów
z interakcjami i brak odnośników do nieistniejących ekranów.

## Powiązanie z historyjkami

| Story | Nazwany przepływ | Początek w prezentacji | Ekran w edytorze |
| --- | --- | --- | --- |
| [SCRUM-16](https://fleet-flow.atlassian.net/browse/SCRUM-16) | S1 / Logowanie → Pulpit → Wylogowanie | [Logowanie](https://www.figma.com/proto/4EFjRAUbCoTjemZpQRVDu9?node-id=2-46&starting-point-node-id=2%3A46&scaling=scale-down) | [01 Logowanie](https://www.figma.com/design/4EFjRAUbCoTjemZpQRVDu9?node-id=2-46) |
| [SCRUM-5](https://fleet-flow.atlassian.net/browse/SCRUM-5) | S1 / Lista i mapa floty | [Lista i mapa](https://www.figma.com/proto/4EFjRAUbCoTjemZpQRVDu9?node-id=2-49&starting-point-node-id=2%3A49&scaling=scale-down) | [04 Pojazdy / kafelki](https://www.figma.com/design/4EFjRAUbCoTjemZpQRVDu9?node-id=2-49) |
| [SCRUM-15](https://fleet-flow.atlassian.net/browse/SCRUM-15) | S1 / Aktualność danych → Awaria źródła → Odzyskane połączenie | [Aktualność danych](https://www.figma.com/proto/4EFjRAUbCoTjemZpQRVDu9?node-id=2-53&starting-point-node-id=2%3A53&scaling=scale-down) | [08 Nieaktualne dane](https://www.figma.com/design/4EFjRAUbCoTjemZpQRVDu9?node-id=2-53) |

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
5. **Spójność ze szkieletem:** na Pulpicie przewiń do modułów Pojazdy,
   Wykorzystanie floty i Ostatnie przejazdy. Otwórz „Edytuj układ” i wróć
   przez „Anuluj” albo „Zapisz układ”. To podgląd trybu edycji, bez symulacji
   przeciągania i trwałego zapisu preferencji. „Ustawienia” pokazują wybrany
   wygląd; zmiana motywów i wgrywanie zdjęć pozostają funkcją aplikacji.
   Pozostałe pozycje nawigacji prowadzą do jawnych ekranów „w przygotowaniu”.

## Ekrany

| Nr | Ekran | Identyfikator Figmy |
| --- | --- | --- |
| 01 | Logowanie | `2:46` |
| 02 | Błąd logowania | `2:47` |
| 03 | Pulpit / dane aktualne | `2:48` |
| 04 | Pojazdy / kafelki | `2:49` |
| 05 | Kafelki / wynik wyszukiwania | `2:50` |
| 06 | Mapa floty | `2:51` |
| 07 | Wybrany pojazd / FF001 | `2:52` |
| 08 | Nieaktualne dane | `2:53` |
| 09 | Synchronizacja | `2:54` |
| 10 | Po odświeżeniu | `2:55` |
| 11 | Pusta flota | `2:56` |
| 12 | Awaria bez danych | `2:57` |
| 13 | Pojazd bez GPS | `2:58` |
| 14 | Wybrany pojazd / FF002 | `4:206` |
| 15 | Kafelki / filtr W ruchu | `9:227` |
| 16 | Mapa / wynik wyszukiwania | `9:284` |
| 17 | Mapa / filtr W ruchu | `9:357` |
| 18 | Awaria / ostatni poprawny odczyt | `9:433` |
| 19 | Ustawienia / Wygląd | `22:316` |
| 20 | Pulpit / Edycja układu | `22:339` |
| 21 | Serwis / W przygotowaniu | `22:403` |
| 22 | Ewidencja przebiegu / W przygotowaniu | `22:426` |
| 23 | Kierowcy / W przygotowaniu | `22:449` |
| 24 | Karty paliwowe / W przygotowaniu | `22:472` |
| 25 | Alerty / W przygotowaniu | `22:495` |

## Wygląd i dostęp

Plik zawiera edytowalne warstwy, Inter, wspólne zmienne kolorów oraz
komponenty przycisków, pól, statusów, nawigacji, metryk i pustych stanów.
Wygląd opiera się na [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md), `tokens.css`,
`glass.css`, rejestrze modułów i nawigacji aplikacji: jasny motyw, szklane
powierzchnie, zaokrąglenie kart 18 px oraz tapeta `backgrounds/city.jpg`.
Znak i wektorowe ikony pochodzą z projektu. Jedyną bitmapą ekranów jest
tapeta; interfejs pozostaje edytowalny. Mapa jest ilustracją wektorową,
a nie obrazem z danymi klienta.

Zakres prototypu obejmuje trzy Story Sprintu 1. Obecność przyszłych modułów
w nawigacji nie oznacza, że prototyp implementuje całe MVP. Analityka, alerty
i historia mają jawne puste stany zamiast zmyślonych wyników. Podgląd ustawień
i układu nie symuluje wszystkich preferencji dostępnych w lokalnej aplikacji.

Właścicielem pliku jest konto `j.czaja.568` użyte do połączenia Figmy.
Udostępnienie prowadzącemu zostało odłożone do otrzymania jego adresu
e-mail. Przed oddaniem właściciel powinien nadać mu **Can view**
i sprawdzić dostęp z jego konta. Weryfikacja Figma Education jest osobnym
procesem i nie zastępuje udostępnienia pliku.
