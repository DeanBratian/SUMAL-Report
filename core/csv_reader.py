# CHECKED

from os import path
import pandas as pd
from dataclasses import fields
from datetime import datetime
from core.models import TransportNoticeModel, WoodItemModel, CSVParseResult
from core.utils import normalize_field
from core.enums import CSVParseStatus
from core.config import APP_CONFIG
from core.sr_error import SRError
from core.logger import Logger

class CsvReader:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.expected_header_fields = [
            f.metadata.get("csv_column", f.name) 
            for f in fields(TransportNoticeModel) if f.name != "wood_items"
        ]
        self.expected_wood_item_fields = [
            f.metadata.get("csv_column", f.name)
            for f in fields(WoodItemModel)
        ]

        # Format of dates in CSV files downloaded from SUMAL
        self.SUMAL_CSV_DATE_FORMAT = APP_CONFIG.TIME_FORMAT

        self.logger.debug(f"expected_header_fields: {self.expected_header_fields}")
        self.logger.debug(f"expected_wood_item_fields: {self.expected_wood_item_fields}")

    # ---------------------------------------------------------------------- #

    def parse_csv_row_to_dataclass(
            self, row: pd.Series, cls: type[TransportNoticeModel] | type[WoodItemModel]
        ) -> TransportNoticeModel | WoodItemModel:
        
        """Parse a CSV row into a TransportNoticeModel or WoodItemModel, general data is read from the first row and checked across columns.
        WoodItemModels are read from each row"""
        data = {}
        for f in fields(cls):
            csv_col = f.metadata.get("csv_column", f.name)

            # wood_items is a relation field with no CSV column — skip by name.
            if f.name == "wood_items":
                continue

            # Columns are pre-validated and fillna("") applied — value is always a string.
            value: str = row[csv_col]

            # Empty CSV fields, ignore and normalize (zero out)
            if value == "":
                value = normalize_field(f)
                if value is None:
                    raise SRError(
                        f"Câmpul '{csv_col}' este gol și nu poate fi normalizat (tip: {f.type.__name__})",
                        title = "Eroare parsare CSV"
                    )
            else:
                try:
                    if f.type is int:
                        value = int(value)
                    elif f.type is float:
                        value = float(value)
                    elif f.type is datetime:
                        value = datetime.strptime(value, self.SUMAL_CSV_DATE_FORMAT)
                except Exception as e:
                    raise SRError(
                        f"Nu s-a putut converti valoarea '{value}' "
                        f"pentru câmpul '{csv_col}': {e}",
                        title = "Eroare conversie valoare CSV"
                    )

            data[f.name] = value

        return cls(**data)
    
    # ---------------------------------------------------------------------- #

    def read_notice(self, file_path: str) -> TransportNoticeModel:
        """Parse a CSV file into a TransportNoticeModel"""

        filename: str = path.basename(file_path)

        try:
            df = pd.read_csv(file_path, sep = ",", dtype = str).fillna("")
        except Exception as e:
            raise SRError(
                f"Fișierul '{filename}' nu a putut fi deschis/citit:\n{e}",
                title = "Eroare accesare CSV"
            )

        if df.empty:
            raise SRError(
                f"Fișierul '{filename}' este gol.",
                title = "Eroare fișier CSV gol"
            )

        # 1. All required columns must be present
        required = set(self.expected_header_fields + self.expected_wood_item_fields)
        missing: list[str] = [col for col in required if col not in df.columns]
        if missing:
            self.logger.error(f"CSV '{filename}' missing columns: {missing}")
            raise SRError(
                f"Fișierul '{filename}' nu conține coloanele necesare:\n"
                + "\n".join(f"  • {c}" for c in missing),
                title = "Eroare coloane lipsă CSV"
            )

        # 2. Header fields must be consistent across all rows (same notice)
        for col in self.expected_header_fields:
            if len(df[col].unique()) > 1:
                self.logger.error(f"CSV '{filename}' inconsistent header field '{col}': {df[col].unique().tolist()}")
                raise SRError(
                    f"Câmpul '{col}' are valori diferite pe rânduri în fișierul '{filename}'.",
                    title = "Eroare date inconsistente CSV"
                )

        # 3. Parse header from first row
        try:
            notice = self.parse_csv_row_to_dataclass(df.iloc[0], TransportNoticeModel)
        except SRError as e:
            raise SRError(
                f"Eroare la parsarea header-ului în fișierul '{filename}': {e.message}",
                title = e.title
            )

        # 4. Parse wood items from every row
        wood_items: list[WoodItemModel] = []
        for idx, (_, row) in enumerate(df.iterrows(), start = 1):
            try:
                wood_items.append(self.parse_csv_row_to_dataclass(row, WoodItemModel))
            except SRError as e:
                raise SRError(
                    f"Eroare la rândul {idx} din fișierul '{filename}': {e.message}",
                    title = e.title
                )
        notice.wood_items = wood_items

        self.logger.debug(
            f"Parsed notice: {notice.cod_unic} | "
            f"{len(wood_items)} wood items, vol = {notice.volum_total_aviz} m³, "
            f"emitent = {notice.emitent_nume}, destinatar = {notice.destinatar_nume}"
        )
        return notice

    # ---------------------------------------------------------------------- #

    def read_all_notices_in_folder(
            self, folder_path: str, unique_filenames: list[str]
        ) -> tuple[list[TransportNoticeModel], list[CSVParseResult]]:
        """Parse all CSV files in target folder.
        Errors are collected per-file into CSVParseResult and never propagated — a bad notice
        should not block the rest of the batch. Consumes all Exceptions and returns batch result."""
        notices: list[TransportNoticeModel] = []
        parse_results: list[CSVParseResult] = []

        for filename in unique_filenames:
            full_path = path.join(folder_path, filename)
            try:
                notice = self.read_notice(full_path)
                notices.append(notice)
                parse_results.append(CSVParseResult(filename, CSVParseStatus.OK, ""))
            except SRError as e:
                self.logger.error(f"Failed parsing '{filename}': {e.message}")
                parse_results.append(CSVParseResult(filename, CSVParseStatus.ERROR, e.message))
            except Exception as e:
                self.logger.error(f"Unexpected error parsing '{filename}': {e}")
                parse_results.append(CSVParseResult(filename, CSVParseStatus.ERROR, str(e)))
        
        return notices, parse_results
