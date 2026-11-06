# ADR SCRUM-102 — SSO/MFA po MVP

Data: 06.11.2026. Właściciel zakresu: Jakub Czaja (PO).
Status decyzji o zakresie: **potwierdzona przez PO**.
Status implementacji SSO/MFA: **odłożona; niewdrożona**.

## Decyzja i jej źródło

PO odpowiedział 06.11.2026 na pytanie, czy organizacja wymaga SSO/MFA już
teraz w Fleet-Flow: „Nie — zostawić jako etap po MVP”.
Na etapie MVP pozostają istniejące lokalne konta i sesje aplikacji.
SCRUM-102 nie blokuje demonstracji MVP z powodu braku SSO, zgodnie z jego
opisem w Jira. Decyzja o kolejności prac nie jest zatwierdzeniem pełnego
bezpieczeństwa, prywatności ani spełnienia wymagań innej organizacji.

Nie wybrano dostawcy tożsamości ani tenanta. Nie utworzono IdP, nie poniesiono
kosztów i nie aktywowano SSO/MFA. Nie powstaje własna implementacja MFA
w ramach dokumentowania tej decyzji. Priorytet pozostaje P2 po MVP;
warunkowe podniesienie do P1 wymaga konkretnego wymagania organizacji.

## Obecny stan techniczny

Przejrzano `main` / `4ce144e3e988106059acdbb6cd01ae9baa3beee4`:

- `backend/app/modules/auth/models.py`: lokalny użytkownik, hash hasła,
  rola, aktywność, opcjonalny e-mail oraz osobne rekordy sesji/resetu.
- `backend/app/modules/auth/router.py`: logowanie, limit prób, losowy token
  sesji w cookie HttpOnly, SameSite=Strict i Secure dla docelowego HTTPS.
- `backend/app/modules/auth/service.py`: kontrola aktywności konta i sesji.
  `User` nie zawiera tożsamości OIDC, tenanta ani informacji o MFA.
- `backend/app/modules/auth/reset.py`: reset lokalnego hasła. Istnienie
  kodu resetu nie jest dowodem konfiguracji lub dostawy poczty produkcyjnej.

To **nie zapewnia MFA**. Nie ma callbacku OIDC ani odbioru jego scenariuszy.
Hasło, TLS, cookie i reset nie zastępują drugiego składnika.

## Warunki wznowienia po MVP

| Wymagana decyzja / dowód | Właściciel przygotowania | Stan |
| --- | --- | --- |
| Organizacja i uzasadnione wymaganie SSO/MFA | PO wraz z właściwą organizacją | Brak bieżącego wymagania według decyzji PO |
| IdP, tenant/issuer, region, umowy i koszt | PO + Dawid Hnat, zatwierdza właściciel organizacji | Nieustalone; brak zgody na wydatki |
| Mapowanie tożsamości i ról oraz granice organizacji | PO + developer IAM, review innej osoby | Do opracowania; brak automatycznego nadawania admina lub łączenia kont wyłącznie po e-mailu |
| Wymóg MFA i sposób potwierdzenia jego spełnienia przez wybrany IdP | Organizacja + developer IAM | Do uzgodnienia i negatywnych testów dla danego dostawcy |
| Wyłączenie konta, unieważnienie sesji i logout | Dawid Hnat + developer IAM | Do ustalenia, jak szybko odebrany dostęp dociera do aktywnej sesji Fleet-Flow |
| Break-glass i recovery | Upoważniony administrator organizacji + Dawid Hnat | Do wskazania właściciele, kontrola dostępu, audyt i ćwiczenie; bez danych awaryjnych w Git/Jira |
| Migracja lokalnych kont i rollback | Developer IAM + Dawid Hnat; odbiór QA | Do opracowania przed aktywacją, bez osłabiania wymaganego MFA przez fallback |

Brak tych danych blokuje przyszłą aktywację integracji; nie jest poleceniem
kupna usługi ani utworzenia dostępu dla nowego podmiotu.

## Zakres przyszłej implementacji i odbioru

Po zatwierdzeniu dostawcy i kosztów osobny PR realizuje wymagania SCRUM-102:

1. OIDC Authorization Code z kontrolą state/nonce/redirect i walidacją tokenów
   właściwą dla wybranego IdP. Integracja nadal wydaje własną sesję HttpOnly;
   tokeny IdP nie trafiają do localStorage, URL aplikacji ani logów.
2. Zatwierdzone mapowanie ról, obsługę odebrania konta i wymogu MFA.
3. Negatywne testy obcego issuer/tenanta, callback replay, niespełnionego MFA
   i wyłączonego konta oraz testy migracji, recovery, logout i rollbacku.
4. Niezależny review, wymagane zielone CI, odbiór QA na konkretnym SHA
   i potwierdzone wdrożenie. Powyższa lista to wymagania, a nie wyniki PASS.

## Powiązania i rozliczenie zadania

- [SCRUM-102](https://fleet-flow.atlassian.net/browse/SCRUM-102) — całość
  warunkowej integracji pozostaje w backlogu po MVP.
- SCRUM-47/48/49 — administracja, role i konta pozostają osobnym zakresem.
- SCRUM-94 — ustalenie administratora danych i granicy organizacji.

Ten ADR kończy ustalenie kolejności prac. Nie zamyka całego SCRUM-102 jako
wdrożonego OIDC/MFA i nie zmienia kryteriów akceptacji na samą dokumentację.
