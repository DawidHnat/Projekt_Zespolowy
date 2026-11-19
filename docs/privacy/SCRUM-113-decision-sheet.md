# SCRUM-94/113 — arkusz decyzji do zatwierdzenia

Wersja 2, 19.11.2026. Przygotował **agent Codex na polecenie Jakuba Czai**.
Kod: `cb634da0ece8cd93424bfc16a5185cf817a0cbb1`; środowisko: izolowany
checkout, bez odczytu rekordów klientów. Dowód techniczny:
[istniejący inwentarz, wersja 2](inventory.v1.json), `technical_refresh`.
Porównanie wszystkich **15 tabel i pól: PASS**; niezależny review aktualizacji
oczekuje. [Kryteria SCRUM-94](SCRUM-94-acceptance.md).

**Decyzja PO z 19.11: jedna firma/przedsiębiorca i jedno API WEBFLEET;
rozbudowa dla innych firm jest poza projektem.** To zatwierdzenie zakresu
produktu, nie wskazanie administratora ani zgoda na rzeczywiste dane.
Nie przekazano nowej decyzji dopuszczającej dane rzeczywistej firmy;
ostatnia deklaracja syntetycznego demo pozostaje źródłem zakresu demonstracji.
Nie jest to audyt zawartości VPS.

**P01–P18: 0 zatwierdzonych, 18 BLOCKED.** Żaden merge dokumentacji,
review techniczny ani decyzja PO o jednej firmie nie wypełnia pól
`approved_by`/`approved_at` właściciela danych. Szczegółowe pytania i wymagany
dowód każdego P są zachowane w `policy_decisions` istniejącego JSON.

| Decyzje | Co dokładnie zatwierdzić / aktualny fakt techniczny | Kto ma podjąć następny krok |
| --- | --- | --- |
| P01/P02 — administrator, procesorzy, cel, pola | Wskazać rzeczywisty podmiot i osobę uprawnioną; role WEBFLEET/Mapbox/SMTP/VPS/GitHub/Jira, cel i minimalne pola D01–D22. Demo nie wymaga wymyślenia firmy. | **Jakub Czaja** wskazuje imiennie uprawnionego właściciela i konsultującego; wskazany administrator zatwierdza. Obecnie nazwiska/podmiotu brak. |
| P03/P07 — role i granica firmy | Jedna firma jest zatwierdzonym zakresem PO. Osobno: kto widzi GPS/historię/kontakty, kto edytuje, administracja IT; admin/editor/viewer i jedna konfiguracja źródła nie zatwierdzają celu dostępu. | **Jakub Czaja** uzyskuje decyzję administratora; **Dawid Hnat** potwierdza mapowanie ról. |
| P04 — retencja/wyjątki | Okres lub zdarzenie początku/końca per kategoria, hold/wyjątki dla DB, logów, plików, urządzeń i kopii. Preferencje konta są już w DB i dumpach. Żaden okres nie został ustalony. | Administrator wskazany przez **Jakuba Czaję** zatwierdza; **Dawid Hnat** ocenia wykonanie SCRUM-109. |
| P08 — prywatne użycie | Cel/godziny/odbiorcy GPS, prywatne przejazdy i niejednoznaczne przydziały. Obecność pola lub API nie rozstrzyga dopuszczalnego użycia. | **Jakub Czaja** uzyskuje decyzję administratora i kierownika docelowej floty. |
| P09/P15/P16 — informowanie i lokalne dane | Wersjonowana informacja dla osób; instrukcja wolnego tekstu/obrazów, współdzielonego urządzenia i przyszłych dokumentów/audytu. Logout nie wymazuje localStorage/IndexedDB. | Administrator zatwierdza z konsultującym; **Jakub Czaja** koordynuje, **Dawid Hnat** wyznacza minimalne pola przyszłych plików. |
| P05/P17 — DSAR/eksport | Weryfikacja osoby i autoryzacja, zakres oraz cudze dane, bezpieczne wydanie i wygaśnięcie pliku; przypisania kierowców z #110 nie są jeszcze w main. | Administrator wskazany przez **Jakuba Czaję** zatwierdza; backend/QA wykonują SCRUM-110 dopiero z tym wejściem. |
| P06/P13 — usunięcie, backup/restore | Wyjątki, minimalny ślad i ponowne zastosowanie usunięcia po restore/imporcie. **Operacyjne storage/koszt/RPO/RTO i pełny off-site recovery są DEFERRED do SCRUM-84/S5**, bez ponownego uzgadniania dziś. Obecne kopie/rollback SCRUM-18 mają osobny zakres. | Administrator zatwierdza skutki dla danych; **Dawid Hnat i Jakub Czaja** realizują operacyjny P13 w końcowym S5. Odroczenie nie oznacza zatwierdzonej polityki ani dostarczonego backupu. |
| P10 — screening DPIA | Wskazany kontekst, osoby, pola GPS/czas/prędkość/adres, skala i zastosowanie; udokumentowany wynik, uzasadnienie i dalsze kroki. Dla przykładowej firmy nie wpisujemy fikcyjnej oceny. | **Jakub Czaja** wskazuje właściwego DPO/prawnika i administratora; konsultujący wykonuje screening, administrator odbiera wynik. Brak tożsamości i wyniku. |
| P11/P12/P14/P18 — incydent i dostawcy | Odpowiedzialne kontakty, zabezpieczenie dowodów, zakres SDK/telemetrii, umowy/transfery, logi/rotacja i dostęp do narzędzi. Nie wywodzić tego z samej domeny hosta. | **Dawid Hnat** dostarcza techniczne ustalenia, **Jakub Czaja** uzyskuje kontakty/decyzję administratora i koordynuje incydent. |

Zatwierdzający przekazuje dla każdego P: **decyzję i jej zakres, konkretną
osobę i umocowanie, wersję/datę, bezpieczny odnośnik do dowodu, wynik
APPROVED albo uzasadnione BLOCKED oraz rzeczywiście uzgodniony termin**.
Nazwisk, terminów i akceptacji nie uzupełnia agent za właściciela.

**Odbiór całych SCRUM-94/113: BLOCKED** do wymaganych rzeczywistych decyzji
i screeningu. Techniczny spis jest uaktualniony; nie uruchamia to retencji,
usuwania, wielofirmowości ani przetwarzania danych rzeczywistej firmy.
