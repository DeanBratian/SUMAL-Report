"""Interactive HTML report — replaces the Excel workbook.

One self-contained .html file (inline CSS/JS, no external requests): all notice
data is embedded as JSON and ALL price math runs in the browser, ported 1:1 from
report_generator._populate_notice_totals / _aggregate_category_statistics. The
"Depozite & prețuri" tab lets the user type unit prices for exactly the deposits
the notices reference; every money figure recalculates live. Prices persist in
localStorage per period and can be exported back as deposit_prices.json so the
next backend run picks them up. Without prices, every volume/count figure still
renders — only money shows an em dash.
"""

import json
import os
from datetime import date, datetime

from core.config import APP_CONFIG, DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE
from core.logger import Logger
from core.models import TransportNoticeModel, DepozitDataModel

class HtmlReportGenerator:
    def __init__(self, logger: Logger):
        self.logger = logger

    # ---------------------------------------------------------------------- #

    def generate(
            self, notices: list[TransportNoticeModel], deposit_data: list[DepozitDataModel],
            start: date, end: date, output_path: str,
            prestari_codes: list[str] | None = None
        ) -> None:
        """Render the report. notices must be parsed+classified (infer_volume_totals
        done); deposit_data holds only deposits referenced by notices, with any
        already-known prices filled in."""
        payload = self._build_payload(notices, deposit_data, start, end, prestari_codes or [])

        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_template.html")
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()

        html = template.replace(
            "/*__PAYLOAD__*/", json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        self.logger.info(
            f"HTML report written: {output_path} "
            f"({len(notices)} notices, {len(deposit_data)} deposits, {len(html)} bytes)"
        )

    # ---------------------------------------------------------------------- #

    def _build_payload(
            self, notices: list[TransportNoticeModel], deposit_data: list[DepozitDataModel],
            start: date, end: date, prestari_codes: list[str]
        ) -> dict:
        return {
            "company": APP_CONFIG.NUME_OWN,
            "cui": APP_CONFIG.CUI_OWN,
            "period": {
                "start": start.strftime("%d.%m.%Y"),
                "end": end.strftime("%d.%m.%Y"),
                "key": f"{start.isoformat()}_{end.isoformat()}",
            },
            "generated_at": datetime.now().strftime(APP_CONFIG.TIME_FORMAT),
            "tax_rate": APP_CONFIG.TAX_RATE_IMPOZIT,
            "notices": [self._notice_dict(n) for n in notices],
            "deposits": [self._deposit_dict(d) for d in deposit_data],
            "prestari_codes": prestari_codes,
        }

    # ---------------------------------------------------------------------- #

    @staticmethod
    def _notice_dict(n: TransportNoticeModel) -> dict:
        t = n.totals
        return {
            "cod": n.cod_unic,
            "data": n.data_ora_emitere.strftime(APP_CONFIG.TIME_FORMAT_SHORT),
            "tip": n.type.name,
            "tip_label": str(n.type),
            "provenienta": n.provenienta,
            "transport": n.cap_tractor.strip(),
            "v_total": n.volum_total_aviz,
            "v_lr": t.volum_total_lemn_rotund,
            "v_lf": t.volum_total_lemn_foc,
            "v_ch": t.volum_total_cherestele,
            "specii_lr": t.volume_pe_specii_lemn_rotund,
            "specii_lf": t.volume_pe_specii_lemn_foc,
            "specii_ch": t.volume_pe_specii_cherestele,
        }

    # ---------------------------------------------------------------------- #

    @staticmethod
    def _deposit_dict(d: DepozitDataModel) -> dict:
        enabled = sorted(DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE[d.tip_depozit])
        return {
            "nume": d.nume_depozit,
            "tip": d.tip_depozit.name,
            "tip_label": str(d.tip_depozit),
            "sursa": str(d.sursa_depozit),
            "enabled_fields": enabled,
            "prices": {f: getattr(d.price_data, f) for f in enabled},
        }
