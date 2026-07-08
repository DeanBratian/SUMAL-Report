import pytest
from controllers.notice_details_controller import NoticeDetailsController
from core.enums import NoticeType, GoodType
from core.utils import float_to_display_str
from tests.conftest import make_notice, make_wood_item

@pytest.fixture
def ctrl():
    notice = make_notice()
    notice.infer_volume_totals()
    notice.type = NoticeType.INTRARE_DIN_PARTIDA_PROPRIE
    return NoticeDetailsController(notice)

# ---------------------------------------------------------------------- #

class TestGetTitle:

    def test_returns_cod_unic(self, ctrl):
        assert ctrl.get_title() == ctrl.notice.cod_unic

    # ---------------------------------------------------------------------- #

    def test_custom_cod_unic(self):
        notice = make_notice(cod_unic="TEST_CODE_123")
        c = NoticeDetailsController(notice)
        assert c.get_title() == "TEST_CODE_123"

# ---------------------------------------------------------------------- #

class TestPoints:

    def test_loading_point_merges_fields(self, ctrl):
        result = ctrl.get_loading_point()
        assert ctrl.notice.punct_incarcare_localitate in result
        assert ctrl.notice.punct_incarcare_adresa in result
        assert ", " in result

    # ---------------------------------------------------------------------- #

    def test_unloading_point_merges_fields(self, ctrl):
        result = ctrl.get_unloading_point()
        assert ctrl.notice.punct_descarcare_localitate in result
        assert ctrl.notice.punct_descarcare_adresa in result

    # ---------------------------------------------------------------------- #

    def test_loading_point_skips_empty_parts(self):
        notice = make_notice(punct_incarcare_localitate = "Mures", punct_incarcare_adresa = "")
        c = NoticeDetailsController(notice)
        assert c.get_loading_point() == "Mures"

    # ---------------------------------------------------------------------- #

    def test_unloading_point_skips_empty_parts(self):
        notice = make_notice(punct_descarcare_localitate = "", punct_descarcare_adresa = "Strada X")
        c = NoticeDetailsController(notice)
        assert c.get_unloading_point() == "Strada X"

    # ---------------------------------------------------------------------- #

    def test_both_empty_returns_empty(self):
        notice = make_notice(punct_incarcare_localitate = "", punct_incarcare_adresa = "")
        c = NoticeDetailsController(notice)
        assert c.get_loading_point() == ""

# ---------------------------------------------------------------------- #

class TestValidityPeriod:

    def test_format(self, ctrl):
        result = ctrl.get_validity_period()
        assert "→" in result
        assert "08-12-2025 16:57:38" in result
        assert "09-12-2025 16:57:38" in result

# ---------------------------------------------------------------------- #

class TestPartyData:

    def test_emitent_with_details(self, ctrl):
        result = ctrl.get_emitent_data()
        assert ctrl.notice.emitent_nume in result
        assert ctrl.notice.emitent_cui in result
        assert "[" in result

    # ---------------------------------------------------------------------- #

    def test_destinatar_with_details(self, ctrl):
        result = ctrl.get_destinatar_data()
        assert ctrl.notice.destinatar_nume in result
        assert "[" in result

    # ---------------------------------------------------------------------- #

    def test_emitent_without_details(self):
        notice = make_notice(emitent_cui = "", emitent_reg_com = "")
        c = NoticeDetailsController(notice)
        result = c.get_emitent_data()
        assert "[" not in result
        assert result == notice.emitent_nume

    # ---------------------------------------------------------------------- #

    def test_destinatar_without_details(self):
        notice = make_notice(destinatar_cui = "", destinatar_reg_com = "")
        c = NoticeDetailsController(notice)
        result = c.get_destinatar_data()
        assert "[" not in result

# ---------------------------------------------------------------------- #

class TestNoticeInfoData:

    def test_returns_all_keys(self, ctrl):
        data = ctrl.get_notice_info_data()
        expected_keys = {
            "emitent", "destinatar", "provenienta", "punct_incarcare",
            "punct_descarcare", "valabilitate", "volum_total", "transport", "tip"
        }
        assert set(data.keys()) == expected_keys

    # ---------------------------------------------------------------------- #

    def test_tip_is_string(self, ctrl):
        data = ctrl.get_notice_info_data()
        assert isinstance(data["tip"], str)
        assert data["tip"] == str(NoticeType.INTRARE_DIN_PARTIDA_PROPRIE)

    # ---------------------------------------------------------------------- #

    def test_volum_total_matches_notice(self, ctrl):
        data = ctrl.get_notice_info_data()
        assert data["volum_total"] == float_to_display_str(ctrl.notice.volum_total_aviz)

# ---------------------------------------------------------------------- #

class TestVolumeBreakdown:

    def test_empty_when_no_items(self, ctrl):
        # Default notice has no wood items
        assert ctrl.get_volume_breakdown() == {}

    # ---------------------------------------------------------------------- #

    def test_single_type(self):
        notice = make_notice(volum_total_aviz = 3.0)
        notice.wood_items = [make_wood_item(sortiment = "Lemn rotund", volum_mc = 3.0)]
        notice.infer_volume_totals()
        c = NoticeDetailsController(notice)

        breakdown = c.get_volume_breakdown()
        assert str(GoodType.LEMN_ROTUND) in breakdown
        assert breakdown[str(GoodType.LEMN_ROTUND)] == "3"
        assert len(breakdown) == 1

    # ---------------------------------------------------------------------- #

    def test_mixed_types(self):
        notice = make_notice(volum_total_aviz = 5.0)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 2.0),
            make_wood_item(sortiment = "Lemn de foc", volum_mc = 3.0, nr_crt = 2)
        ]
        notice.infer_volume_totals()
        c = NoticeDetailsController(notice)

        breakdown = c.get_volume_breakdown()
        assert len(breakdown) == 2
        assert str(GoodType.LEMN_ROTUND) in breakdown
        assert str(GoodType.LEMN_FOC) in breakdown

    # ---------------------------------------------------------------------- #

    def test_zero_volume_excluded(self):
        notice = make_notice(volum_total_aviz = 2.0)
        notice.wood_items = [make_wood_item(sortiment = "Lemn rotund", volum_mc = 2.0)]
        notice.infer_volume_totals()
        c = NoticeDetailsController(notice)

        breakdown = c.get_volume_breakdown()
        assert str(GoodType.LEMN_FOC) not in breakdown
        assert str(GoodType.CHERESTELE) not in breakdown

# ---------------------------------------------------------------------- #

class TestWoodItemsTableData:

    def test_returns_wood_items(self):
        notice = make_notice()
        notice.wood_items = [make_wood_item(), make_wood_item(nr_crt = 2, specie = "Fag")]
        c = NoticeDetailsController(notice)

        result = c.get_wood_items_table_data()
        assert result is notice.wood_items
        assert len(result) == 2

    # ---------------------------------------------------------------------- #

    def test_empty_items(self):
        notice = make_notice()
        notice.wood_items = []
        c = NoticeDetailsController(notice)
        assert c.get_wood_items_table_data() == []
