# SCRUM-58 — model zagrożeń uploadu dokumentów i zdjęcia pojazdu oraz polityka przechowywania

Dokument określa model zagrożeń, zastosowane kontrole techniczne i warunki wdrożenia operacyjnego dla mechanizmu plików pojazdu w `SCRUM-58` (story `SCRUM-57`, epik `SCRUM-93`, powiązania `SCRUM-59`, `SCRUM-60`, `SCRUM-84`, `SCRUM-94`).

## 1. Zakres wspólnego mechanizmu plików

- Jeden wspólny magazyn prywatny (`PrivateAttachmentStore`) i jedna tabela metadanych (`vehicle_attachments`) obsługują:
  - skany badania technicznego (`kind="inspection"`, do 3 plików na pojazd, formaty `PDF`, `JPG`, `PNG`, do 10 MB),
  - skany polisy ubezpieczeniowej (`kind="insurance"`, do 3 plików na pojazd, formaty `PDF`, `JPG`, `PNG`, do 10 MB),
  - wspólne zdjęcie pojazdu (`kind="vehicle_photo"`, maksymalnie 1 aktualne zdjęcie na trwałe UUID pojazdu, formaty `JPG`, `PNG`, `WebP`, do 10 MB na wejściu, limit 40 MP i maksymalny bok 1024 px; `PDF` jest odrzucany).
- Terminy `inspection_due_on` oraz `insurance_due_on` w tabeli `vehicles` stanowią jedyne źródło tych dat w całej aplikacji i nie są nadpisywane przez synchronizację WEBFLEET.

## 2. Analiza zagrożeń według formatów i powierzchni ataku

| Obszar / format | Zagrożenie | Kontrola w kodzie (`backend/app/modules/fleet/documents.py`) |
| --- | --- | --- |
| Nazwa pliku i ścieżka | Path traversal (`../`), separatory `/`/`\`, znaki sterujące, ukryte pliki `.`, nadmierna długość | Odrzucenie niedozwolonych ścieżek (`422 INVALID_FILENAME`). Zapis na dysku używa wyłącznie losowego 32-znakowego klucza hex (`uuid4().hex`) poza webrootem. |
| Spoofing rozszerzenia i MIME | Plik wykonywalny, HTML/SVG lub inny format przesłany jako `.pdf`/`.jpg`/`.png` albo niezgodny `Content-Type` | Niezależna kontrola rozszerzenia, opcjonalnego `Content-Type` oraz rzeczywistych sygnatur binarnych (magic bytes i pełny rozbiór struktury kontenera). |
| Strumień HTTP i pamięć | Wyczerpanie pamięci/dysku dużym strumieniem lub wieloma plikami | Czytanie strumieniowe z twardym limitem bajtów przed buforowaniem (`UPLOAD_MAX_FILE_BYTES = 10 MB` -> `413 FILE_TOO_LARGE`) oraz limit 3 plików na rodzaj dokumentu (`409 DOCUMENT_LIMIT_REACHED`) i 1 zdjęcia pojazdu. |
| `PDF` (wyłącznie skany dokumentów) | Aktywna zawartość (`/JavaScript`, `/JS`, `/Launch`, `/OpenAction`, `/AA`, `/EmbeddedFiles`, `/RichMedia`, `/XFA`, `/SubmitForm`, `javascript:`), również zaciemniona hexem `#xx` lub ukryta w strumieniu `FlateDecode`; bomba dekompresji | Weryfikacja nagłówka `%PDF-1.`/`%PDF-2.`, obiektów i `%%EOF`, dekodowanie sekwencji `#xx`, limitowana dekompresja `FlateDecode` (`<= 2x limit`) oraz odrzucenie aktywnych tokenów (`422 UNSAFE_FILE_CONTENT`). Pobranie wymusza `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff` oraz `Content-Security-Policy: default-src 'none'; sandbox`. |
| `PNG` (skany i zdjęcie pojazdu) | Uszkodzone chunki, manipulacja CRC, bomba dekompresji `IDAT` (pixel/zlib bomb), wyciek metadanych `eXIf`/`tEXt`/`iTXt`/`zTXt` | Weryfikacja podpisu, CRC32 każdego chunku, wymiarów `IHDR` (`<= 40 MP`, `<= 10 000 px`), limitowana dekompresja `IDAT` potwierdzająca dekodowalność linii obrazu, usunięcie chunków metadanych oraz przeskalowanie 8-bitowych zdjęć pojazdu do boku `<= 1024 px`. |
| `JPG` / `JPEG` (skany i zdjęcie pojazdu) | Brak pełnej struktury (`SOF`/`DQT`/`SOS`/`EOI`), nadmierne wymiary pikseli, wyciek lokalizacji GPS i danych urządzenia w `APP1` (`EXIF`/`XMP`) lub `APP13` (`IPTC`) | Walidacja markerów JPEG, limitu `<= 40 MP` (oraz `<= 1024 px` dla zdjęcia pojazdu) i bezstratne wycięcie wszystkich segmentów `APP1`–`APP15` oraz `COM` przed zapisem. |
| `WebP` (wyłącznie zdjęcie pojazdu) | Niezgodny kontener `RIFF`/`WEBP`, brak strumienia `VP8`/`VP8L`, wyciek chunków `EXIF`/`XMP `, nadmierny rozmiar | Walidacja kontenera `RIFF` i nagłówków ramki `VP8`/`VP8L`/`VP8X`, limit `<= 40 MP` i `<= 1024 px`, wycięcie chunków `EXIF` i `XMP ` oraz wyzerowanie flag metadanych. |
| Malware i kwarantanna | Udostępnienie zainfekowanego pliku innemu użytkownikowi lub publikacja przy awarii skanera | **Fail-closed:** każdy plik trafia najpierw do `quarantine/<storage_key>` (`0600`). Publikacja do `clean/<storage_key>` następuje wyłącznie przy werdykcie `clean`. Domyślny produkcyjny adapter `UnconfiguredMalwareScanner` zwraca `scanner_unavailable` (`SCANNER_NOT_CONFIGURED`) do czasu zatwierdzenia usługi skanującej i jej kosztu przez właściciela. Żaden plik o statusie `quarantined`, `scanner_unavailable` ani `rejected` nie może zostać pobrany (`409 FILE_NOT_AVAILABLE`). |
| Podmiana pliku | Utrata wcześniejszego dokumentu lub zdjęcia przy błędzie walidacji, skanera lub zapisu | Walidacja i skanowanie kandydata odbywają się przed podmianą rekordu. Przy błędzie (`413`/`422`/`409`/`503`) poprzedni plik `clean` oraz jego metadane i daty pozostają nienaruszone. |
| IDOR i kontrola ról | Odczyt, podmiana lub usunięcie dokumentu/zdjęcia obcego pojazdu przez zmianę UUID; zapis przez `viewer` | Każda operacja weryfikuje sesję oraz przynależność `Vehicle.source_account` (`404 NOT_FOUND` dla obcego UUID lub niezgodnej pary `(vehicle_id, document_id)`). Zapisy wymagają `admin`/`editor` i zaufanego `Origin`; `viewer` posiada wyłącznie odczyt. Pliki nie mają publicznych URL i nigdy nie trafiają do logów ani WEBFLEET. |

