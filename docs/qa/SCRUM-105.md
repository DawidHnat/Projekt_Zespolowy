# SCRUM-105 — planowane funkcje i lokalne dane

Serwis, Ewidencja przebiegu, Kierowcy, Karty paliwowe i Alerty mają napis
„Planowane” w nawigacji oraz na stronie. Rejestr `navigation.ts` wyznacza
oba oznaczenia przez `placeholder`. Usunięcie go wraz z podłączeniem
zaimplementowanego widoku usuwa oznaczenie. Działające widoki nie mają etykiety.
Identyfikatory stron, widgetów i klucze preferencji pozostają takie same.

Ustawienia i galeria pojazdów informują o zapisie na danym urządzeniu i w danej
przeglądarce. Dialog zdjęcia pojazdu oraz własne tło opisują brak wysyłki
na serwer i utratę lokalnego pliku po wyczyszczeniu danych przeglądarki.
Zdjęcia i rozmiary pojazdów mają przestrzeń konta; wygląd dashboardu i tło
pozostają preferencjami przeglądarki. Synchronizacja jest zakresem SCRUM-91.
Błąd trwałego zapisu nadal jawnie przełącza informację na bieżącą sesję.

## Sprawdzenie

`npm test`, `npm run build`, `npm run test:e2e` w `frontend/`, z izolowaną
bazą i ustawieniami opisanymi w SCRUM-83. E2E przechodzi wszystkie pięć
planowanych stron przez nawigację klawiaturą, sprawdza lokalne komunikaty
w ustawieniach, własnym tle i dialogu zdjęcia, Escape oraz powrót fokusu.
Axe WCAG A/AA bada te ekrany w jasnym i ciemnym motywie, na desktopie
oraz przy 390 px. Kontrola szerokości wykrywa poziome przewijanie stron.
Zrzuty `local-settings-*.png` i `local-photo-*.png` zapisują się w wynikach testów.

Niezależny QA: potwierdzić czytelność etykiet w menu telefonu, wejście i powrót
klawiaturą, zachowanie zapisanych wcześniej układów, poprawny komunikat
przy zablokowanym IndexedDB/localStorage. Sprawdzić także Safari. Wynik
implementacyjny E2E nie jest podpisem niezależnego QA ani zatwierdzeniem PR.
