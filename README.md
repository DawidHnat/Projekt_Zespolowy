# Fleet-Flow

Fleet-Flow to aplikacja webowa wspierająca zarządzanie flotą pojazdów, wykorzystująca dane z systemu WEBFLEET.connect.

Celem projektu jest stworzenie prostszego, czytelniejszego i bardziej funkcjonalnego interfejsu do najczęściej wykorzystywanych danych flotowych. Aplikacja ma umożliwiać szybki dostęp do informacji potrzebnych w codziennym zarządzaniu flotą oraz ograniczyć konieczność korzystania z dodatkowych narzędzi do analizowania, filtrowania i przygotowywania danych.

## Problem

System Webfleet udostępnia dużą ilość danych dotyczących pojazdów i ich użytkowania, jednak dla zwykłego użytkownika dostęp do części informacji jest mało intuicyjny.

Najważniejsze problemy, które chcemy rozwiązać:

- skomplikowany i mało czytelny interfejs;
- trudny dostęp do często wykorzystywanych danych;
- ograniczone możliwości wygodnego filtrowania i sortowania informacji;
- konieczność przechodzenia między wieloma widokami w celu uzyskania potrzebnych danych;
- ograniczone możliwości dostosowania interfejsu do potrzeb użytkownika;
- niewygodne przygotowywanie danych dotyczących historii przejazdów;
- mało praktyczna forma części raportów generowanych bezpośrednio w Webfleet.

Fleet-Flow ma uprościć pracę z danymi flotowymi poprzez prezentowanie najważniejszych informacji w czytelnych i łatwo dostępnych widokach.

Aplikacja ma również ułatwić pracę z historią przejazdów. Użytkownik będzie mógł przypisywać do przejazdów ich cel oraz dodatkowy opis, co pomoże w przygotowywaniu ewidencji przebiegu pojazdów oraz dokumentacji wykorzystywanej do celów rozliczeniowych i podatkowych.

Fleet-Flow nie zastępuje systemu Webfleet, lecz wykorzystuje jego dane i przedstawia je w prostszej oraz bardziej dopasowanej do codziennej pracy formie.

## Użytkownik

Głównym użytkownikiem aplikacji jest **kierownik floty**.

Potrzebuje on przede wszystkim szybkiego dostępu do informacji pozwalających:

- sprawdzić liczbę kilometrów przejechanych przez pojazd w wybranym okresie;
- kontrolować aktualne położenie i status pojazdów;
- sprawdzić, czy pojazdy są użytkowane zgodnie z przeznaczeniem;
- analizować historię przejazdów;
- kontrolować czas pracy i sposób użytkowania pojazdów;
- analizować ekonomiczność użytkowania floty;
- uzupełniać cele oraz opisy przejazdów;
- przygotowywać dane potrzebne do ewidencji przebiegu pojazdów;
- szybciej przygotowywać zestawienia i raporty.

## Trzy najważniejsze funkcje

### 1. Lista i mapa floty

Aplikacja umożliwi wyświetlanie czytelnej listy pojazdów oraz ich aktualnego położenia na wspólnej mapie.

Podstawowe informacje o pojeździe będą obejmować między innymi:

- nazwę lub numer rejestracyjny;
- pozycję GPS;
- aktualny status;
- prędkość;
- przebieg.

Pojazdy będą oznaczone na mapie w sposób pozwalający na ich łatwe rozpoznanie również przy większym oddaleniu widoku.

Lista pojazdów ma być czytelna, łatwa do filtrowania oraz dostępna bez konieczności przechodzenia pomiędzy wieloma ekranami.

### 2. Szczegóły, historia pojazdu i ewidencja przebiegu

Po wybraniu pojazdu użytkownik będzie mógł zobaczyć jego podstawowe dane, historię przejazdów oraz informacje potrzebne do prowadzenia ewidencji przebiegu pojazdu.

Widok ma umożliwiać szybkie sprawdzenie między innymi:

