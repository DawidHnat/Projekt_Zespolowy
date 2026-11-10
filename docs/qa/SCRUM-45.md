# SCRUM-45 — zdjęcia i kafelki pojazdów

Weryfikacja 10.11.2026, baza `main` `5b5fceb`. Podstawa personalizacji jest
w scalonym PR #16, a edycja zbiorowa i paginacja w PR #17.

## Poprawka po odtworzeniu błędu

1. Na komputerze zapisz rozmiar Duże: 480 × 500 px.
2. Zwęź okno do 390 px. Kafelek ma widoczne 364 px, ale nadal zapisane 480 px.
3. Rozciągnij narożnik pionowo o 50 px, zapisz i wróć do dużego okna.

Przed poprawką zapisywała się szerokość 364 px. Teraz pozostaje 480 px,
a wysokość wynosi 550 px. Niezmieniana oś zachowuje zapisany wymiar, także
przy drobnym ruchu bocznym poniżej 5 px. Celowe poziome rozciąganie nadal
rozpoczyna się od widocznej krawędzi. Nie zmieniono formatu preferencji.

## Wyniki autora

- `npm test`: 50/50 PASS; typecheck i build PASS.
- Pełna regresja Playwright: 36/36 PASS, desktop i mobile. Końcowy zestaw
  personalizacji po uzupełnieniu formatów i asercji sieci: 10/10 PASS.
- Przed poprawką test mobilnego rozciągania na komputerowym Chromium nie
  przeszedł: oczekiwane 480 px, otrzymane 364 px. Zdjęcia już wtedy działały.
- JPG, PNG i WebP są odczytywane i ponownie kodowane; obraz 1200 × 600 jest
  zapisywany jako WebP 1024 × 512. Znacznik danych testowych dopisany do
  oryginału nie występuje w zapisanym obrazie.
- Dodanie, podmiana, usunięcie i odświeżenie zdjęcia działają. Zdjęcie jest
  wspólne dla kafelka i panelu pojazdu. Testy nie wykazały wysyłki obrazów
  do API. Drugie konto nie widzi zdjęcia pierwszego; ponowne logowanie
  właściciela przywraca jego zdjęcie.
- Nieobsługiwany typ, uszkodzony plik i plik ponad 10 MB pokazują błąd bez
  utraty poprzedniego zdjęcia. Niedostępny IndexedDB pozwala używać obrazu
  w sesji z ostrzeżeniem; po odzyskaniu magazynu usunięcie działa.
- Minimum 280 × 420 mieści dane i stopkę, także przy oknie 320 px.
  Sprawdzono Zapisz/Anuluj, pionowy i poziomy gest, zachowanie szkicu po
  przejściu do Ustawień, natychmiastowy zapis motywu/materiału oraz odświeżenie.
- Obejrzano zrzuty minimum w ciemnym/klasycznym widoku i błędu zdjęcia
  w jasnym/szklanym widoku. Testy generują je w `frontend/test-results/`.

Środowisko: lokalny backend i izolowana baza `fleet_flow_test_e2e`, wyłącznie
syntetyczne rekordy oraz jednolite obrazy testowe. Żadne dane próbne nie
trafiły do produktu. Połączenia zewnętrzne są blokowane. Modele i kod
znaczników nadal używają osobnych pojazdów i tego samego źródła zdjęć;
żywy renderer Mapbox, znacznik ze zdjęciem i wybór nakładających się pozycji
wymagają niezależnego sprawdzenia w docelowej aplikacji.

## Odbiór przed Gotowe

Review: Jakub Nazarewicz. QA: Marcel Głowacki, zgodnie ze SCRUM-45 / SCRUM-23.

1. Odtwórz kroki mobilnego rozciągania z początku dokumentu, również myszą
   i dotykiem. Sprawdź pion, poziom, klawiaturę, presety, Zapisz i Anuluj.
2. Dodaj własny niesensytywny obraz, odśwież, zastąp i usuń. Zweryfikuj
   brak obrazu na drugim koncie i informację o lokalnym zapisie.
3. Sprawdź to samo zdjęcie na znaczniku Mapbox i kafelku, wybór pojazdu,
   status oraz nakładające się pozycje bez grupowania przy oddalaniu.
4. Sprawdź Ustawienia, zachowanie szkicu, motyw i mały ekran. Błędy pliku
   oraz niedostępnego magazynu muszą być czytelne.

Wyniki autora nie zastępują niezależnego review i QA. Przed zamknięciem
zadania wymagane są zielone CI ostatniego commita, scalenie przez PR
i odbiór wdrożonej wersji.
