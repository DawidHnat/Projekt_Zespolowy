# SCRUM-32 — alerty i formularze reguł MVP

Widok `#alerts` pokazuje rzeczywiste alerty dziennego dystansu z API SCRUM-31:
pojazd, polski dzień, wartość, zapisany próg i odczyt własnego konta. Filtr
Wszystkie/Nieprzeczytane/Przeczytane i wspólna paginacja działają na serwerze.
Odczyt nie oznacza wykonania sprawy. Dane wiersza zawsze opisują niepełne
pokrycie dnia pomiarami. Równość progu i duplikaty nadal obsługuje backend.

Admin/editor tworzy, edytuje i wyłącza regułę dla floty albo aktywnego pojazdu.
Wybór pojazdu ma wyszukiwanie i paginację, obejmuje także auta bez GPS.
Viewer czyta reguły i zapisuje jedynie własny odczyt. Błąd zapisu nie czyści
formularza i nie symuluje sukcesu. Nieudane potwierdzenie odczytu wymaga
sprawdzenia bieżącego stanu; po błędzie sieci serwer mógł już przyjąć zapis.

Pulpit wykorzystuje istniejący widget `activity`: rzeczywista liczba
nieprzeczytanych, maksymalnie trzy najnowsze zdarzenia i przejście do pełnej
listy. Nie zmieniono trwałych ID układu. Polling współdzieli zasady SCRUM-98:
pauza poza widoczną/online kartą, anulowanie i backoff bez nakładania żądań.

Listy API otrzymały opcjonalne `vehicle_name` i `license_plate` pobierane
przez JOIN w zapytaniu strony, bez dodatkowego odczytu na każdy wiersz.
Kanoniczny kontrakt i wygenerowane typy zostały uzupełnione. Nazwy są bieżące;
dystans, próg i dzień pozostają historycznym dowodem samego alertu.

## Sprawdzenie

- Backend: Ruff i pytest z izolowanym PostgreSQL; zgodność kanonicznego
  kontraktu, prywatność odczytu, zakres źródła, zachowanie starego alertu
  po zmianie/wyłączeniu reguły i dezaktywacji pojazdu.
- Frontend: `npm test`, `npm run build`, `npm run test:e2e`.
- `e2e/alerts.spec.ts`: trwałość odczytu po reload, drugi użytkownik,
  filtr, druga strona, 503 zapisu i poprawne ponowienie, stan pusty,
  reguła floty/pojazdu, zachowany szkic po 503, wyłączenie reguły,
  klawiatura/focus i axe w obu motywach, desktop/390 px.
- Fixtures działają wyłącznie po jawnym opt-in na lokalnej bazie
  `fleet_flow_test_e2e`. Żadne próbki nie są dodawane do produktu.

Niezależny QA SCRUM-33 powinien sprawdzić dodatkowo Safari, równość progu,
brak duplikatów po ponownym przeliczeniu i odebrany przyrost na wdrożonym SHA.
Ten PR obejmuje pierwotne MVP. Terminy OC/badań, cztery wspólne stany obsługi,
rozbudowana personalizacja i e-mail są odbierane w SCRUM-69/73.
