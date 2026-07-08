#CHECKED

from core.models import TransportNoticeModel, WoodItemModel
from core.enums import GoodType
from core.config import APP_CONFIG
from core.utils import float_to_display_str

class NoticeDetailsController:
    def __init__(self, notice: TransportNoticeModel):
        # Each NoticeDetailsWindow displays and owns a TransportNoticeModel
        self.notice: TransportNoticeModel = notice
    
    # ---------------------------------------------------------------------- #

    def get_title(self) -> str:
        """Returns cod unic from the owned notice"""
        return self.notice.cod_unic
    
    # ---------------------------------------------------------------------- #

    def get_loading_point(self) -> str:
        """Returns loading point string by merging localitate and adresa from the owned notice"""
        parts: list[str] = [
            self.notice.punct_incarcare_localitate,
            self.notice.punct_incarcare_adresa
        ]
        return ", ".join(filter(None, parts))

    # ---------------------------------------------------------------------- #

    def get_unloading_point(self) -> str:
        """Returns unloading point string by merging localitate and adresa from the owned notice"""
        parts: list[str] = [
            self.notice.punct_descarcare_localitate,
            self.notice.punct_descarcare_adresa
        ]
        return ", ".join(filter(None, parts))

    # ---------------------------------------------------------------------- #

    def get_validity_period(self) -> str:
        """Returns validity period string by merging data/ora emitere and valabil pana la from the owned notice"""
        emitere_str = self.notice.data_ora_emitere.strftime(APP_CONFIG.TIME_FORMAT)
        expirare_str = self.notice.valabil_pana_la.strftime(APP_CONFIG.TIME_FORMAT)
        return f"{emitere_str} → {expirare_str}"

    # ---------------------------------------------------------------------- #

    def get_emitent_data(self) -> str:
        """Returns emitent data string by merging nume, CUI and J from the owned notice"""
        name = self.notice.emitent_nume
        cui = self.notice.emitent_cui
        reg_com = self.notice.emitent_reg_com

        details: str = ", ".join(filter(None, [cui, reg_com]))
        if details:
            return f"{name} [{details}]"
        return name

    # ---------------------------------------------------------------------- #

    def get_destinatar_data(self) -> str:
        """Returns destinatar data string by merging nume, CUI and J from the owned notice"""
        name = self.notice.destinatar_nume
        cui = self.notice.destinatar_cui
        reg_com = self.notice.destinatar_reg_com

        details: str = ", ".join(filter(None, [cui, reg_com]))
        if details:
            return f"{name} [{details}]"
        return name

    # ---------------------------------------------------------------------- #

    def get_notice_info_data(self) -> dict:
        """Returns the notice info data from the owned notice"""
        return {
            "emitent": self.get_emitent_data(),
            "destinatar": self.get_destinatar_data(),
            "provenienta": self.notice.provenienta,
            "punct_incarcare": self.get_loading_point(),
            "punct_descarcare": self.get_unloading_point(),
            "valabilitate": self.get_validity_period(),
            "volum_total": float_to_display_str(self.notice.volum_total_aviz),
            "transport": self.notice.cap_tractor,
            "tip": str(self.notice.type)
        }
    
    # ---------------------------------------------------------------------- #

    def get_volume_breakdown(self) -> dict[str, str]:
        """Get volume breakdown with formatted strings ready for display."""
        totals = self.notice.totals
        breakdown: dict[str, str] = {}
        if totals.volum_total_lemn_rotund > 0.0:
            breakdown[GoodType.LEMN_ROTUND] = float_to_display_str(totals.volum_total_lemn_rotund)
        if totals.volum_total_lemn_foc > 0.0:
            breakdown[GoodType.LEMN_FOC] = float_to_display_str(totals.volum_total_lemn_foc)
        if totals.volum_total_cherestele > 0.0:
            breakdown[GoodType.CHERESTELE] = float_to_display_str(totals.volum_total_cherestele)
        return breakdown

    # ---------------------------------------------------------------------- #

    def get_wood_items_table_data(self) -> list[WoodItemModel]:
        """Returns the wood items data from the owned notice"""
        return self.notice.wood_items