- podstawowych informacji o pojeździe;
- historii tras;
- daty i czasu przejazdu;
- miejsca rozpoczęcia i zakończenia trasy;
- przejechanego dystansu;
- przebiegu pojazdu;
- postojów;
- celu przejazdu;
- dodatkowego opisu przejazdu.

Użytkownik będzie mógł uzupełniać cel i opis przejazdu.

Pozwoli to łatwiej przygotowywać dane wykorzystywane przy tworzeniu ewidencji przebiegu pojazdu oraz dokumentacji potrzebnej do celów rozliczeniowych i podatkowych.

Docelowo aplikacja może również umożliwiać generowanie czytelnego raportu ewidencji przebiegu za wybrany okres.

### 3. Analityka i alerty

Aplikacja będzie prezentować dane potrzebne do analizy wykorzystania i ekonomiczności floty.

Użytkownik będzie mógł korzystać z czytelnych zestawień oraz alertów uruchamianych po spełnieniu określonych warunków.

Przykładowe zastosowania:

- analiza liczby przejechanych kilometrów;
- analiza wykorzystania pojazdów;
- analiza ekonomiczności użytkowania floty;
- porównywanie danych pomiędzy pojazdami;
- wykrywanie nietypowego sposobu użytkowania pojazdu;
- kontrolowanie wybranych parametrów pojazdów;
- informowanie użytkownika o określonych zdarzeniach lub przekroczeniach;
- tworzenie zestawień dla wybranego okresu.

## Zespół i role

| Osoba | Rola lub role |
|---|---|
| Jakub Czaja | Lider / Product Owner, Developer |
| Dawid Hnat | Infrastruktura, Developer |
| Jakub Nazarewicz | Developer |
| Marcel Głowacki | QA |

Jedna osoba może pełnić więcej niż jedną rolę. Każda z czterech wymaganych ról ma przypisanego właściciela.

## Technologie

Planowany stos technologiczny projektu:

- **Frontend:** React + TypeScript
- **Backend:** Python + FastAPI
- **Baza danych:** PostgreSQL
- **Mapa:** Mapbox
- **Integracja danych:** WEBFLEET.connect
- **Repozytorium:** GitHub
- **Zarządzanie projektem:** Jira
- **Środowisko deweloperskie:** VPS z systemem Linux

## Zakres MVP

Pierwsza wersja aplikacji skupia się na trzech głównych obszarach:

1. liście i mapie floty;
2. szczegółach, historii pojazdów i ewidencji przebiegu;
3. analityce i alertach.

W pierwszej wersji najważniejsze jest przygotowanie działającej podstawy aplikacji i integracji z danymi WEBFLEET.connect.

Bardziej rozbudowane raporty, dodatkowe możliwości personalizacji oraz kolejne moduły mogą być rozwijane w dalszych etapach projektu.

## Struktura startowa projektu

Repozytorium zawiera przygotowane katalogi i puste pliki do dalszej pracy.
Aplikacja nie jest jeszcze zaimplementowana i nie da się jej uruchomić.
Kod poszczególnych funkcji będzie powstawał w osobnych zadaniach projektu SCRUM.

- [Podział katalogów](docs/STRUCTURE.md)
- [Zasady współpracy i PR](CONTRIBUTING.md)
- [Instrukcje dla agentów AI](AGENTS.md)

## Serwer deweloperski

Aplikację rozwijamy lokalnie. Wspólny serwer VPS OVHcloud z Ubuntu został
zakupiony. Aktywacja i logowanie SSH nie zostały jeszcze zweryfikowane. Adres
zostanie dodany po sprawdzeniu dostępu, przed oddaniem zadania.

- [Stan serwera i wymagane testy SSH](DEV_SERVER.md)
- [Przygotowanie dostępu czterech osób](infra/vps/README.md)
- [Podział pracy i pierwsze zadania](docs/TASKS.md)
