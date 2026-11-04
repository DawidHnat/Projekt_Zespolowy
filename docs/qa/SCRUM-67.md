# SCRUM-67 — domena i HTTPS

## Potwierdzony zakres z 3 listopada 2026

- Główny rekord A `fleet-flow.pl` zmieniono w OVH z `213.186.33.5`
  na `57.129.179.53`, TTL 300 s. Przed zmianą TTL wynosił 3600 s;
  poprzednia odpowiedź może pozostawać w pamięci resolverów do godziny.
- Zmieniono tylko ten rekord. NS, poczta, MX, SPF, DKIM i pozostałe wpisy
  zachowano. Nie dodawano AAAA bez testu IPv6.
- Na VPS `APP_DOMAIN=fleet-flow.pl`, `CORS_ORIGINS=https://fleet-flow.pl`
  oraz istniejące `COOKIE_SECURE=true`. Kontenery API i Caddy odtworzono
  bez budowy obrazu, migracji, zmiany bazy lub kont.
- Publiczna strona wersji po HTTP na IP prowadzi do nowej domeny.
- Zmienna Actions `DEV_PUBLIC_URL=https://fleet-flow.pl` i istniejący sekret
  `DEV_RUNTIME_ENV` są zaktualizowane. Zawartości sekretu nie publikowano
  ani nie zapisywano lokalnie; pozostałe wartości zachowano.
- Caddy uzyskał certyfikat. Test HTTPS zwrócił HTTP 200 z poprawną
  weryfikacją TLS; `/api/health/ready` zwróciło `{"status":"ok"}`.
- Przeglądarka otworzyła ekran logowania bez ostrzeżenia TLS, z wersją
  aplikacji `4ce144e`. Nie deklaruje to odbioru istniejącego konta ani mapy.

## Zakres tego PR i kolejność wdrożenia

Główny adres działa już na dotychczasowym Caddyfile z nowym środowiskiem.
Ten PR dodaje nazwane przekierowania HTTP oraz HTTPS z `www` i starego
hostname VPS na domenę kanoniczną, z zachowaniem URI. HTTP po IP nadal
pokazuje stronę wersji; API i logowanie wymagają HTTPS.

4 listopada 2026 ponownie potwierdzono rekord A w autorytatywnym DNS OVH,
gotowość API, odpowiedź 401 dla `/api/v1/auth/me` bez sesji i zgodność SHA
`4ce144e` z `main` na stronie HTTP po IP. W izolowanych kontenerach Caddy
zweryfikowano konfigurację, pięć przekierowań HTTP/HTTPS z zachowaniem URI,
HTTPS domeny kanonicznej oraz odpowiedzi 200 dla HTTP po IP i 404 dla API
po HTTP na IP. Test przekierowań używał lokalnego CA i danych syntetycznych.

1. Uzyskać niezależny review konfiguracji i zielone CI zgodnie z ochroną `main`.
2. Po review zmienić w OVH istniejący rekord A `www` z `213.186.33.5` na
   `57.129.179.53` z TTL 300 s.
3. Scalić zatwierdzony PR i poczekać na wdrożenie z `main`. Caddy uzyska
   certyfikat również dla `www`.
   `APP_DOMAIN` ma pozostać `fleet-flow.pl`; powrót do hostname VPS wymaga
   poprzedniego wydania Caddyfile, aby nie zduplikować adresu aliasu.
4. Sprawdzić HTTPS `www` i starego hostname oraz HTTP wszystkich trzech nazw:
   odpowiedź 308, `Location: https://fleet-flow.pl/<ścieżka>?<parametry>`.
5. Potwierdzić HTTP 200 strony głównej i gotowości API na domenie kanonicznej,
   401 chronionego API bez sesji, logowanie istniejącym kontem, sesję po
   odświeżeniu i mapę. Sprawdzić ewentualne ograniczenia adresów tokenu Mapbox
   bez publikowania tokenu. Zmiana hosta wymaga ponownego logowania;
   dotychczasowe cookie nie jest przenoszone pomiędzy domenami.
6. Po wdrożeniu porównać SHA strony z aktualnym `origin/main` i sprawdzić
   kursowe HTTP po IP. SCRUM-67 pozostaje otwarte do pełnego odbioru.

## Przywrócenie poprzedniej konfiguracji

Przed przełączeniem zapisano prywatną kopię środowiska i strony wersji
w `/opt/fleet-flow/shared/domain-switch-20261103/` (katalog root 700,
środowisko 600). Kopie nie należą do Git i nie wolno ich załączać do PR.
Historia strefy OVH umożliwia odtworzenie poprzednich rekordów; dla głównego
rekordu A poprzednią wartością było `213.186.33.5`, TTL 3600 s.

Administrator przywraca poprzednie wydanie Caddyfile, kopię `runtime.env.before`
oraz `status.html.before`, odtwarza tylko API i Caddy z tym samym SHA obrazu,
a w Actions przywraca `DEV_PUBLIC_URL` i sekret środowiska. Sprawdza HTTPS
hostname VPS i gotowość API przed ewentualnym przywróceniem DNS. Sam powrót
rekordu A do parkingu nie przywraca aplikacji. Nie zmieniać bazy, jej hasła
ani rekordów poczty.
