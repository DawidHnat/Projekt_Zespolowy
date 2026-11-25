# SCRUM-114 — metryki operacyjne i bezpieczny `X-Correlation-ID`

Dokument opisuje zakres i granice bezpieczeństwa kodu obserwacji dostarczonego w `SCRUM-114` (podzadanie `SCRUM-99`, epik `SCRUM-93`).

## 1. Bezpieczny identyfikator korelacji (`X-Correlation-ID`)

- Middleware HTTP (`backend/app/main.py`) oraz cykle workera synchronizacji (`backend/app/modules/fleet/sync.py`) wiążą każdy przebieg z identyfikatorem korelacji (`ContextVar`).
- Wartość z nagłówka `X-Correlation-ID` jest akceptowana wyłącznie wtedy, gdy spełnia ograniczenie `^[A-Za-z0-9._-]{8,64}$` (czyste ASCII, bez znaków sterujących, CRLF, spacji i nadmiernej długości). W przeciwnym razie generowany jest nowy losowy identyfikator `uuid4().hex` (32 znaki szesnastkowe).
- Zweryfikowany lub wygenerowany identyfikator jest:
  - zwracany w nagłówku odpowiedzi `X-Correlation-ID` (udostępnionym przez `Access-Control-Expose-Headers`),
  - dołączany jako pole `error.correlation_id` w odpowiedziach błędów serwera (`HTTP 5xx`), przy zachowaniu identycznych ciał odpowiedzi `4xx` (np. anty-enumeracja logowania),
  - udostępniany w UI przy błędach serwera (`ID zgłoszenia: <correlation_id>`) w celu jednoznacznego zgłoszenia incydentu bez ujawniania szczegółów wewnętrznych,
  - zapisywany w ustrukturyzowanych zdarzeniach błędów HTTP `5xx` (`fleet_flow.observability`) oraz w istniejących zanonimizowanych zdarzeniach synchronizacji (`fleet_flow.sync`, bez duplikowania logów z `SCRUM-64`).

## 2. Zakres metryk i ograniczenie liczności etykiet (bounded cardinality)

Endpoint `GET /api/v1/observability/metrics` zwraca migawkę JSON (`format=json`, domyślnie) lub format tekstowy Prometheus (`format=prometheus`):

| Obszar | Pola / metryki | Ograniczenie etykiet i ochrona prywatności |
| --- | --- | --- |
| API i HTTP | `api_up`, `http.requests_total`, `http.errors_5xx_total`, `http.duration_p95_ms`, `http.by_route` | Etykiety ograniczone do stałych metod HTTP, szablonów tras FastAPI (`route_template` albo `unmatched`/`other`, maks. 64) i klas statusów (`2xx`–`5xx`). Brak surowych ścieżek URL, parametrów query, IP i identyfikatorów obiektów. |
| Pula bazy danych | `db_pool.db_up`, `size`, `checked_in`, `checked_out`, `overflow` | Brak DSN, hostów, zapytań SQL i treści wyjątków. |
| Synchronizacja WEBFLEET | `sync.status`, `last_success_age_seconds`, `latest_measurement_age_seconds`, `last_error_code`, `events_total` | Wyłącznie zagregowany wiek i stałe kody (`ok`, `busy`, `rate_limited`, `timeout`, `connection_failed`, `provider_rate_limit`, `local_rate_limit`, `INVALID_RECORDS`, `INCOMPLETE_REPORT`, `SOURCE_DEGRADED`, `SYNC_INTERNAL_ERROR`, `SYNC_CONTROL_FAILED`, `OTHER`). Brak `external_uid`, konta źródłowego, tablic i GPS. |
| Dysk | `disk.status`, `total_bytes`, `used_bytes`, `free_bytes`, `free_ratio` | Tylko liczby bajtów i próg (`warning < 15%`, `critical < 5%`), bez ścieżek hosta w odpowiedzi. |
| Backup i odtworzenie | `backup`, `restore` (`status`, `deferred_to`, `last_success_age_seconds`, `max_age_seconds`) | Gdy `FLEET_FLOW_BACKUP_STATE` nie jest skonfigurowane, zwracany jest jawny stan `not_configured` z `deferred_to: "SCRUM-84"` — bez fikcyjnych dat sukcesu. Po podłączeniu czyta wyłącznie `completed_at` z `last-backup.json` (próg 7 h) i `last-restore.json` (próg 32 dni), spójnie z `infra/backup/check_health.py`. |
| Certyfikat TLS | `tls.status`, `days_remaining`, `warning_days`, `critical_days` | Lokalny odczyt czasu ważności X.509 (`TLS_CERT_PATH`, domyślne progi 21 i 7 dni) lub jawne `not_configured`, gdy ścieżka nie została podana. |
| Bezpieczeństwo i poczta | `auth.events_total`, `mail.events_total`, `mail.queue` | Stałe kody zdarzeń (`login_failed`, `rate_limited`, `forbidden`, `unauthenticated`, `invalid_reset`, `invalid_current_password` oraz `delivered`, `setup_failed`, `smtp_failed`, `state_failed`, `notification_failed`). Kolejka pocztowa ma jawny stan `not_configured` (`deferred_to: "SCRUM-73"`). Brak loginów, adresów e-mail, IP, tokenów i treści wiadomości. |

## 3. Uprawnienia, retencja i zależności operacyjne

- **Uprawnienia:** `GET /api/v1/observability/metrics` wymaga uwierzytelnionej sesji z rolą `admin` (`401 UNAUTHENTICATED` bez sesji, `403 FORBIDDEN` dla ról `editor` oraz `viewer`). Odpowiedzi posiadają nagłówek `Cache-Control: no-store`.
- **Retencja w procesie API:** liczniki oraz ograniczone okna próbek latencji (`deque` maks. 512 próbek globalnie i 128 na szablon trasy) są utrzymywane wyłącznie w pamięci procesu aplikacji i zerowane przy restarcie; nie tworzą nowej tabeli z danymi osobowymi w PostgreSQL. Retencja logów systemowych/journald, docelowego systemu zbierania metryk oraz kanału powiadomień podlega zatwierdzeniu operatora i polityce prywatności `SCRUM-94` / `SCRUM-109`.
- **Granica zadania:** kod `SCRUM-114` nie wybiera płatnej usługi monitoringu, nie zmienia konfiguracji VPS i nie deklaruje produkcyjnego doręczenia alarmów przed decyzją operatora/PO w `SCRUM-99` oraz uruchomieniem kopii w `SCRUM-84`.
