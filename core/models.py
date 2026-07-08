from dataclasses import dataclass, field
from datetime import datetime
from core.enums import (
    NoticeType, GoodType, DepositType, CSVParseStatus,
    DepozitSource, SUMALDepositType,
)
from core.config import APP_CONFIG, VOLUME_PRECISION

@dataclass
class WoodItemModel:
    """Model for one entry in a notice. Every TransportNoticeModel has at at least 1 WoodItemModel"""
    nr_crt: int = field(metadata={"csv_column": "Nr.Crt."})
    grupa_specii: str = field(metadata={"csv_column": "Grupa de specii"})
    specie: str = field(metadata={"csv_column": "Specie"})
    sortiment: str = field(metadata={"csv_column": "Sortiment"})
    subsortiment: str = field(metadata={"csv_column": "Subsortiment"})
    nr_bucati: int = field(metadata={"csv_column": "Nr. Bucati"})
    lungime: float = field(metadata={"csv_column": "Lungime(m)"})
    latime: float = field(metadata={"csv_column": "Latime(m)"})
    inaltime: float = field(metadata={"csv_column": "Inaltime(m)"})
    diametru: float = field(metadata={"csv_column": "Diametru(cm)"})
    volum_mc: float = field(metadata={"csv_column": "Volum(mc)"})
    nume_proprietar: str = field(metadata={"csv_column": "Nume proprietar"})
    cnp_proprietar: str = field(metadata={"csv_column": "Cnp proprietar"})
    detalii_masa_lemnoasa: str = field(metadata={"csv_column": "Detalii masa lemnoasa"})
    container_id: str = field(metadata={"csv_column": "Identificator container"})

# ---------------------------------------------------------------------- #

