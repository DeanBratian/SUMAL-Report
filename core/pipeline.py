import os
from core.csv_reader import CsvReader
from core.excel_reader import ExcelReader
from core.logger import Logger
from core.utils import extract_base_name
from core.enums import CSVParseStatus, DepozitSource, DepositType, NoticeType, FolderStatus
from core.config import DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE
from core.models import (
    IntrariExcelModel, AvizExcelModel, DepoziteExcelModel,
    CSVParseResult, DepozitDataModel, TransportNoticeModel
)
from core.report_generator import ReportGenerator
from core.sr_error import SRError

class ReportPipeline:
    """Headless processing pipeline: detect the period's downloaded files in a
    folder, parse and validate them, initialize deposit data and generate the report."""
    def __init__(self, logger: Logger):
        self.logger = logger
        self.csv_reader: CsvReader = CsvReader(self.logger)
        self.excel_reader: ExcelReader = ExcelReader(self.logger)
        self.report_generator: ReportGenerator = ReportGenerator(self.logger)
        
        # Flag that indicates that chosen folder's files have been parsed
        self.is_parsed: bool = False  
        # User chosen folder path
        self.folder_path: str | None = None

        # Notices from CSV files, sorted by date (ascending) after parsing
        self.notices: list[TransportNoticeModel] = []
        
        # Entries from Intrari_.xlsx file
        self.intrari_entries: list[IntrariExcelModel] = []
        # Entries from Aviz_.xlsx file
        self.aviz_entries: list[AvizExcelModel] = []
        # Entries from Depozite_.xlsx file
        self.depozite_entries: list[DepoziteExcelModel] = []

        # Expecting 3 control xl files Intrari_, Aviz_ and Depozite_
        self.EXPECTED_XL_COUNT: int = 3
        
        # Dict containing unique CSV names and all CSV names; 
        # Keys: unique and all
        self.csv_files_dict: dict[str, list[str]] = {}
        
        # Stores the name of the Intrari_ excel file at key "intrari",
        # the name of the Aviz_ excel file at key "aviz"
        # and the name of Depozite_ excel file at key "depozite"
        self.xl_files_dict: dict[str, str] = {}
        
        # Number of entries in Intrari_ excel file before actually parsing
        self.intrari_xl_row_count: int = 0
        # Number of entries in Aviz_ excel file before actually parsing
        self.aviz_xl_row_count: int = 0
        # Number of entries in Depozite_ excel file before actually parsing
        self.depozite_xl_row_count: int = 0
        
        # CSV file parsing statuses
        self.csv_parse_results: list[CSVParseResult] = [] 
        
        # List of DepositDataModel objects created by the user, populated by deposit_data_window
        # entries from Depozite_ xl file + unknown provenienta from notices
        self.deposit_data: list[DepozitDataModel] = []

    # ---------------------------------------------------------------------- #    

    def set_folder(self, folder_path: str) -> bool:
        """Stores the user selected folder as a string and resets state if a new folder is selected"""
        if self.folder_path == folder_path:
            return False

        self.folder_path = folder_path
        self.reset_state()
        return True
    
    # ---------------------------------------------------------------------- #

    def reset_state(self) -> None:
        """Resets the stat when user chooses another folder"""
        self.is_parsed = False
        self.notices.clear()

        self.intrari_entries.clear()
        self.aviz_entries.clear()
        self.depozite_entries.clear()

        self.csv_files_dict.clear()
        self.xl_files_dict.clear()

        self.intrari_xl_row_count = 0
        self.aviz_xl_row_count = 0
        self.depozite_xl_row_count = 0
        
        self.csv_parse_results.clear()
        self.deposit_data.clear()

    # ---------------------------------------------------------------------- #

    def detect_csv_files(self) -> None:
        """Analyze the provided CSV files, skipping duplicates and populating csv_files_dict"""
        processed_notices_base_names: set[str] = set()
        unique_notice_names: list[str] = []
        all_notice_names: list[str] = []
        try:
            entries: list[str] = os.listdir(self.folder_path)
        except OSError as e:
            raise SRError(
                f"Folderul nu poate fi accesat:\n{e}",
                title = "Eroare acces folder pentru CSV"
            )
        for f in entries:
            if f.lower().endswith(".csv"):
                all_notice_names.append(f)
                base_name: str = extract_base_name(f)
                if base_name in processed_notices_base_names:
                    self.logger.debug(f"Skipping duplicate notice file: {f}")
                    continue
                processed_notices_base_names.add(base_name)
                unique_notice_names.append(f)
        
        # Full filenames + extension - Unique CSV files in the selected folder, duplicates removed
        self.csv_files_dict["unique"] = unique_notice_names
        # Full filenames + extension - All CSV files in the selected folder
        self.csv_files_dict["all"] = all_notice_names
        
        self.logger.debug(f"Number of unique CSVs: {len(self.csv_files_dict['unique'])}, all CSVs: {len(self.csv_files_dict['all'])}")
    
    # ---------------------------------------------------------------------- #

    def detect_excel_files(self) -> bool:
        """Analyze the provided Excel files, populating xl_files_dict.
        Detect number of entries for each Excel file without parsing the contents.
        Raise SRError if a control file prefix matches more than one file —
        picking one silently could run the report on stale data (repeated SUMAL
        downloads create e.g. 'Intrari_... (1).xlsx' next to the original)."""
        try:
            entries: list[str] = os.listdir(self.folder_path)
        except OSError as e:
            raise SRError(
                f"Folderul nu poate fi accesat:\n{e}",
                title = "Eroare acces folder pentru Excel"
            )

        matches: dict[str, list[str]] = {"intrari": [], "aviz": [], "depozite": []}
        for f in entries:
            lower: str = f.lower()
            if not lower.endswith(".xlsx"):
                continue
            for key in matches:
                if lower.startswith(f"{key}_"):
                    matches[key].append(f)
                    break

        duplicated: list[str] = [name for files in matches.values() if len(files) > 1 for name in files]
        if duplicated:
            names = "\n".join(f"  • {name}" for name in sorted(duplicated))
            raise SRError(
                f"Există mai multe fișiere Excel de același tip în folder:\n{names}\n\n"
                "Păstrează doar fișierele descărcate cel mai recent din SUMAL și șterge restul.",
                title = "Eroare fișiere Excel duplicate"
            )

        if matches["intrari"]:
            self.xl_files_dict["intrari"] = matches["intrari"][0]
            self.intrari_xl_row_count = self.excel_reader.read_excel_row_count(self.folder_path, matches["intrari"][0])
        if matches["aviz"]:
            self.xl_files_dict["aviz"] = matches["aviz"][0]
            self.aviz_xl_row_count = self.excel_reader.read_excel_row_count(self.folder_path, matches["aviz"][0])
        if matches["depozite"]:
            self.xl_files_dict["depozite"] = matches["depozite"][0]
            self.depozite_xl_row_count = self.excel_reader.read_excel_row_count(self.folder_path, matches["depozite"][0])

        return len(self.xl_files_dict) == self.EXPECTED_XL_COUNT

    # ---------------------------------------------------------------------- #

    def validate_folder_files(self) -> tuple[FolderStatus, dict[str, int]]:
        """Detect CSV and Excel files, return status and counts for logging"""
        self.detect_csv_files()
        correct_nr_xls: bool = self.detect_excel_files()

        unique_csv_count: int = len(self.csv_files_dict["unique"])
        all_csv_count: int = len(self.csv_files_dict["all"])
        xl_count: int = len(self.xl_files_dict)

        data: dict[str, int] = {
            "unique_csv_count": unique_csv_count,
            "all_csv_count": all_csv_count,
            "xl_count": xl_count,
            "expected_xl_count": self.EXPECTED_XL_COUNT,
            "expected_csv_count": self.get_csv_count_per_excels(),
        }

        if unique_csv_count == 0 and xl_count == 0:
            self.logger.info("Folder validation: NO_FILES — no CSV or Excel files found")
            return FolderStatus.NO_FILES, data

        if not correct_nr_xls:
            self.logger.info(f"Folder validation: MISSING_XL — found {xl_count}/{self.EXPECTED_XL_COUNT} Excel files")
            return FolderStatus.MISSING_XL, data

        if not self.is_correct_csv_count():
            self.logger.info(f"Folder validation: MISSING_CSV — expected {self.get_csv_count_per_excels()} CSV files, found {all_csv_count}")
            return FolderStatus.MISSING_CSV, data

        self.logger.info(f"Folder validation: READY — {unique_csv_count} unique CSVs, {xl_count} Excels")
        return FolderStatus.READY, data

    # ---------------------------------------------------------------------- #

    def parse_files(self) -> None:
        """Parse all files. Raise SRE if there are CSV parsing errors,
        and if unknown sortiment, notice type, orphan codes, if volume validation
        fails, or if cherestele appears on an LR (round-wood) deposit notice"""

        # CSV parsing
        self.notices, self.csv_parse_results = self.csv_reader.read_all_notices_in_folder(
            self.folder_path, self.csv_files_dict["unique"]
        )

        error_files: set[str] = self.get_error_files()
        self.logger.info(f"CSV batch parse complete: {len(self.notices)} OK, {len(error_files)} errors out of {len(self.csv_files_dict['unique'])} files")
        if error_files:
            names = "\n".join(f"  • {f}" for f in sorted(error_files))
            raise SRError(
                f"Următoarele fișiere CSV nu au putut fi procesate:\n{names}\n\n"
                "Verifică fișierul de log-uri pentru detalii",
                title = "Eroare procesare CSV"
            )

        # Excel parsing
        self.intrari_entries = self.excel_reader.read_intrari_excel(
            self.folder_path, self.xl_files_dict["intrari"]
        )
        self.aviz_entries = self.excel_reader.read_aviz_excel(
            self.folder_path, self.xl_files_dict["aviz"]
        )
        self.depozite_entries = self.excel_reader.read_depozite_excel(
            self.folder_path, self.xl_files_dict["depozite"]
        )

        self.logger.debug(
            f"Loaded {len(self.intrari_entries)} Intrari / "
            f"{len(self.aviz_entries)} Aviz / "
            f"{len(self.depozite_entries)} Depozite entries"
        )

        # Cross-validate notices against Excel control files,
        # each notice from CSV must exist at least in one Excel file
        intrari_codes: set[str] = {ie.cod_aviz for ie in self.intrari_entries}
        aviz_codes: set[str] = {ae.cod_aviz for ae in self.aviz_entries}
        orphan_codes: list[str] = []

        for notice in self.notices:
            if notice.cod_unic not in intrari_codes and notice.cod_unic not in aviz_codes:
                orphan_codes.append(notice.cod_unic)
                self.logger.error(f"Notice not found in Intrari or Aviz Excel: {notice.cod_unic}")

        if orphan_codes:
            codes = "\n".join(f"  • {c}" for c in orphan_codes)
            raise SRError(
                f"Următoarele avize nu au fost găsite nici în Intrări, nici în Avize:\n{codes}\n\n"
                "Verifică că fișierele Excel sunt la zi",
                title = "Eroare avize lipsă din Excel"
            )

        # Type inference + validation
        unknown_type_codes: list[str] = []
        unknown_sortiment_codes: list[str] = []
        invalid_volume_codes: list[str] = []
        cherestele_on_lr_codes: list[str] = []

        for notice in self.notices:
            notice.infer_notice_type(self.depozite_entries)
            unknown_sortiments: list[str] = notice.infer_volume_totals()

            # Don't allow UNKNOWN notice types
            if notice.type == NoticeType.UNKNOWN:
                unknown_type_codes.append(notice.cod_unic)
                self.logger.error(f"Unknown type for notice: {notice.cod_unic}")
            # Don't allow UNKNOWN sortiment
            if unknown_sortiments:
                sortiments: str = ", ".join(unknown_sortiments)
                unknown_sortiment_codes.append(f"{notice.cod_unic} ({sortiments})")
                self.logger.error(f"Unknown sortiments for notice {notice.cod_unic}: {sortiments}")
            # Don't allow invalid volume totals
            if not notice.validate_volumes(self.logger):
                invalid_volume_codes.append(notice.cod_unic)
                self.logger.error(f"Volume validation failed: {notice.cod_unic}")

            # Cherestele is processed wood — it can only move through the principal
            # deposit, never an LR (round-wood) deposit. Its presence on an LR notice
            # means corrupt input that would otherwise be priced at 0 RON silently.
            if (notice.type in (NoticeType.INTRARE_DIN_PARTIDA_PROPRIE,
                                 NoticeType.IESIRE_DIN_DEPOZIT_LR)
                    and notice.totals.volum_total_cherestele > 0):
                cherestele_on_lr_codes.append(notice.cod_unic)
                self.logger.error(f"Cherestele on LR-deposit notice: {notice.cod_unic}")

        if unknown_type_codes:
            codes = "\n".join(f"  • {c}" for c in unknown_type_codes)
            raise SRError(
                f"Tipul nu a putut fi dedus pentru următoarele avize:\n{codes}\n\n"
                "Verifică că datele din Depozite_.xlsx corespund cu avizele",
                title = "Eroare tip aviz necunoscut"
            )

        if unknown_sortiment_codes:
            codes = "\n".join(f"  • {c}" for c in unknown_sortiment_codes)
            raise SRError(
                f"Sortimente necunoscute în următoarele avize:\n{codes}",
                title = "Eroare sortiment necunoscut"
            )

        if invalid_volume_codes:
            codes = "\n".join(f"  • {c}" for c in invalid_volume_codes)
            raise SRError(
                f"Validarea volumelor a eșuat pentru următoarele avize:\n{codes}\n\n"
                "Suma volumelor din articole nu corespunde cu volumul total al avizului",
                title = "Eroare validare volume"
            )

        if cherestele_on_lr_codes:
            codes = "\n".join(f"  • {c}" for c in cherestele_on_lr_codes)
            raise SRError(
                f"Următoarele avize conțin cherestea pe un depozit de lemn rotund (LR):\n{codes}\n\n"
                "Cheresteaua poate intra/ieși doar din depozitul principal. "
                "Verifică sortimentele și tipul depozitului.",
                title = "Eroare cherestea pe depozit LR"
            )

        self.logger.debug(
            f"Type inference & validation complete: "
            f"{len(unknown_type_codes)} unknown types, "
            f"{len(unknown_sortiment_codes)} unknown sortiments, "
            f"{len(invalid_volume_codes)} volume mismatches"
        )

        # Sort notices by date ascending
        self.notices.sort(key = lambda n: n.data_ora_emitere)

        # Log notice type breakdown
        type_counts: dict[str, int] = {}
        for n in self.notices:
            key: str = n.type.name if n.type else "NONE"
            type_counts[key] = type_counts.get(key, 0) + 1
        self.logger.info(f"Notice type breakdown: {type_counts}")

        self.is_parsed = True
    
    # ---------------------------------------------------------------------- #

    def initialize_deposit_data(self) -> tuple[set[str], set[str]]:
        """Build deposit_data from parsed entries, filtering out deposits unreferenced by any notice.
        Returns (external_deposits, ignored_deposits) for logging/reporting. Raise SRE on unknown deposit type"""
        self.deposit_data.clear()

        # All provenienta values actually used in notices
        proveniente_din_avize: set[str] = {
            notice.provenienta
            for notice in self.notices
            if notice.provenienta
        }

        # Deposits sourced from external companies (not in Depozite_ Excel)
        external_deposits: set[str] = {
            notice.provenienta
            for notice in self.notices
            if notice.type == NoticeType.INTRARE_DIN_SURSA_EXTERNA
            and notice.provenienta
        }

        ignored_deposits: set[str] = set()

        # 1. Keep only deposits from Depozite_ Excel that are referenced by notices
        for d in self.depozite_entries:
            if d.nume_depozit not in proveniente_din_avize:
                self.logger.debug(f"Ignoring nume_depozit from depozite_entries: {d.nume_depozit}")
                ignored_deposits.add(d.nume_depozit)
                continue
            self.logger.debug(f"Making DepozitDataModel {d.nume_depozit}, {d.tip_depozit}")
            deposit = DepozitDataModel(d.nume_depozit, d.tip_depozit, DepozitSource.EXCEL_SUMAL)
            if deposit.tip_depozit == DepositType.UNKNOWN:
                raise SRError(
                    f"Tipul depozitului '{d.nume_depozit}' nu a putut fi determinat (valoare: '{d.tip_depozit}')",
                    title = "Eroare tip depozit necunoscut"
                )
            self.deposit_data.append(deposit)

        # 2. Add external deposits
        for deposit_name in external_deposits:
            if not any(d.nume_depozit == deposit_name for d in self.deposit_data):
                self.logger.debug(f"Making external DepozitDataModel {deposit_name}, Depozit extern")
                self.deposit_data.append(
                    DepozitDataModel(deposit_name, "Depozit extern", DepozitSource.AVIZE)
                )

        self.logger.info(
            f"Deposit data initialized: {len(self.deposit_data)} active deposits, "
            f"{len(external_deposits)} external, {len(ignored_deposits)} ignored"
        )
        for dep in self.deposit_data:
            self.logger.debug(f"Deposit: '{dep.nume_depozit}' | type = {dep.tip_depozit.name} | source = {dep.sursa_depozit.name}")

        return external_deposits, ignored_deposits

    # ---------------------------------------------------------------------- #

    def generate_report(self, output_path: str, prestari_notices: list[TransportNoticeModel]) -> None:
        """Generate comprehensive multi-sheet Excel report"""
        self.logger.info(f"Starting report generation: {len(self.notices)} notices, {len(prestari_notices)} prestări, {len(self.deposit_data)} deposits")
        deposit_names: set[str] = {d.nume_depozit for d in self.deposit_data}
        notices_without_deposit: list[TransportNoticeModel] = [n for n in self.notices if n.provenienta not in deposit_names]

        if notices_without_deposit:
            details: str = "\n".join(
                f"  • {n.cod_unic}  (proveniență: {n.provenienta})"
                for n in notices_without_deposit
            )
            raise SRError(
                f"Nu s-au găsit date de depozit pentru:\n{details}\n\n",
                title = "Eroare date depozit lipsă"
            )

        self.report_generator.generate_report(
            self.notices,
            self.deposit_data,
            output_path,
            prestari_notices
        )

    # ---------------------------------------------------------------------- #

    def _validate_all_deposit_data_entries(self) -> bool:
        """
        Validates that all enabled fields in all deposits have been filled.
        Returns True if all deposits are complete, False otherwise.
        """
        if not self.deposit_data:
            self.logger.debug("Deposit validation: no deposit data")
            return False

        for deposit in self.deposit_data:
            required: frozenset = DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE[deposit.tip_depozit]
            price_data = deposit.price_data
            missing_fields: list[str] = []
            for field_name in required:
                value = getattr(price_data, field_name, 0)
                if not value > 0:
                    missing_fields.append(field_name)
            if missing_fields:
                self.logger.debug(f"Deposit '{deposit.nume_depozit}' incomplete — missing: {missing_fields}")
                return False

        self.logger.debug("All deposit data entries validated successfully")
        return True

    # ---------------------------------------------------------------------- #

    def set_deposit_data(self, data: list[DepozitDataModel]) -> None:
        """Updates the deposit data with user-edited values"""
        self.deposit_data = data

    # ---------------------------------------------------------------------- #

    def get_error_files(self) -> set[str]:
        """Proceses CSV parse results and builds a set of filenames that had processing errors"""
        return {
            result.filename
            for result in self.csv_parse_results
            if result.status == CSVParseStatus.ERROR
        }
    
    # ---------------------------------------------------------------------- #
    # Known constraint !
    # Number of all CSV Files expected is: number of entries in Intrari_ xl file + number of entries in Aviz_ xl file ->
    # All entries in the Excels combined must be equal to the number of CSVs - duplicates exist and are filtered -> 
    # files are manually downloaded from SUMAL site
    
    def is_correct_csv_count(self) -> bool:
        """Determine if the correct number of CSVs were provided based on expected number of files from Excels"""
        return self.get_csv_count_per_excels() == len(self.csv_files_dict["all"])
    
    # ---------------------------------------------------------------------- #

    def can_start_parsing(self) -> bool:
        """Criteria that must be met in order to be able to start parsing"""
        return (
            not self.is_parsed and # Parsing already done — selecting a new folder resets this
            self.folder_path is not None and
            self.depozite_xl_row_count > 0 and # Some DepoziteEntries exist
            len(self.csv_files_dict["unique"]) > 0 and # Some CSVs exist
            len(self.xl_files_dict) == self.EXPECTED_XL_COUNT and # All control Excel files exist
            self.get_csv_count_per_excels() == len(self.csv_files_dict["all"]) # All expected CSVs exist
        )

    # ---------------------------------------------------------------------- #

    def can_generate_reports(self) -> bool:
        """Criteria that must be met in order to be able to generate reports"""
        # First check basic parsing requirements
        if not (self.is_parsed and len(self.notices) > 0 and len(self.get_error_files()) == 0):
            return False
        
        # Check if all deposit data has prices filled
        return self._validate_all_deposit_data_entries()
    
    # ---------------------------------------------------------------------- #
    
    def get_csv_count_per_excels(self) -> int:
        """Determine the number of expected CSV count based on the Excels Intrari_ and Aviz_"""
        return self.intrari_xl_row_count + self.aviz_xl_row_count
    
    # ---------------------------------------------------------------------- #

