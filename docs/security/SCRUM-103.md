# SCRUM-103 — role w bazie i lokalna dokumentacja API

Obecny katalog ról pozostaje `admin`, `editor`, `viewer`. Login, zależności
żądań i CLI korzystają z `app/modules/auth/policies.py`. Admin i editor mogą
edytować istniejące funkcje biznesowe, viewer czyta dane i zachowuje własny
odczyt alertów. Zmiana nie dodaje uprawnień ani operacji administracyjnych.
Odrzucenie sesji nieaktywnego konta, Origin, HttpOnly/Secure/SameSite i
odwołanie sesji pozostają egzekwowane na serwerze.

## Migracja

`0007_user_roles` dodaje CHECK `ck_users_role`. Przed skanem zajmuje blokadę
zapisu `users`, następnie sprawdza istniejące wartości. Nieznana rola przerywa
całą transakcję bez zmiany rekordów i bez wypisywania danych użytkownika.
Operator musi wyjaśnić niepoprawne konto z właścicielem dostępu; nie ma
masowego przypisania viewer ani automatycznej eskalacji do admina.

Po zatwierdzeniu review, QA i okna infrastruktury:

1. Potwierdzić sprawdzony backup i dokładne SHA. Zatrzymać zapisujące procesy
   API/worker, w tym CLI tworzenia i edycji kont.
2. W prywatnej konsoli sprawdzić liczbę nieznanych ról:
   `SELECT count(*) FROM users WHERE role NOT IN ('admin','editor','viewer') OR role IS NULL;`.
   Wynik musi wynosić zero. Szczegółów kont nie publikować w logach/PR.
3. Uruchomić standardowe `python -m alembic upgrade head`, bez wypisywania
   DATABASE_URL. Sprawdzenie danych i constraint są jedną transakcją.
4. Uruchomić procesy na odebranym SHA; sprawdzić login, odczyt viewer,
   zabronioną edycję viewer i dozwoloną edycję editor na danych testowych.

Rollback DDL: zatrzymać zapisy i `python -m alembic downgrade 0006_fleet_search`.
Usuwa jedynie constraint ról, zachowuje UUID, role, hashe i sesje. Wcześniejsza
migracja wyszukiwania pozostaje. Nie wykonywać downgrade poniżej 0006 bez
instrukcji SCRUM-97. Wdrożenia ani migracji VPS nie wykonano w tym PR.

## Dokumentacja API

`/docs`, `/redoc`, `/docs/oauth2-redirect` i `/openapi.json` są dostępne tylko,
gdy wszystkie CORS_ORIGINS wskazują loopback i `API_DOCS_ENABLED` nie jest
false. Domyślny lokalny development zachowuje dokumentację, zdalne pochodzenie
wyłącza ją automatycznie. Jawne `API_DOCS_ENABLED=true` przy zdalnym pochodzeniu
powoduje bezpieczny błąd konfiguracji. Dozwolone wartości: true/false.
Ręczne skonstruowanie Settings nie omija dodatkowej kontroli w create_app.

Schemat do testów/generowania można otrzymać z `app.openapi()` bez publicznego
endpointu. Nie należy włączać publicznych docs do debugowania zdalnego serwera;
uruchomić lokalne środowisko na tym samym SHA. Nie dodano wyjątków w Caddy.

## Dowody i odbiór

Test PostgreSQL przechodzi kontrolowaną odmowę migracji z nieznaną rolą,
upgrade/downgrade, zachowanie kont i sesji oraz odrzucenie czterech
niepoprawnych wartości bezpośrednim UPDATE. Testy API sprawdzają 401, viewer
403, dopuszczenie editor/admin i odmowę obcego Origin. Osobno badane są
cztery tryby lokalne/zdalne i flagi docs oraz konfiguracja środowiska.
Wyniki CI i SHA znajdują się w PR/Jirze. Niezależny review/QA pozostaje wymagany.
