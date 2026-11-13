# SCRUM-38 — dashboard i zmiana rozmiaru okna

Powtórna weryfikacja 09.11.2026, baza `main` `5b5fceb`. Pierwotny dashboard
jest w scalonym PR #6, a poprawka poziomego przewijania tabeli w PR #57.
Ten przyrost poprawia responsywność istniejącego dashboardu.

## Odtworzone i poprawione błędy

1. Przy oknie 980 px i wciąż aktywnym profilu desktop minimum prawego
   kafelka rosło ponad jego cztery kolumny. Silnik spychał go poniżej lewego,
   zostawiając duży pusty obszar. Teraz kafelki w tym samym wierszu dzielą
   dostępną szerokość, zachowując minima treści. Dotyczy to również Mapy.
   Wysokości są przeliczane dopiero dla docelowej szerokości. Sama zmiana
   okna nie nadpisuje preferencji; na szerokim ekranie wracają zapisane rozmiary.
2. Po otwarciu menu na telefonie i powiększeniu okna zostawała osłona,
   która przyciemniała i blokowała stronę. Przejście powyżej 760 px zamyka
   menu oraz usuwa osłonę. Ponowne zwężenie nie otwiera menu samoczynnie.

Oba scenariusze nie przeszły na poprzednim kodzie. Logi odtworzenia są
lokalnymi dowodami autora; nie zastępują niezależnego odbioru zespołu.

## Zakres weryfikacji autora

- Model preferencji i układu: 51/51 testów jednostkowych PASS; build i typecheck PASS.
- Pełna regresja przeglądarkowa: 40/40 PASS, obejmująca obecne przepływy
  API i nowy zestaw SCRUM-38, w konfiguracji desktop i mobile.
- Szerokości okna 320–1440 px, w tym granice menu 760/761 px oraz profilu
  siatki 720 px kontenera. Sprawdzenie w obie strony bez przeładowania strony.
- Jasny/Szkło i Ciemny/Klasyczny, tryb zwykły i edycja: brak nakładania
  kafelków, poziomego przewijania dokumentu i ucięcia treści statycznej lub
  pierwszego wiersza tabeli. Szeroka tabela przewija się we własnym kontenerze.
- Rzeczywiste gesty myszy: przeciąganie i rozciąganie, zmiana okna podczas
  gestu oraz późniejsza edycja klawiaturą. Mechanizm RGL i grupowanie
  pomiarów pozostały bez zmian; nie wykonywano pomiaru liczby klatek.
- Niezależne szkice desktop/compact: zmiana wysokości, zapis, odświeżenie,
  brak zmiany osobnego układu Mapy. Ukrycie kafelka i Anuluj przywracają widok.
- Motyw systemowy reaguje na zmianę systemu; materiał i akcent przetrwały
  odświeżenie. Wyszukiwanie modułu obsługuje brak wyników i wyczyszczenie.
- Testy sprawdzają brak nieobsłużonych błędów JavaScript, również podczas
  zmian szerokości. Zrzuty generują się w `frontend/test-results/`.

Środowisko testowe: Chromium, lokalny backend oraz izolowana baza
`fleet_flow_test_e2e` z syntetycznymi rekordami. Połączenia zewnętrzne są
blokowane; nie testowano żywego renderera Mapbox ani WEBFLEET. Moduły
planowane pozostały pustymi stanami, bez dodawania danych demonstracyjnych.

## Niezależny odbiór przed Gotowe

Review frontendu: drugi developer, zgodnie z CODEOWNERS — Jakub Nazarewicz.
QA: Marcel Głowacki, z retestem widoku w SCRUM-40.

1. Na szerokim ekranie otwórz Pulpit. Zmniejszaj i powiększaj okno, zwłaszcza
   w pobliżu 980, 971, 760, 755 i 320 px. Nie może być nakładania ani pustych
   „schodków”, gdy oba sąsiednie kafelki mieszczą się w jednym wierszu.
2. Otwórz menu na telefonie, powiększ okno, ponownie zwęź. Strona ma pozostać
   dostępna, a menu zamknięte. Sprawdź również Escape i wybór sekcji.
3. W edytorze użyj narożnika, przeciągania, strzałek, Shift + strzałek oraz
   suwaków i presetów w dialogu. Zmień okno podczas gestu. Edytor nadal ma działać.
4. Zapisz odmienne układy telefonu i komputera. Sprawdź odświeżenie, Anuluj,
   ukrywanie i ponowne włączanie modułów. Sprawdź również dedykowaną Mapę.
5. Sprawdź oba materiały i motywy, klawiaturę, fokus dialogów i Escape oraz
   ograniczony ruch/przezroczystość. Obejrzyj pusty stan i pierwszy rekord
   przy najniższym dopuszczalnym rozmiarze kafelka.

Zielone testy autora wymagają jeszcze zielonego CI ostatniego commita,
niezależnego review i QA, scalenia przez PR oraz retestu wdrożonej wersji.
Do tego czasu SCRUM-38 pozostaje W trakcie weryfikacji.
