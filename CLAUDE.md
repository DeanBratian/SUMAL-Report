# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
python app.py                                   # process last completed month (cron target)
python app.py --start 01.06.2026 --end 30.06.2026
python app.py --login-test                      # only verify sumal-map.ro login
python app.py --folder inputs                   # process an already-downloaded folder
```

**Dependencies** (install via `pip install -r requirements.txt`): `pandas`, `openpyxl`, `requests`.

**Credentials**: `SUMAL_USERNAME`/`SUMAL_PASSWORD` env vars, or git-ignored `secrets.local.json` (`{"username": ..., "password": ...}`).

## Running Tests

```bash
python -m pytest tests/ -v
```

## Architecture

**Headless backend** (no UI — the former PyQt6 GUI was removed in July 2026) for processing Romanian timber transport notices (SUMAL) and generating period reports. Runs unattended (cron on the 1st of each month for the ended month); all operations are traced to `logs/sumal_report.log`. The company context is "Brat Valms Service Tur S.R.L." (constants in `core/config.py`; SUMAL company id 9052, idAngajat 16058).

### Layers

- **`app.py`** — CLI entrypoint: resolves the target period, logs in, downloads, runs the pipeline.
- **`sumal/`** — sumal-map.ro HTTP automation
  - `config.py` — endpoints, credential loading; documents the captured OAuth2 login flow
  - `client.py` — `SumalClient`: Spring Security form login (`_csrf` + username/password POST to `/auth/login`, server-side code exchange, `SESSION` cookies, 24h expiry). Detects the sometimes-active login captcha (`CaptchaRequiredError`) — it cannot be solved headless.
  - `downloader.py` — `SumalDownloader`: fetches the period's Avize Electronice / Intrari NIR / Depozite Excel exports + per-notice CSVs. **Endpoints are implemented from user-captured HAR files; capture-pending methods raise SRError.**
- **`core/`** — business logic
  - `pipeline.py` — `ReportPipeline` (ex-MainController): folder file detection, parsing, cross-validation (notices vs. control Excels, type inference, volume checks), deposit initialization, report generation
  - `models.py`, `csv_reader.py`, `excel_reader.py`, `report_generator.py`, `config.py`, `enums.py`, `utils.py`, `logger.py`, `sr_error.py` — as before
  - `deposit_prices.py` — headless replacement for the old pricing dialog: per-period `deposit_prices.json` in the run folder, auto-synced with detected deposits; unfilled fields block report generation with a clear error

### Data Flow

1. Period resolved (`--start/--end` or last completed month) → files downloaded into `downloads/<start>_<end>/`
2. Pipeline detects CSV + 3 control Excels (`Intrari_*.xlsx`, `Aviz_*.xlsx`, `Depozite_*.xlsx`), parses into dataclass models
3. Notices classified into 4 types (intrare din partidă proprie etc.), volumes computed per good type/species, validated, sorted by `data_ora_emitere`
4. Deposit prices applied from `deposit_prices.json`; report generated in the run folder

### Planned (see memory)

SQLite database for species/sortiments and stock ledger; HTML report replacing the Excel output (same report math, plus price statistics — medians etc. — from deposit prices).

### Error Handling

Raise `SRError(message, title="Eroare")` for user-facing errors — `app.py` catches, logs and exits non-zero (1 = SRError, 2 = unexpected). Use `core/logger.py` for all trace output.

## Security Notes

- `secrets.local.json`, `*.har` captures and `downloads/` are git-ignored — never commit them (HARs contain the plaintext password and session cookies).
