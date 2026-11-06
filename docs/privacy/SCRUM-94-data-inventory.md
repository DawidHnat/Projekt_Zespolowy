# SCRUM-94 — inwentarz danych i rejestr decyzji prywatności

Wersja 0.1, 06.11.2026. Koordynator: Jakub Czaja (PO).
Źródło techniczne: `main` / `4ce144e3e988106059acdbb6cd01ae9baa3beee4`.
Status: **inwentarz do review; zatwierdzenie polityki i screening DPIA BLOCKED**.
To nie jest zaakceptowana polityka retencji ani screening wykonany przez DPO.

## Zakres i brakujące zatwierdzenia

Administrator rzeczywistych danych oraz osoba zatwierdzająca retencję nie
zostali wskazani. Użytkownik potwierdził 06.11.2026, że nie ma tych informacji.
Autor repozytorium, właściciel konta WEBFLEET, administrator VPS i PO nie są
automatycznie tą samą osobą ani administratorem danych w rozumieniu RODO.
Rola prawna dostawców zależy od faktycznych umów i przepływów; poniżej jest
lista do weryfikacji, bez deklarowania zawartych umów powierzenia.

Inwentarz powstał z przeglądu kodu i konfiguracji przykładowej. Nie pobierano
rekordów klienta, sekretów ani rzeczywistych danych GPS i nie zmieniano usług.

| Ustalenie do zatwierdzenia | Stan | Właściciel ustalenia | Termin |
| --- | --- | --- | --- |
| Nazwa administratora, zakres organizacji i osoby uprawnione do decyzji | BLOCKED: brak wskazania | Jakub Czaja koordynuje ustalenie; administrator niewskazany | Data nieustalona; wymagane przed odbiorem rzeczywistych danych |
| Cele, podstawy, role, okresy retencji i wyjątki dla każdej kategorii | BLOCKED | Administrator niewskazany; koordynator Jakub Czaja | Data nieustalona; przed SCRUM-109/110/111 |
| Screening DPIA oraz decyzja o dalszej ocenie | BLOCKED: brak wskazanego DPO/prawnika i informacji o skali | Właściwa osoba do wskazania przez administratora; koordynator Jakub Czaja | Data nieustalona; przed odbiorem prywatności |
| Prywatne użycie aut, informacja dla osób i ich prawa | BLOCKED | Administrator niewskazany; koordynator Jakub Czaja | Data nieustalona; przed użyciem tej funkcji |
| Umowy/dostawcy, lokalizacje przetwarzania i ewentualne transfery | BLOCKED: umowy nie zostały dostarczone | Administrator niewskazany; Dawid Hnat zbiera parametry infrastruktury | Data nieustalona; przed zatwierdzeniem przepływów |

Braki dat są jawne: dokument nie tworzy fikcyjnego terminu ani akceptacji.
Do czasu decyzji bezpiecznym zakresem demonstracji są dane syntetyczne.
Dokument nie potwierdza, że istniejące środowisko zawiera wyłącznie takie dane.

## Inwentarz i minimalne pola

„Obecny” oznacza implementację w sprawdzonym kodzie, nie potwierdzony stan
bazy produkcyjnej. „Planowany” nie oznacza dostępnego endpointu. Cele w tabeli
opisują użycie funkcji; ich dopuszczalność zatwierdza administrator.

