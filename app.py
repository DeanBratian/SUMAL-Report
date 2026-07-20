"""SUMAL Report — headless backend.

Downloads the period's files from sumal-map.ro, parses and validates them and
generates the report. Designed to run unattended (cron on the 1st of each month
for the month that just ended); everything is traced to logs/sumal_report.log.

Usage:
    python app.py                                   # last completed month
    python app.py --start 01.06.2026 --end 30.06.2026
    python app.py --login-test                      # only verify SUMAL login
    python app.py --folder inputs                   # process an already-downloaded folder
"""

import argparse
import os
import sys
from datetime import date, datetime, timedelta

from core import deposit_prices
from core.db import get_connection
from core.enums import FolderStatus
from core.html_report import HtmlReportGenerator
from core.logger import Logger
from core.pipeline import ReportPipeline
from core.sr_error import SRError
from sumal.catalog import sync_catalog
from sumal.client import SumalClient
from sumal.config import load_credentials
from sumal.downloader import SumalDownloader

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATE_FORMAT = "%d.%m.%Y"  # CLI date format: 01.06.2026

# ---------------------------------------------------------------------- #

def last_completed_month(today: date) -> tuple[date, date]:
    """First and last day of the month before the one containing `today`."""
    first_of_current = today.replace(day=1)
    end = first_of_current - timedelta(days=1)
    return end.replace(day=1), end

# ---------------------------------------------------------------------- #

def resolve_period(args) -> tuple[date, date]:
    if (args.start is None) != (args.end is None):
        raise SRError("Folosește --start și --end împreună (format: 01.06.2026).",
                      title="Eroare perioadă")
    if args.start is None:
        return last_completed_month(date.today())

    try:
        start = datetime.strptime(args.start, DATE_FORMAT).date()
        end = datetime.strptime(args.end, DATE_FORMAT).date()
    except ValueError as e:
        raise SRError(f"Dată invalidă ({e}). Format așteptat: 01.06.2026.",
                      title="Eroare perioadă")
    if start > end:
        raise SRError("Data de început este după data de sfârșit.", title="Eroare perioadă")
    return start, end

# ---------------------------------------------------------------------- #

def login(logger: Logger) -> SumalClient:
    username, password = load_credentials(PROJECT_ROOT)
    client = SumalClient(logger, username, password)
    client.login()
    return client

# ---------------------------------------------------------------------- #

def process_folder(folder: str, start: date, end: date, logger: Logger) -> None:
    """Parse + validate a folder of downloaded files and generate the report."""
    pipeline = ReportPipeline(logger)
    pipeline.set_folder(folder)

    status, counts = pipeline.validate_folder_files()
    if status != FolderStatus.READY:
        raise SRError(
            f"Folderul '{folder}' nu este complet ({status.name}): {counts}",
            title="Eroare fișiere perioadă"
        )

    pipeline.parse_files()
    external, ignored = pipeline.initialize_deposit_data()
    if external:
        logger.info(f"External deposits detected: {sorted(external)}")
    if ignored:
        logger.info(f"Deposits ignored (no notices reference them): {sorted(ignored)}")

    # Prices are optional: the HTML report renders volumes/counts always and
    # lets the user type the missing prices directly in its Depozite tab
    missing = deposit_prices.sync_and_apply(folder, pipeline.deposit_data, logger)
    if missing:
        logger.warning(
            f"{len(missing)} price fields still empty — money figures will show '—' "
            "until filled in the report or in "
            f"{os.path.join(folder, deposit_prices.PRICES_FILENAME)}"
        )

    # Every notice must resolve to a known deposit before rendering
    deposit_names = {d.nume_depozit for d in pipeline.deposit_data}
    orphans = [n for n in pipeline.notices if n.provenienta not in deposit_names]
    if orphans:
        details = "\n".join(f"  • {n.cod_unic}  (proveniență: {n.provenienta})" for n in orphans)
        raise SRError(f"Nu s-au găsit date de depozit pentru:\n{details}",
                      title="Eroare date depozit lipsă")

    output_path = os.path.join(
        folder, f"Raport_{start.strftime(DATE_FORMAT)}_{end.strftime(DATE_FORMAT)}.html"
    )
    # Prestări marking was a manual UI step; headless runs treat no notice as prestări yet
    HtmlReportGenerator(logger).generate(
        pipeline.notices, pipeline.deposit_data, start, end, output_path
    )
    logger.info(f"Report written: {output_path}")

# ---------------------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(description="SUMAL Report — headless backend")
    parser.add_argument("--start", help="începutul perioadei, ex: 01.06.2026")
    parser.add_argument("--end", help="sfârșitul perioadei, ex: 30.06.2026")
    parser.add_argument("--login-test", action="store_true",
                        help="doar verifică autentificarea SUMAL, fără descărcări")
    parser.add_argument("--sync-catalog", action="store_true",
                        help="doar sincronizează catalogul SUMAL (specii, sortimente, operațiuni) în data/sumal.db")
    parser.add_argument("--folder",
                        help="procesează un folder deja descărcat (sare peste login/descărcare)")
    args = parser.parse_args()

    logger = Logger(os.path.join(PROJECT_ROOT, "logs", "sumal_report.log"))
    logger.info(f"=== SUMAL Report run started: {' '.join(sys.argv)} ===")

    try:
        start, end = resolve_period(args)
        logger.info(f"Target period: {start.strftime(DATE_FORMAT)} -> {end.strftime(DATE_FORMAT)}")

        if args.login_test:
            client = login(logger)
            client.get_user_companies()
            client.close()
            logger.info("Login test finished successfully")
            return 0

        if args.sync_catalog:
            client = login(logger)
            try:
                sync_catalog(client, get_connection(PROJECT_ROOT), logger)
            finally:
                client.close()
            return 0

        if args.folder:
            folder = os.path.abspath(args.folder)
        else:
            client = login(logger)
            folder = os.path.join(
                PROJECT_ROOT, "downloads", f"{start.isoformat()}_{end.isoformat()}"
            )
            os.makedirs(folder, exist_ok=True)
            downloader = SumalDownloader(client, logger)
            try:
                # Refresh the reference catalog while the session is live —
                # the report/DB phases rely on it being current
                sync_catalog(client, get_connection(PROJECT_ROOT), logger)
                downloader.download_period(start, end, folder)
            finally:
                client.close()

        process_folder(folder, start, end, logger)
        logger.info("=== Run finished successfully ===")
        return 0

    except SRError as e:
        logger.error(f"{e.title}: {e.message}")
        return 1
    except Exception:
        import traceback
        logger.error(f"Unhandled exception:\n{traceback.format_exc()}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
