# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
python app.py
```

**Dependencies** (install via `pip install -r requirements.txt`):
- `PyQt6` — GUI framework
- `pandas` — CSV/Excel reading
- `openpyxl` — Excel generation and styling

## Running Tests

```bash
python -m pytest tests/ -v
```

## Building the Executable

```bash
pip install pyinstaller
pyinstaller sumal_report.spec
```

Output: `dist/SUMAL Report.exe` (single-file, no-console Windows build).

## Architecture

This is a **PyQt6 desktop GUI application** (MVC pattern) for processing Romanian timber transport notices (SUMAL) and generating Excel reports. The company context is "Brat Valms Service Tur S.R.L." (constants in `core/config.py`).

### Layer Overview

- **`core/`** — Business logic, no UI dependencies
  - `models.py` — Dataclass models: `TransportNoticeModel`, `WoodItemModel`, `DepozitDataModel`, Excel mapping models
  - `csv_reader.py` / `excel_reader.py` — Parse input files into models
  - `report_generator.py` — Generates multi-sheet `.xlsx` reports; all values are precomputed in Python and written as static numbers (only the per-sheet TOTAL row uses a SUBTOTAL formula so it follows table filters)
  - `config.py` — `APP_CONFIG` (company identity, tax rate, date formats), `VOLUME_PRECISION`/`PRICE_PRECISION`, `DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE`
  - `enums.py` — `NoticeType`, `GoodType`, `DepositType`, `AppState`, `FolderStatus`, etc.
  - `resources.py` — `APP_RESOURCES`: path resolution for source vs. PyInstaller-frozen runs, stylesheet loading
  - `utils.py` — Small helpers: `normalize_field`, `extract_base_name`, `refresh_style`, `float_to_display_str`
  - `logger.py` — Wraps Python logging; outputs to both console and `logs/sumal_report.log`
  - `sr_error.py` — `SRError(message, title="Eroare")` custom exception for user-facing errors

- **`ui/`** — PyQt6 widgets only; styled via `styles.qss`
  - `main_window.py` — Central window with notice table
  - `deposit_data_window.py` / `deposit_card_widget.py` — Deposit pricing dialog
  - `notice_details_window.py` — Read-only detail viewer
  - `toggle_switch_button.py` — Custom animated toggle switch for prestări marking

- **`controllers/`** — Mediates between `core/` and `ui/`
  - `main_controller.py` — Orchestrates file detection, parsing, validation, report generation
  - `deposit_data_controller.py` — Handles saving/loading user-entered deposit pricing data
  - `notice_details_controller.py` — Formats notice fields for the read-only detail viewer

### Data Flow

1. User selects a folder → `MainController` detects CSV + 3 Excel control files (`Intrari_*.xlsx`, `Aviz_*.xlsx`, `Depozite_*.xlsx`)
2. `CsvReader` / `ExcelReader` parse files into dataclass models
3. Notices are classified into 4 types based on sender/recipient, volumes are calculated per good type/species, and validated (no unknown types/sortiments, item volumes must sum to notice total)
4. Notices are sorted by `data_ora_emitere` ascending
5. `DepositDataWindow` prompts user for pricing data per deposit
6. `ReportGenerator.generate_report()` produces the final multi-sheet Excel output

### Deposit Types

Three deposit types (LR/temporary, main, external) each require different pricing fields. Type inference is in `models.py`, enabled fields per type are defined in `config.py` (`DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE`).

### Error Handling

Raise `SRError(message, title="Eroare")` for user-facing errors — the UI catches and displays these as dialogs. Use the logging system (`core/logger.py`) for debug/trace output; logs go to `logs/`.
