# ADR SCRUM-94 — granica organizacji w obecnej aplikacji

Data: 06.11.2026. Status: **propozycja ograniczenia technicznego do review**.
Koordynator: Jakub Czaja. Powiązany [inwentarz danych](../privacy/SCRUM-94-data-inventory.md).

## Kontekst

W `main` (`4ce144e`) istnieje jedno konto WEBFLEET w konfiguracji instancji.
`context()` API wybiera flotę na podstawie konfiguracji serwera, a `User`
nie ma identyfikatora organizacji ani powiązania z jej zakresem danych.
`source_account` porządkuje dane źródła, lecz nie jest uprawnieniem użytkownika
do tenantów. `Driver` również nie ma granicy organizacji. To nie jest
zweryfikowana implementacja izolacji kilku klientów.

## Proponowane ograniczenie

Obecny model rozpatrywać wyłącznie jako instancję jednej organizacji.
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
Akceptacja administratora i review techniczne pozostają otwarte.
