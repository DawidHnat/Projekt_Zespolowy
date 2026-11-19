# SCRUM-94/113 — arkusz potwierdzonych ustaleń i pozostałych decyzji

Wersja 3, **19.11.2026**. Zapis: **agent Codex na polecenie Jakuba Czai**.
Kod odniesienia `cb634da0ece8cd93424bfc16a5185cf817a0cbb1`; źródło: odpowiedzi
PO, pola 1–6. Dane identyfikujące firmę i właściciela są w lokalnym rejestrze
poza Git/Jira. Bez odczytu rekordów klientów, zmian VPS i żywego API.
[Zapis ustaleń w SCRUM-113](https://fleet-flow.atlassian.net/browse/SCRUM-113?focusedCommentId=10362).
[Inwentarz](inventory.v1.json), `operating_context` i `decision_refresh`;
[kryteria 94](SCRUM-94-acceptance.md).

## Potwierdzone przez Jakuba

- **Rzeczywiste dane jednej firmy, jedno API WEBFLEET**, wyłącznie projekt zespołowy; bez rozbudowy dla innych firm. Koryguje to wcześniejsze założenie syntetycznego demo. Testy agenta nadal były izolowane i syntetyczne.
- Podmiot i właściciel wskazani lokalnie. Jakub odpowiada za projekt i zarządza tym obszarem w firmie. Według jego relacji właściciel udzielił **ustnej zgody 2 października** (rok 2026 z kontekstu).
- **Dostęp całej czwórki**: Jakub Czaja, Dawid Hnat, Jakub Nazarewicz, Marcel Głowacki. **Pokaz prowadzącemu dozwolony**; publiczne udostępnianie rzeczywistych danych nieustalone.
- Użyczenie **do końca lutego 2027 r.** (rok z kontekstu semestru). Projekt nie będzie kontynuowany; wszystkie dane zgromadzone dla projektu — VPS, eksporty, kopie lokalne — mają zostać usunięte. To plan, nie wykonanie usunięcia.
- **Nie było konsultacji DPO/prawnej**; nie przedstawiono wyniku screeningu DPIA wymaganego przez kryteria zadania.

**0 kompletnych APPROVED P01–P18.** Istnieją powyższe częściowe ustalenia;
nie przedstawiamy już administratora, celu, odbiorców ani terminu jako całkowicie
nieznanych. Zapis relacji PO nie uzupełnia nieprzekazanych procedur i konsultacji.

| Decyzje | Co ustalono / co nadal pozostaje | Następny odpowiedzialny krok |
| --- | --- | --- |
| P01/P02 — podmiot, cel i pola | Właściciel wskazany lokalnie, użyczenie do projektu jednej firmy; pozostałe role dostawców, umowy, podstawa i minimalne D01–D22 niepotwierdzone | **Jakub Czaja** koordynuje z właścicielem i konsultującym; dane identyfikujące poza Git/Jira |
| P03/P07 — odbiorcy i role | Dostęp czwórki i jedna firma potwierdzone; szczegółowe uprawnienia GPS/historii/eksportu/admin IT i mapowanie ról nadal otwarte | **Jakub** z właścicielem potwierdza macierz; **Dawid** mapowanie techniczne |
| P04/P06/P15 — retencja i usuwanie | Koniec użyczenia i plan usunięcia danych projektu potwierdzone; okresy/wyjątki kategorii, logi, magazyny przeglądarki, wykonanie i dowód nadal otwarte | **Jakub** koordynuje decyzje, **Dawid** przygotowuje wykonanie właściwego zakresu 109/111 po zatwierdzeniu |
| P08/P09/P16 — prywatne użycie, informowanie i minimalne pliki | Nie przekazano odrębnych ustaleń tych obszarów; zgoda na API nie jest protokołem tych decyzji | **Jakub** z właścicielem i konsultującym; **Dawid** dane techniczne |
| P05/P17 — eksport osoby | Weryfikacja osoby, autoryzacja, zakres i wygaśnięcie pliku niepotwierdzone | **Jakub** koordynuje zatwierdzenie, backend/QA wykonuje 110 z właściwym wejściem |
| P10 — screening DPIA | Potwierdzono brak konsultacji, nie wynik screeningu | **Jakub** wskazuje konsultującego i uzyskuje wynik; właściciel odbiera |
| P13 — backup/restore | Storage/koszt/RPO/RTO/alarmy i pełny recovery **DEFERRED do SCRUM-84/S5**; skutki usuwania po restore niezatwierdzone | **Dawid/Jakub** operacyjnie w końcowym S5; polityka danych z właścicielem |
| P11/P12/P14/P18 — incydent, dostawcy i logi | Kontakty proceduralne, SDK/telemetria, umowy i retencja logów niepotwierdzone | **Dawid** dane techniczne, **Jakub** decyzje właściciela i konsultację |

**Pełny odbiór 94/113: BLOCKED** do pozostałych kryteriów. Potwierdzone fakty
są zapisane; nie uruchomiono retencji, kasowania, żywego API/SMTP ani operacji VPS.
Kryteriów zadania nie zmieniono dla wyniku sprintu.
