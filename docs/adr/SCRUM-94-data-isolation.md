# ADR SCRUM-94 — granica organizacji w obecnej aplikacji

Data: 06.11.2026; aktualizacja 19.11.2026 po odpowiedziach PO.
Status: **zakres jednej firmy potwierdzony przez PO; odbiór polityki firmy otwarty**.
Koordynator: Jakub Czaja. Powiązany
[inwentarz SCRUM-112](https://github.com/DawidHnat/Projekt_Zespolowy/blob/cffaaebce81cf3955fe7d98879fe521da8a61031/docs/privacy/SCRUM-112-inventory.md)
z [PR #52](https://github.com/DawidHnat/Projekt_Zespolowy/pull/52).
ADR stanowi materiał do decyzji P07 tego inwentarza. Właściciel został wskazany
w lokalnym rejestrze 19.11; pozostałe warunki P01/P07 są w SCRUM-113.

**Historyczny zapis 10.11, skorygowany poniżej 19.11:** opis granicy odpowiadał `main` 5b5fceb.
PO potwierdził obecny projekt bez rzeczywistych danych floty i docelową
obsługę jednej firmy. To decyzja zakresu produktu, bez wskazania przyszłego
administratora, okresów retencji i dopuszczenia jego rzeczywistych danych.
[Korekta wersji inwentarza, ryzyka i pakiet do zatwierdzeń](../privacy/SCRUM-94-acceptance.md)
rozróżnia to ustalenie od akceptacji polityki. Decyzje administratora P01/P07
pozostają otwarte.

## Potwierdzenie zakresu — 19.11.2026

PO Jakub Czaja potwierdził rzeczywiste dane jednej firmy i jedno API WEBFLEET, wyłącznie do projektu; bez rozbudowy dla innych firm. Podmiot i właściciel zostali wskazani w lokalnym rejestrze poza Git/Jira. Według relacji PO ustna zgoda z 2 października obejmuje dostęp całej czwórki i pokaz prowadzącemu. Użyczenie do końca lutego 2027 r.; potem koniec projektu i plan usunięcia jego danych. Publiczne udostępnianie nieustalone, konsultacji DPO/prawnej nie było. Koryguje to wcześniejsze założenie wyłącznie syntetycznej demonstracji; nie jest odczytem rekordów VPS ani pełnym zatwierdzeniem P01–P18. Aktualny model `cb634da` nadal nie ma granicy tenantów. Dwa konta QA sprawdzają użytkowników tej samej firmy. [Aktualny arkusz](../privacy/SCRUM-113-decision-sheet.md).

## Kontekst historyczny

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
`source_account`. Wskazanie właściciela i zgłoszony zakres użycia są już
zapisane w ograniczonym rejestrze; pozostałe procedury i wymagany screening
pozostają otwarte. Izolowane testy agenta korzystają z danych syntetycznych.

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
pełnego zatwierdzenia przetwarzania ani wyniku screeningu.
Właściciel użyczającej firmy: **wskazany lokalnie według relacji Jakuba**;
pełne kryteria P01–P18 nadal otwarte;
koordynator ustalenia: Jakub Czaja; termin kalendarzowy: nieustalony.
Zakres produktu zaakceptował Jakub Czaja / PO 10.11.2026 w rozmowie.
Akceptacja administratora i review techniczne aktualizacji pozostają otwarte.
