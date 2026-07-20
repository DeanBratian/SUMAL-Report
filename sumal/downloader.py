"""Downloads the period's files from sumal-map.ro into a local folder,
reproducing exactly what the manual SUMAL Report workflow collected:

  - Aviz_*.xlsx      — Avize Electronice export for the period.
  - Intrari_*.xlsx   — Intrari NIR export, scoped to the principal deposit.
  - Depozite_*.xlsx  — Depozite export (active deposits).
  - one CSV per notice row: every aviz in the period yields a CSV; every
    Intrari NIR row yields one more file for the same notice (the manual flow
    downloaded it twice). Duplicates share the notice code and differ only in
    the timestamp suffix — core/pipeline dedupes them by base name, and the
    file count must equal Intrari rows + Aviz rows (the pipeline's cross-check).

All filter/export request shapes were captured from browser traffic 2026-07-19.
Filter bodies must contain EVERY field, with the exact ""/null mix the web
client sends — missing keys make the server return HTTP 500.
"""

from datetime import date, datetime, timedelta
import os

from core.logger import Logger
from core.sr_error import SRError
from sumal.client import SumalClient
from sumal.config import (
    API_DATE_FORMAT, PRINCIPAL_DEPOSIT_ID,
    EP_AVIZE_FILTER, EP_AVIZE_EXPORT, EP_AVIZ_CSV, EP_INTRARI_FILTER, EP_INTRARI_EXPORT,
    EP_DEPOZITE_LIST, EP_DEPOZITE_EXPORT,
)

# Filename timestamp suffix, matching the site's manual download naming
# (AP..._08_12_2025 16_57_38.csv) — core/utils.extract_base_name strips it.
FILE_TS_FORMAT = "%d_%m_%Y %H_%M_%S"

AVIZE_EXPORT_COLUMNS = ("Cod Aviz,Tip Transport,Provenienta,Mijloc transport,"
                        "Numar mijloc transport,Categorie transport,Status,"
                        "Volum total aviz(mc),Data emitere")
AVIZE_EXPORT_PROPERTIES = ("codAviz,numeTipTransport,provenienta,numeMijlocTransport,"
                           "numarTransport,numeCategorieTransport,status,volum,dataEmitere,")

INTRARI_EXPORT_COLUMNS = "Număr NIR,Companie emitenta,Cod aviz,Dată NIR,Grupe specii,Volum (mc),Status"
INTRARI_EXPORT_PROPERTIES = "numarPV,numeCompanie,codAviz,dataPV,grupeSpecii,volumIntrare,status,"

DEPOZITE_EXPORT_COLUMNS = "Nume depozit,Latitudine,Longitudine,Tip depozit,Status depozit,Judet"
DEPOZITE_EXPORT_PROPERTIES = "numeDepozit,latitudine,longitudine,numeDepozitTip,numeDepozitStatus,numeJudet,"

