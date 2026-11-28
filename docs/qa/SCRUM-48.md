# SCRUM-48 — konta, aktywacja i uprawnienia

## Macierz techniczna

PO zatwierdził 21.11.2026 poniższe mapowanie w zakresie obecnych funkcji.
Panel i API administracyjne są dostępne Administratorowi. Pozostałe operacje
korzystają z dotychczasowych reguł jednej organizacji opisanej w
[ADR SCRUM-94](../adr/SCRUM-94-data-isolation.md).

| Operacja | Administrator `admin` | Kierownik floty `editor` | Użytkownik `viewer` |
| --- | --- | --- | --- |
| Odczyt listy, mapy GeoJSON, szczegółów GPS i zapisanych przejazdów skonfigurowanej floty | Tak | Tak | Tak |
| Odczyt kartoteki i historii przypisań kierowców skonfigurowanej floty | Tak | Tak | Tak |
| Edycja kartoteki pojazdu, kierowców i przypisań, adnotacji przejazdów oraz reguł alertów | Tak | Tak | Niedostępna |
| Odczyt alertów i własny stan przeczytania | Tak | Tak | Tak |
| Ręczne żądanie odczytu źródła w ramach wspólnego limitu | Tak | Tak | Tak |
| Własny profil, hasło, sesje i preferencje | Tak | Tak | Tak |
| Lista kont, tworzenie, edycja ról i statusów oraz zaproszenia | Tak | Niedostępne | Niedostępne |

Uprawnienia do szczegółowych danych GPS, historii, eksportu, dokumentów i
audytu w przyszłej polityce firmy pozostają zakresem
[SCRUM-113](https://fleet-flow.atlassian.net/browse/SCRUM-113). Odbiór z
rzeczywistymi danymi i e-mailem wymaga uzgodnień z tego zadania oraz
zatwierdzonego odbiorcy testowego. Konto aplikacji to osobny rekord od kierowcy.

## Obsługa kont

1. Wejdź w **Użytkownicy** jako Administrator. **Dodaj konto** zapisuje imię,
   nazwisko, adres, unikalny login i rolę. Konto zaczyna jako oczekujące.
2. Użyj **Wyślij zaproszenie** w oknie konta. Serwer generuje losowy link
   ważny 24 godziny i zapisuje tylko hash tokenu. Link zawiera token w
   fragmencie URL. Odbiorca sam ustawia pierwsze hasło o długości 12–1024
   znaków. Link można wykorzystać raz.
3. Statusy oczekujące, nieaktywne i zablokowane odmawiają sesji. Konto
   oczekujące przechodzi do aktywnego po ustawieniu hasła. Użycie starego
   linku po zmianie adresu, roli lub statusu kończy się odmową.
4. Zmiany roli, statusu, loginu lub e-maila odwołują sesje konta. Serwer
   odrzuca blokadę, dezaktywację i zmianę roli ostatniego aktywnego
   administratora, również przy równoległych zmianach.

Logowanie akceptuje login lub e-mail bez rozróżniania wielkości liter.
Adres z uwzględnieniem oryginalnych znaków służy do wysyłki, a zapisany
identyfikator logowania stosuje tę samą normalizację Unicode co login.
Próby dla obu identyfikatorów trafiają do jednego limitu konta (10/min);
obowiązuje też wspólny limit 10/min na IP. Wieloznaczny adres z danych
historycznych daje neutralną odmowę, a wcześniejszy login nadal działa.
Limity zaproszeń wynoszą 3/min na konto i 10/min na administratora.
Po nieudanej ponownej wysyłce wcześniejszy ważny link dalej działa.

## Kontrakt API

| Metoda i ścieżka (prefiks `/api/v1`) | Zastosowanie |
| --- | --- |
| `GET /admin/users` | Paginowana lista kont. Filtry strony to `page` i `page_size`. |
| `POST /admin/users` | Tworzy konto z polami `first_name`, `last_name`, `username`, `email`, `role`. |
| `PATCH /admin/users/{uuid}` | Zmienia wskazane pola i status. Wymaga bieżącego `version`. |
| `POST /admin/users/{uuid}/activation` | Wysyła zaproszenie na zapisany adres wraz z kontrolą `version`. |
| `POST /auth/activation/confirm` | Przyjmuje `token` i nowe `password`. Link sam autoryzuje operację. |

Zapisy i potwierdzenie wymagają dozwolonego Origin. Listę i operacje na
kontach chroni rola `admin` po stronie API. Odpowiedzi administracyjne
zawierają stan konta, wersję i pola profilowe. Błędy poczty wskazują możliwość
ponowienia na koncie oczekującym.

## Odbiór

| Scenariusz | Oczekiwany dowód |
| --- | --- |
| Administrator tworzy konto i wprowadza pierwsze zmiany | Prawidłowe dane, konflikt z istniejącym loginem/e-mailem `409`, stara wersja `409`, brak hasła i tokenu w odpowiedzi panelu |
| Kierownik i Użytkownik wywołują każdy endpoint administracyjny, także dla cudzego UUID | `403`, brak danych konta i skutku zapisu |
| Odbiorca otwiera zaproszenie oraz ustawia hasło | Przejście do aktywnego, logowanie po loginie i e-mailu, wygasły i zużyty link `400`, dwa równoległe użycia dają tylko jeden sukces |
| Wysłanie lub ponowienie zaproszenia w razie awarii SMTP | Czytelny błąd, aktualny status konta i możliwość ponowienia; poprzedni ważny link działa po nieudanym ponowieniu |
| Rola lub status zmienia się podczas używania aplikacji | Dotychczasowe ciasteczko przestaje dawać dostęp; ponowne logowanie respektuje decyzję i macierz |
| Dwóch administratorów próbuje odebrać sobie dostęp | Pozostaje co najmniej jeden aktywny administrator |
| Migracja istniejących kont i odtworzenie | W izolowanej bazie sprawdzić upgrade/downgrade, zachowanie logowania i aktywności kont oraz przywrócenie kopii |
| Test przeglądarkowy pod testowym adresem | Desktop i telefon, formularz i potwierdzenia, poprawny powrót z linku, nawigacja klawiaturą |

Testy automatyczne korzystają z osobnego PostgreSQL i syntetycznej poczty.
Przegląd według [SCRUM-101](../security/SCRUM-101-ASVS-5.0.0-L2.md) obejmuje
wybrane kontrole limitów, sesji i egzekwowania uprawnień po stronie API
(`v5.0.0-6.3.1`, `v5.0.0-7.2.1`, `v5.0.0-8.2.1`, `v5.0.0-8.3.1`).
