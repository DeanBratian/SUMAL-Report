"""Headless replacement for the old deposit pricing dialog.

Prices live in a per-period deposit_prices.json inside the run folder:
    { "<nume depozit>": { "p_iesire_lr_mc": 120.0, ... }, ... }

Only the fields enabled for the deposit's type are read (see
DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE). The file is (re)written on every sync so
newly detected deposits appear automatically with their fields at 0 while
already-entered values are preserved. Fields still at 0 are reported missing.
"""

import json
import os

from core.config import DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE
from core.logger import Logger
from core.models import DepozitDataModel

PRICES_FILENAME = "deposit_prices.json"

def sync_and_apply(folder: str, deposit_data: list[DepozitDataModel], logger: Logger) -> list[str]:
    """Merge deposit_prices.json with the detected deposits, apply the values to
    deposit_data and rewrite the file. Returns 'deposit: field' entries still unfilled."""
    path = os.path.join(folder, PRICES_FILENAME)

    saved: dict[str, dict[str, float]] = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)

    merged: dict[str, dict[str, float]] = {}
    missing: list[str] = []

    for deposit in deposit_data:
        enabled = DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE[deposit.tip_depozit]
        saved_prices = saved.get(deposit.nume_depozit, {})
        merged_prices: dict[str, float] = {}
        for field_name in sorted(enabled):
            value = float(saved_prices.get(field_name, 0) or 0)
            merged_prices[field_name] = value
            setattr(deposit.price_data, field_name, value)
            if not value > 0:
                missing.append(f"{deposit.nume_depozit}: {field_name}")
        merged[deposit.nume_depozit] = merged_prices

    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    if missing:
        logger.warning(f"Deposit prices incomplete ({len(missing)} fields at 0) in {path}")
    else:
        logger.info(f"Deposit prices complete for {len(merged)} deposits from {path}")
    return missing