class SumalDownloader:
    def __init__(self, client: SumalClient, logger: Logger):
        self.client = client
        self.logger = logger

    # ---------------------------------------------------------------------- #

    def download_period(self, start: date, end: date, dest_folder: str) -> None:
        """Download all files the pipeline needs for [start, end] into dest_folder."""
        self.logger.info(f"SUMAL download: period {start} -> {end} into {dest_folder}")

        avize = self.fetch_avize_list(start, end)
        intrari = self.fetch_intrari_list(start, end)

        self.download_avize_excel(len(avize), start, end, dest_folder)
        self.download_intrari_excel(len(intrari), start, end, dest_folder)
        self.download_depozite_excel(dest_folder)
        self.download_notice_csvs(avize, intrari, dest_folder)

    # ---------------------------------------------------------------------- #

    def fetch_avize_list(self, start: date, end: date) -> list[dict]:
        """All avize (inputs AND outputs) emitted in the period."""
        avize = self.client.fetch_all_pages(
            EP_AVIZE_FILTER, self._avize_filter_body(start, end), sort="dataEmitere,desc"
        )
        self.logger.info(f"SUMAL avize list: {len(avize)} avize in period")
        self._check_period(avize, "dataEmitere", start, end, "findAllAvizFiltrare")
        return avize

    # ---------------------------------------------------------------------- #

    @staticmethod
    def _avize_filter_body(start: date, end: date) -> dict:
        return {
            "idCompanie": "",
            "codAviz": "",
            "codTipTransport": "",
            "codMijlocTransport": "",
            "nrMijlocTransport": "",
            "codCategorieTransport": "",
            "provenienta": "",
            "deLa": start.strftime(API_DATE_FORMAT),
            "panaLa": end.strftime(API_DATE_FORMAT),
            "codStatusAviz": "",
            "tipTransportator": "",
        }

    # ---------------------------------------------------------------------- #

    def download_avize_excel(self, total_rows: int, start: date, end: date, dest_folder: str) -> str:
        params = {
            "tabelName": "Aviz",
            "page": 0,
            "size": max(total_rows, 1),
            "sort": "dataEmitere,desc",
            "columns": AVIZE_EXPORT_COLUMNS,
            "properties": AVIZE_EXPORT_PROPERTIES,
        }
        path = os.path.join(dest_folder, self._stamped_name("Aviz", ".xlsx"))
        self.client.download_xlsx_export(
            EP_AVIZE_EXPORT, params, self._avize_filter_body(start, end), path
        )
        return path

    # ---------------------------------------------------------------------- #

    def fetch_intrari_list(self, start: date, end: date) -> list[dict]:
        """All Intrari NIR rows for the principal deposit in the period.
        Items carry idAviz + codAviz. Every filter field must be present,
        with the exact ""/null mix the web client sends (captured 2026-07-19)."""
        intrari = self.client.fetch_all_pages(
            EP_INTRARI_FILTER, self._intrari_filter_body(start, end), sort="documentNr,desc"
        )
        self.logger.info(f"SUMAL intrari list: {len(intrari)} NIR rows in period")
        return intrari

    # ---------------------------------------------------------------------- #

    @staticmethod
    def _intrari_filter_body(start: date, end: date) -> dict:
        return {
            "dataInceput": start.strftime(API_DATE_FORMAT),
            "dataSfarsit": end.strftime(API_DATE_FORMAT),
            "idDepozit": PRINCIPAL_DEPOSIT_ID,
            "idGrupaSpecie": "",
            "idSpecie": "",
            "idSortiment": "",
            "idSubsortiment": "",
            "numarPV": "",
            "idCompanie": None,
            "codAviz": "",
            "idCompanieAviz": None,
        }

    # ---------------------------------------------------------------------- #

    def download_intrari_excel(self, total_rows: int, start: date, end: date, dest_folder: str) -> str:
        params = {
            "tabelName": "Intrari",
            "page": 0,
            "size": max(total_rows, 1),
            "sort": "documentNr,desc",
            "columns": INTRARI_EXPORT_COLUMNS,
            "properties": INTRARI_EXPORT_PROPERTIES,
        }
        path = os.path.join(dest_folder, self._stamped_name("Intrari", ".xlsx"))
        self.client.download_xlsx_export(
            EP_INTRARI_EXPORT, params, self._intrari_filter_body(start, end), path
        )
        return path

    # ---------------------------------------------------------------------- #

    def download_depozite_excel(self, dest_folder: str) -> str:
        # No status filter: historical periods reference temporary LR deposits
        # that have since been closed (INACTIV) — classification needs them all;
        # the pipeline ignores deposits no notice references.
        body = {
            "numeDepozit": "",
            "codDepozitTip": "",
            "codSirutaJudet": "",
            "codDepozitStatus": "",
            "idCompanieByName": "",
            "idCompanieByCodFiscal": "",
            "idCompanie": "",
        }
        deposits = self.client.fetch_all_pages(EP_DEPOZITE_LIST, body, sort="numeDepozit,asc")
        self.logger.info(f"SUMAL depozite list: {len(deposits)} active deposits")

        params = {
            "tabelName": "Depozite",
            "page": 0,
            "size": max(len(deposits), 1),
            "sort": "numeDepozit,asc",
            "columns": DEPOZITE_EXPORT_COLUMNS,
            "properties": DEPOZITE_EXPORT_PROPERTIES,
        }
        path = os.path.join(dest_folder, self._stamped_name("Depozite", ".xlsx"))
        self.client.download_xlsx_export(EP_DEPOZITE_EXPORT, params, body, path)
        return path

    # ---------------------------------------------------------------------- #

    def download_notice_csvs(self, avize: list[dict], intrari: list[dict], dest_folder: str) -> None:
        """One CSV per aviz; plus a duplicate file per Intrari NIR row (same
        content, later timestamp) so the folder mirrors the manual workflow
        and the pipeline's file-count cross-check holds."""
        csv_by_code: dict[str, str] = {}
        stamp = datetime.now()

        for aviz in avize:
            cod = aviz.get("codAviz", "")
            id_aviz = aviz.get("idAviz")
            if not cod or id_aviz is None:
                raise SRError(
                    f"Aviz fără codAviz/idAviz în răspunsul findAllAvizFiltrare: {aviz}",
                    title="Eroare listă avize SUMAL"
                )
            content = self.client.download_text(EP_AVIZ_CSV.format(id_aviz=id_aviz))
            csv_by_code[cod] = content
            self._write_csv(dest_folder, cod, stamp, content)
        self.logger.info(f"Downloaded {len(csv_by_code)} notice CSVs")

        # Second copy for input notices, as the manual Intrari NIR tab produced.
        # An intrari row missing from the avize list (e.g. notice emitted just
        # before the period, received inside it) is downloaded by its own idAviz.
        overlap = sorted(e.get("codAviz", "") for e in intrari if e.get("codAviz", "") in csv_by_code)
        self.logger.info(
            f"Notices in BOTH Intrari NIR and Avize ({len(overlap)}) get a duplicate CSV, "
            f"deduped later by the pipeline: {overlap}"
        )
        duplicate_stamp = stamp + timedelta(seconds=1)
        for entry in intrari:
            cod = entry.get("codAviz", "")
            if cod in csv_by_code:
                content = csv_by_code[cod]
            else:
                self.logger.warning(f"Intrari notice not in avize list, downloading directly: {cod}")
                content = self.client.download_text(EP_AVIZ_CSV.format(id_aviz=entry["idAviz"]))
            self._write_csv(dest_folder, cod, duplicate_stamp, content)

    # ---------------------------------------------------------------------- #

    def _write_csv(self, dest_folder: str, cod: str, stamp: datetime, content: str) -> None:
        path = os.path.join(dest_folder, f"{cod}_{stamp.strftime(FILE_TS_FORMAT)}.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)

    # ---------------------------------------------------------------------- #

    def _check_period(self, items: list[dict], date_field: str, start: date, end: date, source: str) -> None:
        """Guard against the server silently ignoring an unrecognized date filter:
        every returned item must fall inside the requested period."""
        for item in items:
            parsed = self._parse_api_date(item.get(date_field))
            if parsed is not None and not (start <= parsed.date() <= end):
                raise SRError(
                    f"Endpoint-ul {source} a returnat un aviz din afara perioadei "
                    f"({item.get(date_field)!r}) — filtrul de dată nu a fost aplicat, "
                    "structura request-ului trebuie verificată cu o captură nouă (HAR).",
                    title="Eroare filtru perioadă SUMAL"
                )

    # ---------------------------------------------------------------------- #

    @staticmethod
    def _parse_api_date(value) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):  # epoch milliseconds
            return datetime.fromtimestamp(value / 1000)
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y"):
            try:
                return datetime.strptime(str(value)[:26], fmt)
            except ValueError:
                continue
        return None

    # ---------------------------------------------------------------------- #

    @staticmethod
    def _stamped_name(prefix: str, ext: str) -> str:
        return f"{prefix}_{datetime.now().strftime(FILE_TS_FORMAT)}{ext}"
