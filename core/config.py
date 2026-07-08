# CHECKED

from dataclasses import dataclass
from core.enums import DepositType

@dataclass(frozen = True)
class AppConfig:
    """Immutable application-wide configuration: company identity, tax rates, date formats."""
    NUME_OWN: str
    CUI_OWN: str
    ADRESA_OWN: str
    DEPOZIT_OWN: str
    TAX_RATE_IMPOZIT: float
    TIME_FORMAT: str
    TIME_FORMAT_SHORT: str

# ---------------------------------------------------------------------- #

APP_CONFIG = AppConfig(
    NUME_OWN = "Brat Valms Service Tur S.R.L.",
    CUI_OWN = "39164009",
    ADRESA_OWN = "Valenii De Mures, 99, -, Valenii De Mures",
    DEPOZIT_OWN = "VALENII DE MURES 95",
    TAX_RATE_IMPOZIT = 0.005,
    TIME_FORMAT = "%d-%m-%Y %H:%M:%S",
    TIME_FORMAT_SHORT = "%d-%m-%Y %H:%M"
)

# ---------------------------------------------------------------------- #

"""
Decimal precision policy
Volumes (m³) carry up to this many decimals in the SUMAL CSV source and must
never lose precision: every volume sum is snapped back to this many decimals.
"""
VOLUME_PRECISION = 6

"""
Monetary values (RON prices) are computed at full precision and rounded to this many
decimals only at the final aggregate / on display.
# """
PRICE_PRECISION = 2

# ---------------------------------------------------------------------- #

"""Dict of enabled fields for each type of deposit"""
DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE: dict[DepositType, frozenset] = {
    DepositType.DEPOZIT_TEMPORAR_LR: frozenset({
        "p_intrare_lr_mc",
        "p_intrare_lf_mc",
        "p_transport_mc",
        "p_iesire_lr_mc",
        "p_iesire_lf_mc",
        "p_expl_mc"
    }),
    DepositType.DEPOZIT_PRINCIPAL: frozenset({
        "p_iesire_lr_mc",
        "p_iesire_lf_mc",
        "p_iesire_ch_mc",
        "p_transport_mc"
    }),
    DepositType.DEPOZIT_EXTERN: frozenset({
        "p_intrare_lr_mc",
        "p_intrare_lf_mc",
        "p_intrare_ch_mc",
        "p_transport_mc"
    })
}
