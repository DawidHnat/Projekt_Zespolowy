# ADR SCRUM-94 — granica organizacji w obecnej aplikacji

Data: 06.11.2026; aktualizacja 10.11.2026.
Status: **zakres jednej firmy potwierdzony przez PO; odbiór polityki firmy otwarty**.
Koordynator: Jakub Czaja. Powiązany
[inwentarz SCRUM-112](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cffaaebce81cf3955fe7d98879fe521da8a61031/docs/privacy/SCRUM-112-inventory.md)
z [PR #52](https://github.com/DawidHnat/Projekt_Zespolowy/pull/52).
ADR stanowi materiał do decyzji P07 tego inwentarza. Wskazanie administratora
oraz zatwierdzenia P01/P07 pozostają w SCRUM-113.

Przegląd techniczny 10.11.2026: opis granicy nadal odpowiada `main` 5b5fceb.
PO potwierdził obecny projekt bez rzeczywistych danych floty i docelową
obsługę jednej firmy. To decyzja zakresu produktu, bez wskazania przyszłego
administratora, okresów retencji i dopuszczenia jego rzeczywistych danych.
[Korekta wersji inwentarza, ryzyka i pakiet do zatwierdzeń](../privacy/SCRUM-94-acceptance.md)
rozróżnia to ustalenie od akceptacji polityki. Decyzje administratora P01/P07
pozostają otwarte.

## Kontekst

W `main` (`4ce144e`) istnieje jedno konto WEBFLEET w konfiguracji instancji.
`context()` API wybiera flotę na podstawie konfiguracji serwera, a `User`
nie ma identyfikatora organizacji ani powiązania z jej zakresem danych.
`source_account` porządkuje dane źródła, lecz nie jest uprawnieniem użytkownika
do tenantów. `Driver` również nie ma granicy organizacji. To nie jest
zweryfikowana implementacja izolacji kilku klientów.

## Zakres jednej organizacji

Zgodnie z ustaleniem PO z 10.11 obecny model rozpatrujemy wyłącznie jako
instancję jednej organizacji.
Nie przyjmować drugiej firmy przez samo dodanie kont użytkowników lub zmianę
`source_account`. Do czasu wskazania administratora zakres rzeczywistych danych
pozostaje niezatwierdzony; demonstracja na danych syntetycznych jest osobnym
zakresem od dopuszczenia danych firmy.

Rozszerzenie na wiele organizacji wymaga osobnej decyzji i implementacji:

1. Granice organizacji dla kont, kierowców, pojazdów, przypisań, historii,
   alertów, plików i śladu audytowego; wymuszenie zakresu przy każdym odczycie
   i zapisie, niezależnie od identyfikatora podanego przez klienta.
2. Zasady administracji i migracji, konfiguracje źródeł i oddzielne uprawnienia
   oraz ocenę wspólnej bazy lub oddzielnych instancji.
3. Eksport, usuwanie, backup i restore respektujące granice organizacji.
4. Negatywne testy odczytu, zapisu i odwołań do obiektów innej organizacji
   oraz niezależny odbiór bezpieczeństwa przed udostępnieniem.

## Konsekwencje i zatwierdzenia

ADR nie zmienia kodu, dostępu ani konfiguracji produkcji. Nie poświadcza
legalnego zakresu przetwarzania i nie jest decyzją niewskazanego administratora.
Właściciel decyzji o organizacji i danych: **niewskazany / BLOCKED**;
koordynator ustalenia: Jakub Czaja; termin kalendarzowy: nieustalony.
Zakres produktu zaakceptował Jakub Czaja / PO 10.11.2026 w rozmowie.
Akceptacja administratora i review techniczne aktualizacji pozostają otwarte.
