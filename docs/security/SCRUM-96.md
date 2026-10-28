# SCRUM-96 — nagłówki i zaufany reverse proxy

Baza: SCRUM-107 / PR43 → PR40 → PR39 → PR37 → PR30. Wdrożenie infrastruktury
wymaga review i uzgodnionego okna; nie zmieniono VPS ani DNS/certyfikatów.

## Model zaufania

Caddy jest pierwszym publicznym hopem, bez CDN/LB przed nim. Nie ufa żadnym
nagłówkom klienta: ustawia X-Forwarded-For z adresu bezpośredniego połączenia,
usuwa Forwarded i X-Real-IP, a standardowe X-Forwarded-Proto ustawia sam.
API korzysta z mechanizmu Uvicorn FORWARDED_ALLOW_IPS, który ufa wyłącznie
konkretnemu IP Caddy na prywatnej sieci proxy. Bez wildcarda i zaufania do całych
zakresów prywatnych. Bezpośrednie żądanie do API z innego IP ignoruje forwarding.

Compose dodaje prywatną sieć proxy 172.30.96.0/28; Caddy ma 172.30.96.3,
API alias api-proxy. Reverse proxy używa tego aliasu, aby ruch zawsze przechodził
właściwą siecią. API i PostgreSQL nie mają publikowanych portów. Dotychczasowa
sieć default pozostaje dla bazy i połączeń wychodzących. Ograniczenie publikacji
portów nie zastępuje kontroli Origin, sesji i ról, które pozostają aktywne.

Przed rolloutem operator sprawdza kolizje podsieci z istniejącymi sieciami/VPN.
W razie potrzeby ustawia **razem** FLEET_FLOW_PROXY_SUBNET i FLEET_FLOW_PROXY_IP
(adres w wybranej podsieci, nie wildcard/CIDR). Compose config musi przejść.
Po dodaniu CDN/LB model wymaga osobnego przeglądu dokładnych adresów zaufania;
nie wolno po prostu dodać private_ranges ani ufać wszystkim nagłówkom.

## Nagłówki

W bloku aplikacji Caddy ustawia:

* nosniff, Referrer-Policy same-origin i X-Frame-Options DENY;
* enforced CSP ograniczający frame-ancestors, base-uri i object-src;
* CSP Report-Only z self, blob workerami i rzeczywistymi klasami zasobów Mapbox
  (api.mapbox.com, events.mapbox.com, *.tiles.mapbox.com, obrazy *.mapbox.com);
* Permissions-Policy wyłączający zbędną kamerę, mikrofon, geolokalizację przeglądarki,
  płatności i USB. GPS floty z backendu nie używa geolokalizacji przeglądarki.

Reszta CSP pozostaje report-only; nie włączono enforce całej polityki ani zdalnego
odbiorcy raportów. Błędy są widoczne lokalnie w konsoli przeglądarki; nie należy
publikować raportów z prywatnymi adresami/parametrami. Docelowy Mapbox musi zostać
sprawdzony przez QA z zatwierdzoną konfiguracją: style, kafle, glyphy i workery,
logowanie oraz fallback. Obecne E2E sprawdza login i fallback na syntetycznym API,
ale nie stanowi odbioru TLS/Mapbox na domenie.

Publiczny HTTP nadal pokazuje wyłącznie wersję/odnośnik, bez loginu i API floty.
HSTS nie włączono: warunkiem są odebrane HTTPS, domena i procedura odnowienia
certyfikatu. Po odbiorze operator może w przeglądanym PR zacząć od max-age=300
w **bloku HTTPS aplikacji**, sprawdzić klientów/rollback i dopiero zwiększyć TTL.
Nie dodawać includeSubDomains/preload bez osobnej oceny. Rollback HSTS wymaga
max-age=0 dostarczonego przez nadal działające HTTPS; samo usunięcie nagłówka
nie cofa wcześniej zapamiętanej polityki.

## Powtarzalny test rzeczywistego Caddy

```sh
docker build -f infra/deploy/backend.Dockerfile -t fleet-flow-api:proxy-test .
python3 infra/tests/check_proxy.py --image fleet-flow-api:proxy-test
```

Skrypt tworzy wyłącznie własną sieć --internal oraz efemeryczne Caddy/API/PostgreSQL
z prefiksem fleet-proxy-test-UUID. Brak portów publikowanych na hoście, danych
projektu i żywych integracji. W finally usuwa tylko utworzone przez siebie zasoby.
Baza nazywa się fleet_flow_test_proxy, dane są syntetyczne, a logi nie drukują
połączenia/treści żądań. Caddy i jego Caddyfile pochodzą z konfiguracji wdrożenia.

Dowód developerski 28.10.2026: Caddy2.11.7 (digest zapisany w Compose), API z obrazu
SCRUM-95 Python3.13 Alpine, PostgreSQL17, lokalny Docker Desktop. PASS:

* nagłówki na stronie, readiness oraz odpowiedzi API401; brak HSTS przed odbiorem;
* pierwsze IP: 10 błędnych loginów 401, jedenasty 429 mimo różnych podrobionych
  X-Forwarded-For, Forwarded, X-Real-IP oraz X-Forwarded-Proto;
* drugie rzeczywiste IP nadal otrzymuje 401, nie współdzieli wyczerpanego limitu;
* bezpośredni nieufny klient API również nie obchodzi limitu fałszywym XFF;
* realne rekordy limitera w PostgreSQL mają osobne koszyki [11,1,11];
* HTTP zwraca404 dla API, a publiczną stronę wersji200;
* zasoby testowe zostały usunięte; Compose config PASS;
* backend124 pytest PASS, Ruff check i format --check PASS.

Ten sam skrypt wchodzi do joba Backend image i Required CI. Test lokalny nie jest
dowodem aktywnej konfiguracji na VPS, docelowego HTTPS ani odbioru organizacji.

## Rollout i rollback

1. Inny developer reviewuje Caddy/Compose oraz wynik testu na aktualnym SHA.
2. Operator w uzgodnionym oknie sprawdza CIDR, Compose config, istniejący backup
   i bieżącą wersję; nie włącza WEBFLEET/SMTP w ramach tej zmiany.
3. Aktualizuje Caddy i API w ramach jednej wersji, utrzymuje prywatność portów
   i odbiera login, dwie niezależne ścieżki klienta, 429 oraz brak spoofingu.
4. QA odbiera mapę, fallback i konsolę CSP w docelowych przeglądarkach. Dopiero
   po zebraniu rzeczywistych źródeł można proponować pełne CSP enforce.
5. W razie problemu przywróć poprzednią zatwierdzoną wersję Caddy/Compose razem;
   nie ustawiaj FORWARDED_ALLOW_IPS=* ani nie wyłączaj limitera.

Pozostaje niezależny review/QA oraz rzeczywisty odbiór wdrożenia/TLS. Nie oznaczać
Done na podstawie samego testu Docker. Źródła modelu:
https://uvicorn.dev/settings/ i https://caddyserver.com/docs/caddyfile/directives/reverse_proxy.