## 3. Przechowywanie lokalne, prywatność (`SCRUM-94`) i zakres kopii (`SCRUM-84`)

- **Magazyn lokalny:** katalog wskazany w `FLEET_FLOW_UPLOAD_DIR` znajduje się poza repozytorium i poza webrootem serwera HTTP, z uprawnieniami `0700` dla katalogów `quarantine/` i `clean/` oraz `0600` dla plików. Aplikacja blokuje użycie dowiązań symbolicznych oraz katalogów kodu/frontendu.
- **Szyfrowanie, retencja i usuwanie (`SCRUM-94`):** usunięcie dokumentu lub zdjęcia (`DELETE`) usuwa rekord w PostgreSQL oraz fizyczny plik z dysku po zatwierdzeniu transakcji. Szyfrowanie wolumenu w spoczynku, okres retencji po zakończeniu eksploatacji pojazdu oraz procedury DSAR/usuwania podlegają decyzjom administratora danych w `SCRUM-94` / `SCRUM-109` / `SCRUM-111`.
- **Spójny backup i odtworzenie (`SCRUM-84`, bez zmiany VPS w `SCRUM-58`):**
  - Daty `inspection_due_on` i `insurance_due_on` oraz tabela `vehicle_attachments` (w tym `sha256` i `storage_key`) wchodzą w skład zrzutu `pg_dump -Fc` PostgreSQL.
  - Przed aktywacją uploadu na VPS w zadaniu infrastruktury `SCRUM-84` należy włączyć katalog `clean/` z `FLEET_FLOW_UPLOAD_DIR` do tego samego szyfrowanego snapshotu `restic` (lub spójnego manifestu z weryfikacją `sha256` względem `vehicle_attachments`), tak aby odtworzenie bazy i plików na nowym hoście zachowało pełną zgodność referencyjną i brak osieroconych rekordów. Katalog `quarantine/` nie podlega publikacji po odtworzeniu.

## 4. Decyzje wymagane przed aktywacją produkcyjną

- Właściciel produktu / bezpieczeństwa zatwierdza docelowy silnik skanowania malware (np. lokalny daemon ClamAV w izolowanym kontenerze albo zewnętrzny sandbox) oraz jego koszt i zasoby przed zmianą domyślnego trybu `UnconfiguredMalwareScanner` (`BLOCKED` na decyzję właściciela — kod pozostaje bezpiecznie zamknięty fail-closed).