| Kategoria / stan | Pola i powiązania | Użycie funkcji i magazyn | Minimalizacja i bieżący dostęp |
| --- | --- | --- | --- |
| Pojazdy / obecny | UUID, konto źródła, zewnętrzny UID, nazwa, numer, rejestracja, typ, aktywność, `driver_id` | Identyfikacja floty; `vehicles` w PostgreSQL | UID źródła jest wewnętrzny; API wymaga aktywnej sesji. Wszyscy dopuszczeni użytkownicy korzystają z jednego kontekstu floty |
| GPS i ostatni pomiar / obecny | `vehicle_id`, szerokość/długość, licznik, zapłon, postój, jakość GPS, czas pozycji i odbioru | Lista/mapa i aktualność; `measurements`, jedna próbka na pojazd | Nie jest to historia tras. Nadpisanie próbki nie usuwa jej z istniejącego dumpu bazy |
| Kierowcy / model obecny, kartoteka w SCRUM-42 | UUID, `display_name`, aktywność, aktualne przypisanie przez pojazd | Ręczne dane Fleet-Flow; `drivers` | Bez importu kontaktów i loginów kierowców z WEBFLEET. Nazwa kierowcy może identyfikować osobę |
| Dystanse, reguły, alerty i odczyty / obecny | Pojazd, dzień, częściowy dystans, granice obserwacji, próg i reguła, czasy zdarzenia, użytkownik/czas odczytu | `daily_distances`, `alert_rules`, `alerts`, `alert_receipts` | Agregat nadal jest powiązany z autem/osobą; nie deklarować anonimowości. Admin/editor zapisują reguły; użytkownik oznacza własny odczyt |
| Użytkownicy / obecny | UUID, login, nazwa wyświetlana, hash hasła, rola, aktywność, opcjonalny e-mail | Lokalne konta; `users` | Bez publicznej rejestracji. E-mail potrzebny do resetu; nie jest polem konta kierowcy |
| Sesje i reset / obecny | Hash losowego tokenu, `user_id`, `expires_at` | Autoryzacja; `login_sessions`, `password_resets`; token sesji w cookie | Cookie HttpOnly/SameSite=Strict i Secure dla HTTPS; tokeny autoryzacji nie są zapisywane w localStorage |
| Limity prób / obecny | Hash klucza IP lub loginu, początek okna, licznik | Ochrona logowania/resetu; `login_attempts` | Hash klucza nie stanowi dowodu anonimizacji; brak globalnego harmonogramu retencji |
| Synchronizacja / obecny | Klucz konta źródła, ostatnia próba/sukces, bezpieczny kod błędu | `sync_states`, koordynacja importu | Bez pełnych odpowiedzi dostawcy w błędach API; powiązanie konta pozostaje informacją wewnętrzną |
| Lokalne preferencje i obrazy / obecny | Układ, motyw, identyfikatory pojazdów, przeskalowane obrazy i tło | localStorage oraz IndexedDB przeglądarki | Zdjęcia nie są współdzielonym magazynem serwera. Bitmapa jest przetwarzana lokalnie; zakresy kluczy nie zastępują kontroli dostępu do profilu przeglądarki |
| Historia, cel/opis przejazdu / planowany | Pojazd, identyfikator trasy, czasy, dystans, punkty trasy, ręczny opis, autor i wersja | SCRUM-6/24/29/62; projekt w `docs/DATA_MODEL.md` | Wymaga osobnego odbioru, zasad prywatnych przejazdów i minimalizacji wolnego tekstu |
| Skany dokumentów, polisy, leasing / planowany | Dane auta, terminy i pliki; możliwe dane identyfikacyjne na skanach | SCRUM-57/68 | Nie przesyłać skanów osób do Git/Jira; szczegółowy zakres ustalić przed wdrożeniem |
| Dziennik audytu / planowany | Aktor, operacja, obiekt, czas, wynik; bez treści sekretów | SCRUM-87 | Wymaga projektu dostępu, minimalnego śladu i własnej retencji; nie jest już wdrożonym rejestrem |
| Logi techniczne i kopie bazy / obecne mechanizmy | Logi usług mogą zawierać IP, ścieżki i zapytania; dump bazy obejmuje jej dane | Docker/VPS; dump przed wdrożeniem w `shared/backups` | Nie potwierdzono retencji logów ani kopii poza VPS. Parametry wyszukiwania mogą identyfikować osobę; wymagana weryfikacja redakcji |

## Przepływy i dostawcy do sprawdzenia

1. WEBFLEET → adapter backendu → PostgreSQL → chronione API → przeglądarka.
   Sekrety źródła pozostają po stronie backendu. Kierowcy są wpisami ręcznymi.
