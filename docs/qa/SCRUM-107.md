# SCRUM-107 — dostępność

Baza: PR40 → PR39 → PR37 → PR30. Testy axe są w istniejącym E2E i przez ten job
wchodzą do Required CI. Brak nowych wywołań WEBFLEET/SMTP lub danych demo w produkcie.

## Zakres automatyczny i próg do odbioru

axe-core/playwright 4.14.0, reguły WCAG 2.0/2.1/2.2 A/AA; każde wykryte naruszenie
blokuje, bez exclude/disableRules i bez wyjątków. Próg jest propozycją tej
implementacji do zatwierdzenia w review. Skan obejmuje login, błąd logowania,
listę ze wszystkimi czterema statusami, mapę z fallbackiem, szczegóły/dialog, edytor adnotacji i błąd zapisu
z zachowaniem szkicu. Każdy stan działa w motywie light/dark, 1440×1000 i 390×844.
Test zapisuje jedynie ID reguły/impact i selektory; screenshoty zawierają tylko
syntetyczną flotę. Motyw pochodzi z preferencji, reduced-motion stabilizuje skan.

Osobny test klawiatury sprawdza Enter/Space, Tab/Shift+Tab na granicach dialogu,
strzałkę i End na zakładkach, Escape oraz przywrócenie fokusu do przycisku otwarcia.
Zestaw nie potwierdza całej zgodności WCAG i nie zastępuje odbioru ręcznego.

## Wykryte i naprawione problemy

Kontrolny niescalany PR42 wprowadza testy na starszym UI. Wykrywa zbyt niski
kontrast stopki i aktywnej zakładki oraz opuszczenie dialogu przez Shift+Tab.
W kolejnych stanach axe ujawnił kontrast błędu logowania, fallbacku mapy i opisów
dialogu nad materiałem glass. Poprawki używają wspólnych tokenów: --wallpaper-muted,
--text, ciemniejszego --danger dla light oraz podkreślenia aktywnej zakładki.
Dialog jawnie zawija Tab i Shift+Tab między widocznymi aktywnymi kontrolkami.
Escape aktualizuje stan od razu; opóźnione zdarzenie close nie zamyka ponownie
szybko otwartego panelu. Regresja testuje ponowne otwarcie Spacją oraz szkic.

Lokalny retest: 47/47 npm test, build PASS; skany i klawiatura 6/6 desktop/mobile
PASS po poprawkach. Pełny zestaw E2E: 32/32 PASS w około 60 s po dodaniu wszystkich czterech statusów.
Kontrolny PR42, SHA740850c, run40687910884: Critical browser flows oraz Required CI
FAIL, pozostałe joby SUCCESS. Dowód: https://github.com/DawidHnat/Projekt_Zespolowy/actions/runs/40687910884.
Zielony wynik poprawionego PR należy zachować przy końcowym SHA w zadaniu.

## Ręczny protokół QA — do wykonania przez niezależnego odbiorcę

Przed testem zapisz: SHA, przeglądarkę i wersję, system, datę UTC, adres
środowiska syntetycznego, viewport, motyw/material, osobę testującą. Dla każdego
wiersza poniżej wpisz expected/actual, PASS/FAIL/BLOCKED, zrzut lub opis dowodu
i numer błędu. Nie wklejaj prawdziwej telemetrii ani loginów użytkowników.

| Scenariusz | Oczekiwane zachowanie | Light desktop/mobile | Dark desktop/mobile |
|---|---|---|---|
| Login i błąd | Tab/Shift+Tab w logicznym porządku; etykiety, fokus i komunikat widoczne; Enter wysyła | do odbioru | do odbioru |
| Lista, filtry, fallback | Całość obsługiwana klawiaturą; nazwy pól i przycisków czytelne; aktualizacja ogłoszona | do odbioru | do odbioru |
| Szczegóły | Enter i Spacja otwierają; fokus trafia do zamknięcia; Tab/Shift+Tab nie wychodzą do tła | do odbioru | do odbioru |
| Zakładki | Strzałki/Home/End wybierają zgodną zakładkę; focus widoczny; nazwa i panel powiązane | do odbioru | do odbioru |
| Edycja, zapis, błąd | Cel i opis mają etykiety; błąd i sukces dostępne; szkic zostaje po nieudanym zapisie | do odbioru | do odbioru |
| Escape i powrót | Bez szkicu zamyka i przywraca fokus; przy szkicu odrzucenie potwierdzenia zachowuje tekst i dialog | do odbioru | do odbioru |
| Sieć i powiększenie | Offline nie usuwa szkicu; po powrocie brak przeskoku fokusu; 200%/390px bez ukrycia istotnych kontrolek | do odbioru | do odbioru |

Osobno należy wykonać Safari i używaną technologię asystującą. Ręczny odbiór
jest obecnie NIEODBYTY; nie wolno na podstawie testu developerskiego ustawić Done.
False positive wymaga konkretnego ID/zakresu, uzasadnienia, właściciela i daty
wygaśnięcia w osobnym przeglądanym PR. Obecnie brak wyjątków.

Retest CI ujawnił także zbyt niski kontrast świeżego statusu Postój na jasnym tle.
Przyczyną różnicy local/CI były stare czasy pomiaru w zachowywanej lokalnej bazie
E2E. Reset-case odtwarza teraz świeży pomiar, a axe sprawdza realne odpowiedzi
API kolejno dla stopped/moving/offline/unknown. Poprawiono wspólne jasne tokeny
muted/success/warning zamiast pomijać regułę kontrastu.
