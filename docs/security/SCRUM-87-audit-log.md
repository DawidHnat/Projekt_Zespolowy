# Wspólny dziennik zmian (SCRUM-87 / epik bezpieczeństwa SCRUM-93)

## Cel i zakres

Moduł `backend/app/modules/audit` zapewnia jeden wspólny, transakcyjny dziennik śladu audytowego (`audit_events`) dla operacji biznesowych i bezpieczeństwa w Fleet-Flow:

1. **Kartoteka pojazdu, przebieg ręczny i dokumenty (`fleet`)**:
   - utworzenie pojazdu ręcznego (`vehicle.created`), edycja kartoteki (`vehicle.updated`), archiwizacja (`vehicle.archived`), przywrócenie (`vehicle.restored`), jawne powiązanie ze źródłem WEBFLEET (`vehicle.source_linked`),
   - aktualizacja przebiegu ręcznego (`vehicle.odometer_updated`),
   - terminy i załączniki przeglądów/OC oraz zdjęcia pojazdu (`vehicle.document_dates_updated`, `vehicle.document_uploaded`, `vehicle.document_replaced`, `vehicle.document_deleted`, `vehicle.photo_updated`, `vehicle.photo_deleted`),
   - import zmian danych podstawowych z WEBFLEET (`vehicle.imported` z `actor_type = "import"`, odróżniony od ręcznych zmian użytkownika `actor_type = "user"`).
2. **Kierowcy i przypisania (`drivers`)**:
   - dodanie i edycja kartoteki kierowcy (`driver.created`, `driver.updated`),
   - rozpoczęcie i zakończenie przypisania kierowca–pojazd (`driver_assignment.created`, `driver_assignment.closed`).
3. **Ewidencja podróży (`trips`)**:
   - zapis i edycja celu, opisu oraz kierowcy w adnotacji podróży (`trip_annotation.updated`).
4. **Bezpieczeństwo kont i sesji (`auth`, rozszerzenie audytu SCRUM-93 / SCRUM-48/49)**:
   - udane i odrzucone logowanie (`auth.login_succeeded`, `auth.login_failed`),
   - wylogowanie bieżącej sesji oraz unieważnienie wszystkich sesji (`auth.logout`, `auth.sessions_revoked`),
   - zmiana hasła i potwierdzenie resetu hasła (`auth.password_changed`, `auth.password_reset_confirmed`),
   - gotowość kontraktu `user_account` pod przyszłe operacje administracyjne zmiany roli i aktywności kont (`role`, `active`) bez tworzenia drugiego rejestru.

## Minimalizacja danych i wykluczenie sekretów (zgodność z SCRUM-94)

Zapis `changes` przechodzi przez jawną białą listę pól (`ALLOWED_FIELDS_BY_ENTITY`) oraz blokadę pól zabronionych (`FORBIDDEN_KEYS`) w `backend/app/modules/audit/service.py`:

- **Nigdy nie są zapisywane**: hasła jawne, skróty haseł (`password_hash`), tokeny sesji i resetu (`token`, `token_hash`), klucze API WEBFLEET/SMTP, kody PIN, pełne numery kart płatniczych/paliwowych (dodatkowa maska wyrażeń regularnych 13–19 cyfr), surowe współrzędne GPS (`latitude`, `longitude`, `position_address`), zewnętrzne identyfikatory dostawcy (`external_uid`), ścieżki składowania (`storage_key`) ani treść binarna załączników.
- **Dane kontaktowe kierowcy**: w dzienniku zapisywana jest wyłącznie informacja o skonfigurowaniu pola (`phone_configured`, `email_configured`), aby nie powielać prywatnych numerów telefonów i adresów e-mail w niezmiennym śladzie audytowym.
- **Identyfikator korelacji**: każde zdarzenie zapisuje zweryfikowany `correlation_id` (`^[A-Za-z0-9._-]{1,64}$` lub wygenerowany UUID hex) oraz czas UTC (`occurred_at`).

## Niezmienność (append-only), transakcyjność i kontrola dostępu

- **Jedna transakcja**: wywołanie `record_audit_event(...)` dodaje rekord do tej samej sesji SQLAlchemy co operacja biznesowa przed `session.commit()`. Wycofanie transakcji (`rollback`) wycofuje jednocześnie wpis audytowy.
- **Append-only**:
  - API udostępnia wyłącznie odczyt (`GET /api/v1/audit/events`, `GET /api/v1/audit/actors`) — brak metod `POST`, `PUT`, `PATCH` oraz `DELETE`.
  - Na poziomie bazy danych wyzwalacz `trg_audit_events_append_only` (PostgreSQL) oraz wyzwalacze `BEFORE UPDATE` / `BEFORE DELETE` (SQLite) blokują modyfikację i usuwanie wierszy przez konto aplikacji.
- **Izolacja odczytu**:
  - Zdarzenia flotowe, kierowców i podróży są filtrowane po `source_account` bieżącego konta źródłowego; odpytanie obcego `vehicle_id` zwraca `404 NOT_FOUND`.
  - Zdarzenia bezpieczeństwa (`user_account`, `user_session`) są widoczne w całości wyłącznie dla roli `admin`, a dla ról `editor` i `viewer` jedynie w zakresie ich własnego `user.id`.

## Retencja i kontrolowana procedura prawna

Tryb `append-only` dla bieżącej pracy aplikacji nie oznacza bezterminowego przechowywania danych osobowych:

- Docelowy okres retencji operacyjnej dziennika wynosi **365 dni** dla zdarzeń operacyjnych i bezpieczeństwa (do potwierdzenia w polityce retencji `SCRUM-94`).
- Wyłącznie kontrolowane zadanie utrzymaniowe/prawne (np. wykonanie obowiązku prawnego usunięcia danych lub retencji po upływie okresu przechowywania) może w dedykowanej transakcji administracyjnej ustawić parametr sesji PostgreSQL `SET LOCAL fleet_flow.audit_maintenance = 'allow'` przed wykonaniem archiwizacji/usunięcia przeterminowanych rekordów. Aplikacja webowa nigdy nie ustawia tego parametru.