2. Przeglądarka → Mapbox po style/kafelki, gdy skonfigurowano token.
   Pozycje pojazdów są używane do znaczników i ustawiania widoku mapy.
   Metadane żądań i obszar mapy wymagają oceny; przegląd kodu nie zastępuje
   pomiaru ruchu SDK ani analizy jego warunków/telemetrii.
3. Backend → SMTP OVH → przypisany adres konta: link resetu zawiera token
   jednorazowy. Implementacja nie potwierdza konfiguracji ani faktycznej dostawy.
4. GitHub Actions → VPS OVH: kod, artefakty i prywatna konfiguracja wdrożenia.
   Dane klientów nie należą do repozytorium, artefaktów testowych ani Jira.
5. PostgreSQL → dump przed wdrożeniem → lokalny test restore. Mechanizm ten
   nie potwierdza backupu poza VPS ani późniejszego usuwania danych z kopii.
6. Użytkownik → lokalny obraz/ustawienia → pamięć przeglądarki. To osobny
   magazyn od bazy serwera i wymaga uwzględnienia w procedurze usuwania.

Dostawcy z kodu: WEBFLEET, OVH/VPS i poczta, Mapbox, GitHub/Actions oraz
Atlassian/Jira dla procesu projektu. Podmioty prawne, umowy, regiony i role
pozostają do potwierdzenia, nie wynikają z samych nazw produktów.

## Retencja — stan kodu i wejście do SCRUM-109

| Kategoria | Obecny mechanizm techniczny | Polityka docelowa / status |
| --- | --- | --- |
| Ostatni GPS | Upsert nadpisuje pomiar; dezaktywacja auta nie usuwa całej historii innych tabel | Okres i wyjątki BLOCKED |
| Konta, kierowcy, pojazdy, dystanse i alerty | Brak ogólnego joba retencji | Oddzielny okres dla każdej kategorii BLOCKED |
| Sesje | Ważność domyślnie 12 h; czyszczenie wygasłych przy poprawnym logowaniu | TTL autoryzacji nie jest gwarancją terminowego usunięcia rekordów; polityka BLOCKED |
| Reset | Token ważny 20 min; nowy zastępuje poprzedni, skuteczny reset usuwa tokeny użytkownika | Nie jest to harmonogram czyszczenia wszystkich wygasłych tokenów; polityka BLOCKED |
| Limity prób | Stare okna usuwane przy poprawnym logowaniu; liczniki okien aktualizowane przy próbie | Okres i harmonogram BLOCKED |
| Obrazy/preferencje urządzenia | Pozostają w profilu przeglądarki do usunięcia/zmiany; logout nie jest dowodem wyczyszczenia IndexedDB | Okres, urządzenia współdzielone i sposób czyszczenia BLOCKED |
| Logi i backupy | Dump przy wdrożeniu; brak zatwierdzonej polityki okresów w sprawdzonych plikach | Osobne okresy, wyjątki, przechowywanie i odtwarzanie BLOCKED |
| Dane planowanych modułów | Brak wdrożenia w badanym SHA | Decyzje przed implementacją BLOCKED |

Dla każdego wiersza: zatwierdza niewskazany jeszcze administrator; koordynuje
Jakub Czaja. Podstawa, okres, wyjątki/legal hold, data decyzji, termin realizacji
i wersja są **nieustalone**, nie APPROVED. SCRUM-109 nie otrzymuje arbitralnych
wartości, np. „30 dni”, z tego dokumentu. Nie uruchomiono retencji ani kasowania.

## Procedury do zatwierdzenia i wykonania