@dataclass
class TransportNoticeModel:
    """Model for a transport notice. Has totals and other objects"""
    certificare: str = field(metadata={"csv_column": "Certificare"})
    cod_unic: str = field(metadata={"csv_column": "Cod unic"})
    data_ora_emitere: datetime = field(metadata={"csv_column": "Data si ora emiterii codului unic"})
    valabil_pana_la: datetime = field(metadata={"csv_column": "Valabil pana la data/ora"})
    provenienta: str = field(metadata={"csv_column": "Provenienta"})
    emitent_nume: str = field(metadata={"csv_column": "Emitent - nume"})
    emitent_cui: str = field(metadata={"csv_column": "Emitent - CUI"})
    emitent_reg_com: str = field(metadata={"csv_column": "Emitent - Nr. Reg. Com."})
    emitent_localitate: str = field(metadata={"csv_column": "Emitent - Localitate"})
    emitent_judet: str = field(metadata={"csv_column": "Emitent - Judet"})
    emitent_adresa: str = field(metadata={"csv_column": "Emitent - Adresa"})
    punct_incarcare_judet: str = field(metadata={"csv_column": "Punct incarcare - Judet"})
    punct_incarcare_localitate: str = field(metadata={"csv_column": "Punct incarcare - Localitate"})
    punct_incarcare_adresa: str = field(metadata={"csv_column": "Punct incarcare - Adresa"})
    destinatar_nume: str = field(metadata={"csv_column": "Destinatar - Nume"})
    destinatar_cui: str = field(metadata={"csv_column": "Destinatar - CUI/CNP"})
    destinatar_reg_com: str = field(metadata={"csv_column": "Destinatar - Nr. Reg. Com."})
    destinatar_localitate: str = field(metadata={"csv_column": "Destinatar - Localitate"})
    destinatar_judet: str = field(metadata={"csv_column": "Destinatar - Judet"})
    destinatar_adresa: str = field(metadata={"csv_column": "Destinatar - Adresa"})
    punct_descarcare_depozit: str = field(metadata={"csv_column": "Punct descarcare - Depozit"})
    punct_descarcare_tara: str = field(metadata={"csv_column": "Punct descarcare - Tara"})
    punct_descarcare_judet: str = field(metadata={"csv_column": "Punct descarcare - Judet"})
    punct_descarcare_localitate: str = field(metadata={"csv_column": "Punct descarcare - Localitate"})
    punct_descarcare_adresa: str = field(metadata={"csv_column": "Punct descarcare - Adresa"})
    vama: str = field(metadata={"csv_column": "Vama"})
    identificator_sofer: str = field(metadata={"csv_column": "Identificator sofer"})
    mijloc_transport: str = field(metadata={"csv_column": "Mijloc transport"})
    cap_tractor: str = field(metadata={"csv_column": "Cap tractor"})
    remorca: str = field(metadata={"csv_column": "Remorca"})
    km_bord: int = field(metadata={"csv_column": "Nr. Km la bord"})
    volum_total_aviz: float = field(metadata={"csv_column": "Volum total aviz"})
    wood_items: list[WoodItemModel] = field(default_factory = list)

    # ---------------------------------------------------------------------- #

    class NoticeTotalsModel:
        """Stores all calculated totals and prices for a transport notice"""
        def __init__(self):
            # Volume totals by good type, populated at parse-time in infer_volume_totals
            self.volum_total_lemn_rotund: float = 0.0
            self.volum_total_lemn_foc: float = 0.0
            self.volum_total_cherestele: float = 0.0

            # Volumes by species, populated at parse-time in infer_volume_totals
            # Key is specie, value is the total value for that specie
            # all entries here should equal volum_total_ for that good
            # {"Brad" : 2,33, "Fag" : 10.45 }
            self.volume_pe_specii_lemn_rotund: dict[str, float] = {}
            self.volume_pe_specii_lemn_foc: dict[str, float] = {}
            self.volume_pe_specii_cherestele: dict[str, float] = {}

            # Prices per m³ (from deposit data) - intrare / iesire deduced
            # populated at report generation in _populate_notice_totals
            self.pret_mc_lemn_rotund: int = 0
            self.pret_mc_lemn_foc: int = 0
            self.pret_mc_cherestele: int = 0
            self.pret_mc_transport: int = 0
            self.pret_mc_exploatare: int = 0

            # Calculated totals
            # populated at report generation in _populate_notice_totals
            self.pret_total_lemn_rotund: float = 0.0
            self.pret_total_lemn_foc: float = 0.0
            self.pret_total_cherestele: float = 0.0
            self.pret_total_materiale: float = 0.0
            self.pret_total_transport: float = 0.0
            self.pret_total_exploatare: float = 0.0
            self.pret_total_aviz: float = 0.0
            self.valoare_impozit_punere_in_piata: float = 0.0

    # ---------------------------------------------------------------------- #

    def __post_init__(self):
        self.type: NoticeType | None = None
        self.totals = TransportNoticeModel.NoticeTotalsModel()

    # ---------------------------------------------------------------------- #

    def infer_notice_type(self, depozite_entries: list['DepoziteExcelModel']) -> None:
        """Gets list[DepoziteExcelModel] in depozite_entries, the deposits as they are from the Depozite Excel"""
        depozit_lookup: dict[str, str] = {
            d.nume_depozit: d.tip_depozit
            for d in depozite_entries
        }
        # Destinatar data
        destinatar_is_own = (
            self.destinatar_nume == APP_CONFIG.NUME_OWN and 
            self.destinatar_cui == APP_CONFIG.CUI_OWN and
            self.destinatar_adresa == APP_CONFIG.ADRESA_OWN
        )
        destinatar_is_other = (
            self.destinatar_nume != APP_CONFIG.NUME_OWN and
            self.destinatar_cui != APP_CONFIG.CUI_OWN and
            self.destinatar_adresa != APP_CONFIG.ADRESA_OWN
        )
        # Emitent data
        emitent_is_own = (
            self.emitent_nume == APP_CONFIG.NUME_OWN and 
            self.emitent_cui == APP_CONFIG.CUI_OWN and
            self.emitent_adresa == APP_CONFIG.ADRESA_OWN
        )
        emitent_is_other = (
            self.emitent_nume != APP_CONFIG.NUME_OWN and 
            self.emitent_cui != APP_CONFIG.CUI_OWN and
            self.emitent_adresa != APP_CONFIG.ADRESA_OWN
        )
        # Punct descarcare
        descarcare_in_depozit_own = self.punct_descarcare_depozit == APP_CONFIG.DEPOZIT_OWN
        # Provenienta / tip depozit
        deposit_type = depozit_lookup.get(self.provenienta)

        # INTRARE_DIN_PARTIDA_PROPRIE
        if (destinatar_is_own and emitent_is_own and descarcare_in_depozit_own and
            deposit_type == SUMALDepositType.DEPOZIT_TEMPORAR_LR):
            self.type = NoticeType.INTRARE_DIN_PARTIDA_PROPRIE
            return

        # INTRARE_DIN_SURSA_EXTERNA
        if (destinatar_is_own and emitent_is_other and descarcare_in_depozit_own and
            deposit_type is None):
            self.type = NoticeType.INTRARE_DIN_SURSA_EXTERNA
            return

        # IESIRE_DIN_DEPOZIT_PRINCIPAL
        if (destinatar_is_other and emitent_is_own and not descarcare_in_depozit_own and
            self.provenienta == APP_CONFIG.DEPOZIT_OWN and deposit_type == SUMALDepositType.DEPOZIT):
            self.type = NoticeType.IESIRE_DIN_DEPOZIT_PRINCIPAL
            return

        # IESIRE_DIN_DEPOZIT_LR
        if (destinatar_is_other and emitent_is_own and not descarcare_in_depozit_own and
            deposit_type == SUMALDepositType.DEPOZIT_TEMPORAR_LR):
            self.type = NoticeType.IESIRE_DIN_DEPOZIT_LR
            return

        self.type = NoticeType.UNKNOWN

    # ---------------------------------------------------------------------- #
    
    def infer_volume_totals(self) -> list[str]:
        """Build totals dictionary organized by good type, then by species with volumes.
        Returns a list of unknown sortiment names (empty if all are known)"""

        def infer_good_type(sortiment: str) -> GoodType:
            """Infer the type of the good. From SUMAL we have 'Lemn rotund', 'Lemn de foc' and "Cherestele",
            which are known types"""
            if sortiment == "Lemn rotund":
                return GoodType.LEMN_ROTUND
            elif sortiment == "Lemn de foc":
                return GoodType.LEMN_FOC
            elif sortiment == "Cherestele":
                return GoodType.CHERESTELE
            return GoodType.UNKNOWN

        # ---------------------------------------------------------------------- #

        # Detect unknown sortiments in the notice
        unknown_sortiments: set[str] = set()
        # Total volumes for each good type
        volum_lemn_rotund = volum_lemn_foc = volum_cherestele = 0.0
        # Per species volume for each good type
        specii_lemn_rotund: dict[str, float] = {}
        specii_lemn_foc: dict[str, float] = {}
        specii_cherestele: dict[str, float] = {}

        for item in self.wood_items:
            good_type = infer_good_type(item.sortiment)
            if good_type == GoodType.UNKNOWN:
                unknown_sortiments.add(item.sortiment)
                continue
            specie = item.specie
            if good_type == GoodType.LEMN_ROTUND:
                volum_lemn_rotund += item.volum_mc
                specii_lemn_rotund[specie] = specii_lemn_rotund.get(specie, 0.0) + item.volum_mc
            elif good_type == GoodType.LEMN_FOC:
                volum_lemn_foc += item.volum_mc
                specii_lemn_foc[specie] = specii_lemn_foc.get(specie, 0.0) + item.volum_mc
            elif good_type == GoodType.CHERESTELE:
                volum_cherestele += item.volum_mc
                specii_cherestele[specie] = specii_cherestele.get(specie, 0.0) + item.volum_mc

        # Snap once at the end — both good-type totals and per-species dicts.
        self.totals.volum_total_lemn_rotund = round(volum_lemn_rotund, VOLUME_PRECISION)
        self.totals.volum_total_lemn_foc = round(volum_lemn_foc, VOLUME_PRECISION)
        self.totals.volum_total_cherestele = round(volum_cherestele, VOLUME_PRECISION)

        self.totals.volume_pe_specii_lemn_rotund = {specie: round(volum, VOLUME_PRECISION) for specie, volum in specii_lemn_rotund.items()}
        self.totals.volume_pe_specii_lemn_foc = {specie: round(volum, VOLUME_PRECISION) for specie, volum in specii_lemn_foc.items()}
        self.totals.volume_pe_specii_cherestele = {specie: round(volum, VOLUME_PRECISION) for specie, volum in specii_cherestele.items()}

        return sorted(unknown_sortiments)

    # ---------------------------------------------------------------------- #

    def validate_volumes(self, logger) -> bool:
        """Ensure wood items, totals, and aviz volume match exactly at 6-decimal source precision"""
        raw_items_sum = sum(item.volum_mc for item in self.wood_items)
        raw_totals_sum = (
            self.totals.volum_total_lemn_rotund
            + self.totals.volum_total_lemn_foc
            + self.totals.volum_total_cherestele
        )
        # Snap accumulated sums back to the 6-decimal source precision so float
        # addition noise (e.g. 0.1 + 0.2 == 0.30000000000000004) is removed.
        # volum_total_aviz is NOT rounded — it's a single parse from CSV with no
        # arithmetic applied, so it already is the exact source value.
        total_from_items = round(raw_items_sum, VOLUME_PRECISION)
        total_from_notice_totals = round(raw_totals_sum, VOLUME_PRECISION)

        logger.debug(
            f"[validate_volumes] cod={self.cod_unic}\n"
            f" volum_total_aviz               = {self.volum_total_aviz!r}\n"
            f" sum(wood_items.volum_mc) raw   = {raw_items_sum!r}\n"
            f" sum(wood_items)  (round 6)     = {total_from_items!r}\n"
            f" totals.volum_total_lemn_rotund = {self.totals.volum_total_lemn_rotund!r}\n"
            f" totals.volum_total_lemn_foc    = {self.totals.volum_total_lemn_foc!r}\n"
            f" totals.volum_total_cherestele  = {self.totals.volum_total_cherestele!r}\n"
            f" sum(totals) raw                = {raw_totals_sum!r}\n"
            f" sum(totals)      (round 6)     = {total_from_notice_totals!r}\n"
            f" items == aviz ? {total_from_items == self.volum_total_aviz}  |  totals == aviz ? {total_from_notice_totals == self.volum_total_aviz}"
        )

        if total_from_items != self.volum_total_aviz:
            return False
        if total_from_notice_totals != self.volum_total_aviz:
            return False
        return True

