# KSeF Panel

Prosta aplikacja desktopowa do zarządzania fakturami z Krajowego Systemu e-Faktur (KSeF) dla małej firmy.

## Funkcje

- **Dashboard** - podgląd statystyk, szybkie akcje
- **Przegląd faktur (tryb Tinder)** - przeglądaj faktury jedna po drugiej: akceptuj / odrzuć / oznacz do sprawdzenia
- **Lista faktur** - tabela z filtrami, wyszukiwaniem i akcjami grupowymi
- **Drukowanie** - wybór drukarki, druk pojedynczy i masowy (wszystkie na raz)
- **Statystyki** - podsumowanie miesięczne, wykresy przychodów vs kosztów, top kontrahenci
- **Eksport CSV** - eksport faktur do pliku CSV

## Wymagania

- Python 3.10+
- Windows 10/11 (do drukowania i pakowania EXE)

## Instalacja developerska

```bash
pip install -r requirements.txt
python main.py
```

## Budowanie EXE

```bash
build.bat
```

Wynik: folder `KSeFPanel_Setup/` gotowy do skopiowania na pendrive.

## Instalacja na docelowym komputerze

1. Otwórz `config.json` Notatnikiem, wklej token KSeF i NIP
2. Uruchom `INSTALUJ.bat` jako administrator
3. Na pulpicie pojawi się skrót "KSeF Panel"

## Konfiguracja

Plik `config.json`:

```json
{
    "ksef_token": "twoj-token-ksef",
    "nip": "1234567890",
    "environment": "prod",
    "default_printer": "",
    "auto_fetch_on_start": true
}
```

| Pole | Opis |
|------|------|
| `ksef_token` | Token autoryzacyjny z ksef.podatki.gov.pl |
| `nip` | NIP firmy |
| `environment` | `prod` (produkcja), `demo` (testowe), `test` |
| `default_printer` | Nazwa drukarki (puste = domyślna systemowa) |
| `auto_fetch_on_start` | Automatyczne pobieranie faktur przy starcie |

## Stack technologiczny

- Python + Flask (backend API)
- PyWebView (okno desktopowe)
- TailwindCSS + Chart.js (frontend)
- SQLite (lokalna baza danych)
- PyInstaller (pakowanie do EXE)

## Licencja

Projekt do użytku wewnętrznego.
