# Team Contract — Fleet-Flow

Niniejszy dokument określa podstawowe zasady współpracy zespołu realizującego projekt Fleet-Flow.

**Data przyjęcia kontraktu:** 03.10.2026

---

## 1. Kanał komunikacji i czas odpowiedzi

Głównym kanałem bieżącej komunikacji zespołu jest **Discord**.

Dodatkowo zespół może korzystać z **Messengera** do szybkiego kontaktu i pilnych ustaleń.

Przyjmujemy następujący podział narzędzi:

- **Discord / Messenger** — komunikacja bieżąca;
- **Jira** — zadania, backlog, status prac i blokady;
- **GitHub** — kod źródłowy, dokumentacja i Pull Requesty.

### Czas odpowiedzi

Każdy członek zespołu powinien odpowiedzieć:

- w dni robocze — maksymalnie w ciągu **24 godzin**;
- w weekend — maksymalnie w ciągu **48 godzin**;
- w sprawach pilnych — w miarę możliwości w ciągu **8 godzin**.

Jeżeli ktoś przez dłuższy czas nie będzie dostępny, powinien wcześniej poinformować o tym pozostałych członków zespołu.

---

## 2. Dostępność członków między zjazdami

Deklarowana dostępność zespołu:

| Osoba | Dostępność |
|---|---|
| Jakub Czaja | poniedziałek–piątek: 15:00–23:00; niedziela: 9:00–21:00 |
| Dawid Hnat | poniedziałek–piątek: 17:00–00:00; niedziela: 20:00-22:00 |
| Jakub Nazarewicz | poniedziałek–piątek: 15:00–22:00; sobota–niedziela: 9:00–21:00 |
| Marcel Głowacki | poniedziałek–piątek: 17:00–00:00; sobota-niedziela 20:00-22:00 |

Podane godziny oznaczają orientacyjną dostępność do pracy nad projektem i kontaktu z zespołem.

Nie oznacza to obowiązku pozostawania online przez cały wskazany przedział czasowy.

Jeżeli termin wykonania zadania koliduje z dostępnością członka zespołu, powinno to zostać zgłoszone możliwie wcześnie.

---

## 3. Sposób podejmowania decyzji

Decyzje dotyczące projektu podejmujemy wspólnie.

W przypadku decyzji wymagającej głosowania obowiązuje **większość 3 z 4 członków zespołu**.

Drobne decyzje organizacyjne i techniczne, które nie wpływają istotnie na zakres produktu, może podejmować **lider projektu**.

Spory dotyczące zakresu i decyzji technicznych rozstrzygamy zgodnie z [procedurą sporów](#5-spory-i-nierówny-wkład).

Istotne decyzje dotyczące:

- zakresu produktu;
- architektury;
- wykorzystywanych technologii;
- zmiany głównych funkcji;
- terminów kluczowych etapów

powinny zostać zakomunikowane całemu zespołowi.

---

## 4. Postępowanie przy niedowiezionym zadaniu

Jeżeli członek zespołu widzi ryzyko niewykonania zadania w terminie, powinien poinformować o tym zespół **przed upływem terminu**.

W takiej sytuacji:

1. informujemy zespół o problemie;
2. zapisujemy blokadę lub odpowiednią informację w Jirze;
3. określamy przyczynę opóźnienia;
4. ustalamy, czy potrzebna jest pomoc innej osoby;
5. ustalamy nowy realistyczny termin lub dzielimy zadanie na mniejsze części.

Celem jest jak najszybsze usunięcie blokady, a nie szukanie winnego.

### Powtarzające się problemy

Jeżeli ta sama osoba wielokrotnie nie realizuje przydzielonych zadań bez wcześniejszego poinformowania zespołu:

- zespół omawia przyczynę problemu;
- zakres jej zadań może zostać zmniejszony lub zmieniony;
- zadanie może zostać przekazane innej osobie;
- lider może zmienić podział odpowiedzialności w projekcie.

Każda zmiana podziału odpowiedzialności powinna zostać zakomunikowana całemu zespołowi i, jeżeli dotyczy konkretnego zadania, odnotowana w Jirze.

---

## 5. Spory i nierówny wkład

### Spór w Pull Requeście

Po **dwóch dniach roboczych bez uzgodnionego następnego kroku** lub po
**sześciu merytorycznych komentarzach w tym samym wątku bez decyzji**,
zależnie od tego, co nastąpi wcześniej, autor PR-u organizuje krótką rozmowę
na Discordzie w najbliższym dniu roboczym. Do rozmowy zbiera warianty,
ich konsekwencje i odnośniki do przykładów lub wyników testów.
Po rozmowie zapisuje w PR decyzję, uzasadnienie i następny krok.

- O celu, zakresie i kolejności dostarczenia funkcji decyduje **Właściciel Produktu**
  po wysłuchaniu zespołu. Do Jira trafia ustalona zmiana zakresu.
- O rozwiązaniu technicznym decyduje **zespół**. Porównuje warianty według
  kolejności cech: bezpieczeństwo i prywatność, poprawność i integralność danych,
  niezawodność i możliwość cofnięcia zmiany, utrzymywalność i testowalność,
  wydajność, koszt i czas wdrożenia. Gdy warianty różnią się na kilku poziomach,
  pierwszeństwo ma wyższa cecha. Przy braku konsensusu stosujemy głosowanie 3 z 4.

Jeżeli do końca następnego dnia roboczego po rozmowie brakuje rozstrzygnięcia
lub spór zagraża terminowi oddania, lider zgłasza go prowadzącemu przez
uczelniany kanał zajęć. Dołącza link do PR-u i zgłoszenia w Jirze, zwięzły opis
wariantów, wynik rozmowy oraz pytanie, które wymaga rozstrzygnięcia.
Równolegle informuje zespół i zapisuje ustalenie po odpowiedzi.

### Nierówny wkład

Lider zaczyna od rozmowy z zainteresowaną osobą. Ustala z nią, czy przyczyną
jest blokada, potrzeba wsparcia kompetencyjnego, dostępność albo trudność we
współpracy i więzi z zespołem. Uzgadniają odpowiednio zdjęcie blokady,
pracę w parze, zmianę zakresu lub terminu albo sposób kontaktu i włączenia
w pracę zespołu. Przy utrzymującym się problemie stosujemy
[postępowanie przy niedowiezionym zadaniu](#4-postępowanie-przy-niedowiezionym-zadaniu)
i odnotowujemy zmianę odpowiedzialności w Jirze.

---

## 6. Członkowie zespołu i data przyjęcia kontraktu

| Osoba | Login GitHub |
|---|---|
| Jakub Czaja | `jczaja51` |
| Dawid Hnat | `DawidHnat` |
| Jakub Nazarewicz | `jnazarewiczs` |
| Marcel Głowacki | `mglowacki0` |

**Data przyjęcia kontraktu:** 03.10.2026

Kontrakt obowiązuje wszystkich członków zespołu.

Zmiany w kontrakcie mogą być wprowadzane w trakcie projektu po poinformowaniu wszystkich członków zespołu i zaakceptowaniu zmiany przez zespół.