# ---------------------------------------------------------------------- #

@dataclass
class IntrariExcelModel:
    numar_nir: int = field(metadata={"excel_column": "Număr NIR"})
    companie_emitenta: str = field(metadata={"excel_column": "Companie emitenta"})
    cod_aviz: str = field(metadata={"excel_column": "Cod aviz"})
    data_nir: datetime = field(metadata={"excel_column": "Dată NIR"})
    grupe_specii: str = field(metadata={"excel_column": "Grupe specii"})
    volum_mc: float = field(metadata={"excel_column": "Volum (mc)"})
    status: str = field(metadata={"excel_column": "Status"})

# ---------------------------------------------------------------------- #

@dataclass
class AvizExcelModel:
    cod_aviz: str = field(metadata={"excel_column": "Cod Aviz"})
    tip_transport: str = field(metadata={"excel_column": "Tip Transport"})
    provenienta: str = field(metadata={"excel_column": "Provenienta"})
    mijloc_transport: str = field(metadata={"excel_column": "Mijloc transport"})
    numar_mijloc_transport: str = field(metadata={"excel_column": "Numar mijloc transport"})
    categorie_transport: str = field(metadata={"excel_column": "Categorie transport"})
    status: str = field(metadata={"excel_column": "Status"})
    volum_total_mc: float = field(metadata={"excel_column": "Volum total aviz(mc)"})
    data_emitere: datetime = field(metadata={"excel_column": "Data emitere"})

