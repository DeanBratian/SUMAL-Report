# CHECKED

import openpyxl
import pandas as pd
from datetime import datetime
from core.models import IntrariExcelModel, AvizExcelModel, DepoziteExcelModel
from dataclasses import fields
from os import path
from core.sr_error import SRError
from core.logger import Logger

class ExcelReader:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.expected_intrari_columns = [
            f.metadata.get("excel_column", f.name)
            for f in fields(IntrariExcelModel)
        ]
        self.expected_aviz_columns = [
            f.metadata.get("excel_column", f.name)
            for f in fields(AvizExcelModel)
        ]
        self.expected_depozite_columns = [
            f.metadata.get("excel_column", f.name)
            for f in fields(DepoziteExcelModel)
        ]

        # The format of the date strings in the SUMAL Excel files
        self.SUMAL_EXCEL_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

        self.logger.debug(f"Expected columns Excel Intrari: {self.expected_intrari_columns}")
        self.logger.debug(f"Expected columns Excel Aviz: {self.expected_aviz_columns}")
        self.logger.debug(f"Expected columns Excel Depozite: {self.expected_depozite_columns}")
    
    # ---------------------------------------------------------------------- #
    
    def parse_xl_row_to_dataclass(
            self, row: pd.Series, cls: type[IntrariExcelModel] | type[AvizExcelModel] | type[DepoziteExcelModel]
        ) -> IntrariExcelModel | AvizExcelModel | DepoziteExcelModel:
        
        """Parse an Excel row into a ExcelModel object, universal for all Excels"""
        data = {}
        for f in fields(cls):
            excel_col = f.metadata.get("excel_column", f.name)
            value = row.get(excel_col, None)

            if pd.isna(value):
                raise SRError(
                    f"Coloana '{excel_col}' lipsește sau este goală în {cls.__name__}",
                    title = "Eroare citire Excel"
                )
            try:
                if f.type is int:
                    value = int(value)
                elif f.type is float:
                    value = float(value)
                elif f.type is datetime:
                    value = datetime.strptime(value, self.SUMAL_EXCEL_DATE_FORMAT)
            except Exception as e:
                raise SRError(
                    f"Nu s-a putut converti valoarea '{value}' "
                    f"pentru câmpul '{excel_col}' ({cls.__name__}): {e}",
                    title = "Eroare conversie valoare Excel"
                )

            data[f.name] = value

        return cls(**data)
    
    # ---------------------------------------------------------------------- #

    def read_excel_file(
            self, folder_path: str, file_name: str, 
            cls: type[IntrariExcelModel] | type[AvizExcelModel] | type[DepoziteExcelModel],
            expected_columns: list[str]
        ) -> list[IntrariExcelModel | AvizExcelModel | DepoziteExcelModel]:
        
        """Parse an Excel file into a list of entries"""
        self.logger.info(f"Reading Excel file: {file_name}")
        full_path = path.join(folder_path, file_name)

        try:
            df = pd.read_excel(full_path, engine = "openpyxl")
        except Exception as e:
            raise SRError(
                f"Fișierul Excel '{file_name}' nu a putut fi deschis:\n{e}",
                title = "Eroare deschidere Excel"
            )

        if df.empty:
            raise SRError(
                f"Fișierul Excel '{file_name}' este gol",
                title = "Eroare fișier Excel gol"
            )

        missing = [col for col in expected_columns if col not in df.columns]
        if missing:
            self.logger.error(f"Excel '{file_name}' missing columns: {missing}")
            raise SRError(
                f"Fișierul Excel '{file_name}' nu conține coloanele necesare:\n"
                + "\n".join(f"  • {c}" for c in missing),
                title = "Eroare coloane lipsă Excel"
            )

        entries = []
        for idx, row in df.iterrows():
            try:
                entries.append(self.parse_xl_row_to_dataclass(row, cls))
            except SRError as e:
                raise SRError(
                    f"Eroare la rândul {idx + 1} din '{file_name}': {e.message}",
                    title = e.title
                )
            except Exception as e:
                raise SRError(
                    f"Eroare la procesarea rândului {idx + 1} din '{file_name}':\n{e}",
                    title = "Eroare parsare Excel"
                )

        self.logger.info(f"Parsed {len(entries)} entries of type {cls.__name__}")
        return entries

    # ---------------------------------------------------------------------- #

    def read_intrari_excel(self, folder_path: str, file_name: str) -> list[IntrariExcelModel]:
        """Handler for Intrari_ Excel file reading"""
        return self.read_excel_file(folder_path, file_name, IntrariExcelModel, self.expected_intrari_columns)

    # ---------------------------------------------------------------------- #

    def read_aviz_excel(self, folder_path: str, file_name: str) -> list[AvizExcelModel]:
        """Handler for Aviz_ Excel file reading"""
        return self.read_excel_file(folder_path, file_name, AvizExcelModel, self.expected_aviz_columns)
    
    # ---------------------------------------------------------------------- #

    def read_depozite_excel(self, folder_path: str, file_name: str) -> list[DepoziteExcelModel]:
        """Handler for Depozite_ Excel file reading"""
        return self.read_excel_file(folder_path, file_name, DepoziteExcelModel, self.expected_depozite_columns)
    
    # ---------------------------------------------------------------------- #

    def read_excel_row_count(self, folder_path: str, file_path: str) -> int:
        """
        Return the number of data rows in an Excel file without fully parsing it.
        Returns 0 if the file is missing, empty, or cannot be opened.
        This is intentionally non-fatal — it is used during file detection
        before the user clicks Parse.
        """
        full_path = path.join(folder_path, file_path)
        try:
            wb = openpyxl.load_workbook(full_path, read_only = True)
            ws = wb.active
            max_row = ws.max_row
            wb.close()
            if max_row is None or max_row <= 1:
                self.logger.warning(f"Excel file is empty: {file_path}")
                return 0
            count = max_row - 1
            self.logger.debug(f"Row count for - {file_path}: {count}")
            return count
        except Exception as e:
            self.logger.error(f"Failed to count rows in '{file_path}': {e}")
            return 0
