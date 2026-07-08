from os.path import splitext
import re

from core.config import VOLUME_PRECISION

def normalize_field(field):
    """Returns a default value for each expected field types"""
    if field.type is str:
        return ""
    elif field.type is int:
        return 0
    elif field.type is float:
        return 0.0
    else:
        return None

# ---------------------------------------------------------------------- #

def extract_base_name(filename: str) -> str:
    """Extracts notice id from a notice CSV file name
    AP25001460001000497311251450_08_12_2025_16_57_38.csv -> AP25001460001000497311251450"""
    name, _ = splitext(filename)
    # Match everything before _dd_mm_yyyy
    match = re.match(r"^(.*?)(?:_\d{2}_\d{2}_\d{4})", name)
    if match:
        return match.group(1)
    return name

# ---------------------------------------------------------------------- #

def refresh_style(*widgets):
    """Force QSS re-evaluation on one or more widgets after a property change."""
    for w in widgets:
        w.style().unpolish(w)
        w.style().polish(w)

# ---------------------------------------------------------------------- #

def float_to_display_str(value: float) -> str:
    """Format a measurement (volume m3, dimensions, price) for UI display.
    SUMAL CSV inputs are 6-decimal strings, so values never carry meaningful
    precision below the 6th decimal. This formatter prints the real value at
    up to 6 decimals, never truncating real digits, and strips trailing zeros
    so '10.726900' shows as '10.7269' and '5.000000' shows as '5'.
    """
    formatted = f"{value:.{VOLUME_PRECISION}f}".rstrip("0").rstrip(".")
    return formatted if formatted else "0"