# ---------------------------------------------------------------------- #

@dataclass
class DepoziteExcelModel:
    nume_depozit: str = field(metadata={"excel_column": "Nume depozit"})
    latitudine: float = field(metadata={"excel_column": "Latitudine"})
    longitudine: float = field(metadata={"excel_column": "Longitudine"})
    tip_depozit: str = field(metadata={"excel_column": "Tip depozit"})
    status_depozit: str = field(metadata={"excel_column": "Status depozit"})
    judet: str = field(metadata={"excel_column": "Judet"})

# ---------------------------------------------------------------------- #

class DepozitDataModel:
    class PriceData:
        """Models the price data for each deposit, user inputs that are used to generate the reports"""
        def __init__(self):
            self.p_intrare_lr_mc: int = 0
            self.p_intrare_lf_mc: int = 0
            self.p_intrare_ch_mc: int = 0

            self.p_iesire_lr_mc: int = 0
            self.p_iesire_lf_mc: int = 0
            self.p_iesire_ch_mc: int = 0

            self.p_transport_mc: int = 0
            self.p_expl_mc: int = 0

    # ---------------------------------------------------------------------- #

    def __init__(self, nume_depozit: str, tip_depozit: str, sursa_depozit: DepozitSource):
        """DepozitDataModel entries are custom user entries saved and used in reports
        -> derived from DepoziteExcelModel entries and extracted unknown from notices"""
        self.nume_depozit: str = nume_depozit
        self.tip_depozit: DepositType = self.infer_deposit_type(tip_depozit)
        self.sursa_depozit: DepozitSource = sursa_depozit
        # User provided buy/sell prices for all goods
        self.price_data: DepozitDataModel.PriceData = DepozitDataModel.PriceData()
    
    # ---------------------------------------------------------------------- #

    def infer_deposit_type(self, tip_depozit: str) -> DepositType:
        """Infer the type of the deposit. From SUMAL we have 'Depozit Temporar LR' and 'Depozit',
        which are known types, 'Depozit extern' is used when the deposit is unknown in SUMAL and extracted from a notice"""
        if tip_depozit == "Depozit Temporar LR":
            return DepositType.DEPOZIT_TEMPORAR_LR
        elif tip_depozit == "Depozit":
            return DepositType.DEPOZIT_PRINCIPAL
        elif tip_depozit == "Depozit extern":
            return DepositType.DEPOZIT_EXTERN
        return DepositType.UNKNOWN

# ---------------------------------------------------------------------- #

class CSVParseResult:
    """CSV Parser result model, status for each file and error"""
    def __init__(self, filename: str, status: CSVParseStatus, error: str = ""):
        self.filename: str = filename
        self.status: CSVParseStatus = status
        self.error: str = error
