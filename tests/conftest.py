import os
import sys
from datetime import datetime

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import (
    TransportNoticeModel, WoodItemModel, DepozitDataModel,
    DepoziteExcelModel
)
from core.enums import DepozitSource
from core.config import APP_CONFIG

def make_wood_item(**overrides) -> WoodItemModel:
    """Create a WoodItemModel with sensible defaults."""
    defaults = {
        "nr_crt": 1,
        "grupa_specii": "Rășinoase",
        "specie": "Brad",
        "sortiment": "Lemn rotund",
        "subsortiment": "Bustean gater",
        "nr_bucati": 5,
        "lungime": 4.0,
        "latime": 0.0,
        "inaltime": 0.0,
        "diametru": 28.0,
        "volum_mc": 2.5,
        "nume_proprietar": "",
        "cnp_proprietar": "",
        "detalii_masa_lemnoasa": "",
        "container_id": ""
    }
    defaults.update(overrides)
    return WoodItemModel(**defaults)

# ---------------------------------------------------------------------- #

def make_notice(**overrides) -> TransportNoticeModel:
    """Create a TransportNoticeModel with sensible defaults (own company as destinatar)."""
    defaults = {
        "certificare": "DA",
        "cod_unic": "AP25001460001000497311251450",
        "data_ora_emitere": datetime(2025, 12, 8, 16, 57, 38),
        "valabil_pana_la": datetime(2025, 12, 9, 16, 57, 38),
        "provenienta": "Test Depozit LR",
        "emitent_nume": APP_CONFIG.NUME_OWN,
        "emitent_cui": APP_CONFIG.CUI_OWN,
        "emitent_reg_com": "J26/123/2020",
        "emitent_localitate": "Valenii De Mures",
        "emitent_judet": "Mures",
        "emitent_adresa": APP_CONFIG.ADRESA_OWN,
        "punct_incarcare_judet": "Mures",
        "punct_incarcare_localitate": "Valenii De Mures",
        "punct_incarcare_adresa": "Strada Test",
        "destinatar_nume": APP_CONFIG.NUME_OWN,
        "destinatar_cui": APP_CONFIG.CUI_OWN,
        "destinatar_reg_com": "J26/123/2020",
        "destinatar_localitate": "Valenii De Mures",
        "destinatar_judet": "Mures",
        "destinatar_adresa": APP_CONFIG.ADRESA_OWN,
        "punct_descarcare_depozit": APP_CONFIG.DEPOZIT_OWN,
        "punct_descarcare_tara": "Romania",
        "punct_descarcare_judet": "Mures",
        "punct_descarcare_localitate": "Valenii De Mures",
        "punct_descarcare_adresa": "Strada Test",
        "vama": "",
        "identificator_sofer": "1234567890",
        "mijloc_transport": "Camion",
        "cap_tractor": "MS98LIR",
        "remorca": "MS99LIR",
        "km_bord": 12345.0,
        "volum_total_aviz": 5.0,
        "wood_items": []
    }
    defaults.update(overrides)
    return TransportNoticeModel(**defaults)

# ---------------------------------------------------------------------- #

def make_depozite_excel_entry(**overrides) -> DepoziteExcelModel:
    """Create a DepoziteExcelModel entry."""
    defaults = {
        "nume_depozit": "Test Depozit LR",
        "latitudine": 46.123,
        "longitudine": 24.456,
        "tip_depozit": "Depozit Temporar LR",
        "status_depozit": "Activ",
        "judet": "Mures"
    }
    defaults.update(overrides)
    return DepoziteExcelModel(**defaults)

# ---------------------------------------------------------------------- #

def make_deposit_data(
        name = "Test Depozit LR", tip = "Depozit Temporar LR",
        sursa = DepozitSource.EXCEL_SUMAL, **price_overrides
    ) -> DepozitDataModel:
    """Create a DepozitDataModel with optional price overrides."""
    dd = DepozitDataModel(name, tip, sursa)
    for key, val in price_overrides.items():
        setattr(dd.price_data, key, val)
    return dd