| Obszar | Wejście do realizacji | Stan |
| --- | --- | --- |
| Dostęp | Administrator zatwierdza macierz ról, odbiorców i zakres danych; SCRUM-48 ją egzekwuje. Jedna sesja nie oznacza izolacji kilku firm | BLOCKED: zatwierdzenie; obecny kod opisany wyżej |
| Prywatne użycie i informowanie osób | Ustalić zakres monitoringu, uprawnienia wglądu, informację i obsługę przejazdu prywatnego; brak uniwersalnej zgody na GPS | BLOCKED: decyzja administratora |
| Żądanie osoby / eksport | Zweryfikować osobę i upoważnienie, ustalić powiązania pojazd–kierowca–czas i zakres danych osób trzecich; bezpieczny odbiór; minimalny ślad bez zawartości eksportu | Polityka BLOCKED; implementacja SCRUM-110 |
| Usuwanie/anonimizacja | Zweryfikować upoważnienie, wyjątki i zakres wszystkich tabel/plików, kontrolować ponowny import ze źródła; wynik i minimalny ślad | Polityka BLOCKED; implementacja SCRUM-111 |
| Backup i restore | Określić ważność kopii, dostęp i postępowanie po restore, aby ponownie zastosować wykonane usunięcia przed udostępnieniem danych; sprawdzić odtworzenie | Polityka BLOCKED; recovery SCRUM-84, retencja SCRUM-109 |
| Incydent | Wskazać kontakt, administratora i zastępstwo; ograniczyć dostęp, zabezpieczyć minimalne dowody i przekazać ocenę obowiązków właściwej osobie | BLOCKED: brak właściciela procedury; dokument nie potwierdza spełnienia obowiązków prawnych |

## Materiał do screeningu DPIA

To lista pytań dla właściwej osoby, a nie wykonana przez nią ocena:

- Ilu kierowców/aut dotyczy system, jak często i na jakim obszarze zbiera GPS?
- Czy monitorowani są pracownicy, przejazdy prywatne, czas poza pracą?
- Czy dane służą ocenie zachowania, decyzjom kadrowym, profilowaniu lub
  łączeniu ze skanami/danymi z innych źródeł? Kod alertu dystansu nie dowodzi
  takiego celu, ale cel musi zostać ustalony.
- Jakie są okresy i zakres historii, odbiorcy, skutki błędnego przypisania,
  ryzyka nieuprawnionego wglądu i odtworzenia usuniętych danych z backupu?
- Jakie środki ograniczają te ryzyka i jakie ryzyko pozostaje po ich wdrożeniu?

**Wynik screeningu: BLOCKED / niewykonany.** Autor i jego umocowanie, data,
źródła informacji, uzasadnienie konieczności DPIA/dalszych kroków oraz akceptacja
pozostają do uzupełnienia. Nie stwierdzono braku obowiązku DPIA.

Punkty odniesienia do właściwej oceny:
[RODO, w szczególności art. 5, 24–25, 28, 30, 32–36](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)
oraz [wyjaśnienia UODO dotyczące oceny skutków i wykazu operacji](https://uodo.gov.pl/pl/598/3617).
Artykuł 35 wiąże ocenę z ryzykiem, charakterem, zakresem, kontekstem i celami;
jeśli wyznaczono IOD, przewiduje zasięgnięcie jego porady. Tabela pytań nie
rozstrzyga zastosowania tych przesłanek do nieustalonej organizacji.

## Dowody i warunki odbioru

- Modele: `backend/app/core/models.py`, `backend/app/modules/auth/models.py`,
  `backend/app/modules/analytics/models.py`.
- Dostęp i cykl życia: `backend/app/modules/auth/{service,router,reset}.py`,
  `backend/app/modules/fleet/router.py`, `backend/app/modules/fleet/sync.py`.
- Pamięć urządzenia/mapa: `frontend/src/features/fleet/model/vehicle-photo-store.ts`,
  `frontend/src/features/dashboard/model/background-image.ts`,
  `frontend/src/features/fleet/components/VehicleMap.tsx`.
- Kopie i usługi: `infra/deploy/deploy.sh`, `infra/deploy/compose.yml`,
  `infra/deploy/Caddyfile`; zakres planowany: `docs/DATA_MODEL.md`.
- Założenie organizacji: [ADR SCRUM-94](../adr/SCRUM-94-data-isolation.md).

Do Done SCRUM-94 potrzebne są wskazane i zatwierdzone decyzje właścicieli,
udokumentowany screening, niezależny review PR i wymagane CI. Samo utworzenie
tego inwentarza nie uruchamia SCRUM-109/110/111 i nie zamyka kryteriów zadania.
