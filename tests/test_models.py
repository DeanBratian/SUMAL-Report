import pytest
from unittest.mock import MagicMock
from core.models import DepozitDataModel
from core.enums import NoticeType, DepositType, DepozitSource
from core.config import APP_CONFIG
from tests.conftest import make_notice, make_wood_item, make_depozite_excel_entry

@pytest.fixture
def mock_depozit_lr():
    return [make_depozite_excel_entry()]

# ---------------------------------------------------------------------- #

@pytest.fixture
def mock_depozite_principal_and_lr():
    """Main deposit + LR deposit entries."""
    return [
        make_depozite_excel_entry(
            nume_depozit = APP_CONFIG.DEPOZIT_OWN,
            tip_depozit = "Depozit"
        ),
        make_depozite_excel_entry()
    ]

# ---------------------------------------------------------------------- #

class TestNoticeTypeInference:

    def test_intrare_din_partida_proprie(self, mock_depozit_lr):
        """Own-to-own with provenienta in LR deposit list -> INTRARE_DIN_PARTIDA_PROPRIE."""
        notice = make_notice(
            provenienta = "Test Depozit LR",
            emitent_nume = APP_CONFIG.NUME_OWN, emitent_cui = APP_CONFIG.CUI_OWN, emitent_adresa = APP_CONFIG.ADRESA_OWN,
            destinatar_nume = APP_CONFIG.NUME_OWN, destinatar_cui = APP_CONFIG.CUI_OWN,
            destinatar_adresa = APP_CONFIG.ADRESA_OWN, punct_descarcare_depozit = APP_CONFIG.DEPOZIT_OWN
        )
        notice.infer_notice_type(mock_depozit_lr)
        assert notice.type == NoticeType.INTRARE_DIN_PARTIDA_PROPRIE

    # ---------------------------------------------------------------------- #

    def test_intrare_din_sursa_externa(self, mock_depozit_lr):
        """External sender, own destinatar, provenienta NOT in deposit list -> INTRARE_DIN_SURSA_EXTERNA."""
        notice = make_notice(
            provenienta = "Depozit Extern Necunoscut",
            emitent_nume = "Alt SRL", emitent_cui = "12345678",
            emitent_adresa = "Alta adresa",
            destinatar_nume = APP_CONFIG.NUME_OWN, destinatar_cui = APP_CONFIG.CUI_OWN,
            destinatar_adresa = APP_CONFIG.ADRESA_OWN, punct_descarcare_depozit = APP_CONFIG.DEPOZIT_OWN
        )
        notice.infer_notice_type(mock_depozit_lr)
        assert notice.type == NoticeType.INTRARE_DIN_SURSA_EXTERNA

    # ---------------------------------------------------------------------- #

    def test_iesire_din_depozit_principal(self, mock_depozite_principal_and_lr):
        """Own emitter, external destinatar, provenienta = main deposit -> IESIRE_DIN_DEPOZIT_PRINCIPAL."""
        notice = make_notice(
            provenienta = APP_CONFIG.DEPOZIT_OWN,
            emitent_nume = APP_CONFIG.NUME_OWN, emitent_cui = APP_CONFIG.CUI_OWN, emitent_adresa = APP_CONFIG.ADRESA_OWN,
            destinatar_nume = "Client SRL", destinatar_cui = "99999999",
            destinatar_adresa = "Adresa client", punct_descarcare_depozit = "Depozit client"
        )
        notice.infer_notice_type(mock_depozite_principal_and_lr)
        assert notice.type == NoticeType.IESIRE_DIN_DEPOZIT_PRINCIPAL

    # ---------------------------------------------------------------------- #

    def test_iesire_din_depozit_lr(self, mock_depozit_lr):
        """Own emitter, external destinatar, provenienta in LR deposit -> IESIRE_DIN_DEPOZIT_LR."""
        notice = make_notice(
            provenienta = "Test Depozit LR",
            emitent_nume = APP_CONFIG.NUME_OWN, emitent_cui = APP_CONFIG.CUI_OWN, emitent_adresa = APP_CONFIG.ADRESA_OWN,
            destinatar_nume = "Client SRL", destinatar_cui = "99999999",
            destinatar_adresa = "Adresa client", punct_descarcare_depozit = "Depozit client"
        )
        notice.infer_notice_type(mock_depozit_lr)
        assert notice.type == NoticeType.IESIRE_DIN_DEPOZIT_LR

    # ---------------------------------------------------------------------- #

    def test_unknown_type_when_no_rules_match(self, mock_depozit_lr):
        """If no rules match, type should be UNKNOWN."""
        notice = make_notice(
            provenienta = "Necunoscut",
            emitent_nume = "Alt SRL", emitent_cui = "11111111", emitent_adresa = "Alta",
            destinatar_nume = "Alt2 SRL", destinatar_cui = "22222222",
            destinatar_adresa = "Alta2", punct_descarcare_depozit = "Undeva"
        )
        notice.infer_notice_type(mock_depozit_lr)
        assert notice.type == NoticeType.UNKNOWN

    # ---------------------------------------------------------------------- #

    def test_empty_depozite_list_external_still_works(self):
        """With empty deposit list, external source should still be detected."""
        notice = make_notice(
            provenienta = "Depozit Extern",
            emitent_nume = "Alt SRL", emitent_cui = "12345678",
            emitent_adresa = "Alta adresa",
            destinatar_nume = APP_CONFIG.NUME_OWN, destinatar_cui = APP_CONFIG.CUI_OWN,
            destinatar_adresa = APP_CONFIG.ADRESA_OWN, punct_descarcare_depozit = APP_CONFIG.DEPOZIT_OWN
        )
        notice.infer_notice_type([])
        assert notice.type == NoticeType.INTRARE_DIN_SURSA_EXTERNA

# ---------------------------------------------------------------------- #

class TestVolumeTotals:

    def test_single_lemn_rotund_item(self):
        notice = make_notice(volum_total_aviz = 2.5)
        notice.wood_items = [make_wood_item(sortiment="Lemn rotund", volum_mc=2.5, specie="Brad")]
        notice.infer_volume_totals()

        assert notice.totals.volum_total_lemn_rotund == 2.5
        assert notice.totals.volum_total_lemn_foc == 0.0
        assert notice.totals.volum_total_cherestele == 0.0
        assert notice.totals.volume_pe_specii_lemn_rotund == {"Brad": 2.5}

    # ---------------------------------------------------------------------- #

    def test_mixed_good_types(self):
        notice = make_notice(volum_total_aviz = 7.0)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 2.5, specie = "Brad"),
            make_wood_item(sortiment = "Lemn de foc", volum_mc = 3.0, specie = "Fag", nr_crt = 2),
            make_wood_item(sortiment = "Cherestele", volum_mc = 1.5, specie = "Stejar", nr_crt = 3)
        ]
        notice.infer_volume_totals()

        assert notice.totals.volum_total_lemn_rotund == 2.5
        assert notice.totals.volum_total_lemn_foc == 3.0
        assert notice.totals.volum_total_cherestele == 1.5

    # ---------------------------------------------------------------------- #

    def test_multiple_items_same_species_accumulate(self):
        notice = make_notice(volum_total_aviz = 5.0)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 2.5, specie = "Brad"),
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 2.5, specie = "Brad", nr_crt = 2)
        ]
        notice.infer_volume_totals()

        assert notice.totals.volum_total_lemn_rotund == 5.0
        assert notice.totals.volume_pe_specii_lemn_rotund == {"Brad": 5.0}

    # ---------------------------------------------------------------------- #

    def test_unknown_sortiment_returned_in_list(self):
        notice = make_notice()
        notice.wood_items = [make_wood_item(sortiment="Tip necunoscut")]

        unknown = notice.infer_volume_totals()
        assert unknown == ["Tip necunoscut"]

    # ---------------------------------------------------------------------- #

    def test_empty_wood_items_gives_zero_totals(self):
        notice = make_notice(volum_total_aviz = 0.0)
        notice.wood_items = []
        notice.infer_volume_totals()

        assert notice.totals.volum_total_lemn_rotund == 0.0
        assert notice.totals.volum_total_lemn_foc == 0.0
        assert notice.totals.volum_total_cherestele == 0.0

    # ---------------------------------------------------------------------- #

    def test_float_noise_in_good_type_total_snapped(self):
        """0.1 + 0.2 in float = 0.30000000000000004 — must be snapped to 0.3."""
        notice = make_notice(volum_total_aviz = 0.3)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 0.1, specie = "Brad"),
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 0.2, specie = "Fag", nr_crt = 2)
        ]
        notice.infer_volume_totals()
        assert notice.totals.volum_total_lemn_rotund == 0.3

    # ---------------------------------------------------------------------- #

    def test_float_noise_in_species_dict_snapped(self):
        """Same species summed across two items must be snapped to 6 decimals."""
        notice = make_notice(volum_total_aviz = 0.3)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 0.1, specie = "Brad"),
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 0.2, specie = "Brad", nr_crt = 2)
        ]
        notice.infer_volume_totals()
        assert notice.totals.volume_pe_specii_lemn_rotund == {"Brad": 0.3}

    # ---------------------------------------------------------------------- #

    def test_six_decimal_source_values_sum_clean_in_totals(self):
        """Realistic 6-decimal CSV values: raw float sum has noise, must round clean."""
        notice = make_notice(volum_total_aviz = 0.469134)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn de foc", volum_mc = 0.123456, specie = "Fag"),
            make_wood_item(sortiment = "Lemn de foc", volum_mc = 0.234567, specie = "Fag", nr_crt = 2),
            make_wood_item(sortiment = "Lemn de foc", volum_mc = 0.111111, specie = "Fag", nr_crt = 3)
        ]
        notice.infer_volume_totals()
        assert notice.totals.volum_total_lemn_foc == 0.469134
        assert notice.totals.volume_pe_specii_lemn_foc == {"Fag": 0.469134}

# ---------------------------------------------------------------------- #

class TestVolumeValidation:

    def test_valid_volumes(self):
        notice = make_notice(volum_total_aviz = 5.0)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 3.0),
            make_wood_item(sortiment = "Lemn de foc", volum_mc = 2.0, nr_crt = 2)
        ]
        notice.infer_volume_totals()
        assert notice.validate_volumes(MagicMock()) is True

    # ---------------------------------------------------------------------- #

    def test_mismatched_volumes(self):
        notice = make_notice(volum_total_aviz = 10.0)  # Wrong total
        notice.wood_items = [make_wood_item(sortiment = "Lemn rotund", volum_mc = 2.5)]
        notice.infer_volume_totals()
        assert notice.validate_volumes(MagicMock()) is False

    # ---------------------------------------------------------------------- #

    def test_floating_point_noise_snapped_at_6_decimals(self):
        """0.1 + 0.2 == 0.30000000000000004 in IEEE 754; snapping both sides to 6
        decimals removes the noise so exact equality holds at source precision."""
        notice = make_notice(volum_total_aviz = 0.3)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 0.1, specie = "Brad"),
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 0.2, specie = "Brad", nr_crt = 2)
        ]
        notice.infer_volume_totals()
        assert notice.validate_volumes(MagicMock()) is True

    # ---------------------------------------------------------------------- #

    def test_six_decimal_source_values_match_exactly(self):
        """Realistic case: 6-decimal CSV values that sum (in float) to a noisy
        result must still validate against the 6-decimal aviz total."""
        notice = make_notice(volum_total_aviz = 0.358023)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 0.123456, specie = "Fag"),
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 0.234567, specie = "Fag", nr_crt = 2)
        ]
        notice.infer_volume_totals()
        assert notice.validate_volumes(MagicMock()) is True

    # ---------------------------------------------------------------------- #

    def test_off_by_one_ulp_at_6_decimals_fails(self):
        """If items sum is genuinely off by 1 unit in the 6th decimal, validation fails."""
        notice = make_notice(volum_total_aviz = 0.358023)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 0.123456, specie = "Fag"),
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 0.234568, specie = "Fag", nr_crt = 2)
        ]
        notice.infer_volume_totals()
        assert notice.validate_volumes(MagicMock()) is False

# ---------------------------------------------------------------------- #

class TestDepozitDataModel:
    def test_lr_deposit_type(self):
        dd = DepozitDataModel("Test LR", "Depozit Temporar LR", DepozitSource.EXCEL_SUMAL)
        assert dd.tip_depozit == DepositType.DEPOZIT_TEMPORAR_LR

    # ---------------------------------------------------------------------- #

    def test_principal_deposit_type(self):
        dd = DepozitDataModel("Test Principal", "Depozit", DepozitSource.EXCEL_SUMAL)
        assert dd.tip_depozit == DepositType.DEPOZIT_PRINCIPAL

    # ---------------------------------------------------------------------- #

    def test_extern_deposit_type(self):
        dd = DepozitDataModel("Test Extern", "Depozit extern", DepozitSource.AVIZE)
        assert dd.tip_depozit == DepositType.DEPOZIT_EXTERN

    # ---------------------------------------------------------------------- #

    def test_unknown_deposit_type_returns_unknown(self):
        dd = DepozitDataModel("Bad", "Tip Necunoscut", DepozitSource.EXCEL_SUMAL)
        assert dd.tip_depozit == DepositType.UNKNOWN

    # ---------------------------------------------------------------------- #

    def test_price_data_defaults_to_zero(self):
        dd = DepozitDataModel("Test", "Depozit", DepozitSource.EXCEL_SUMAL)
        pd = dd.price_data
        assert pd.p_intrare_lr_mc == 0
        assert pd.p_iesire_lr_mc == 0
        assert pd.p_transport_mc == 0
        assert pd.p_expl_mc == 0

# ---------------------------------------------------------------------- #

class TestNoticeTotalsDefaults:

    def test_totals_initialized_to_zero(self):
        notice = make_notice()
        t = notice.totals
        assert t.volum_total_lemn_rotund == 0.0
        assert t.volum_total_lemn_foc == 0.0
        assert t.volum_total_cherestele == 0.0
        assert t.pret_total_materiale == 0.0
        assert t.pret_total_transport == 0.0
        assert t.pret_total_exploatare == 0.0
        assert t.pret_total_aviz == 0.0
        assert t.valoare_impozit_punere_in_piata == 0.0

    # ---------------------------------------------------------------------- #

    def test_species_dicts_initialized_empty(self):
        notice = make_notice()
        t = notice.totals
        assert t.volume_pe_specii_lemn_rotund == {}
        assert t.volume_pe_specii_lemn_foc == {}
        assert t.volume_pe_specii_cherestele == {}

    # ---------------------------------------------------------------------- #

    def test_type_initialized_to_none(self):
        notice = make_notice()
        assert notice.type is None

# ---------------------------------------------------------------------- #

class TestVolumeTotalsExtended:

    def test_multiple_species_same_good_type(self):
        """Brad + Molid both Lemn rotund should appear as separate species entries."""
        notice = make_notice(volum_total_aviz = 5.0)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 3.0, specie = "Brad"),
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 2.0, specie = "Molid", nr_crt = 2)
        ]
        notice.infer_volume_totals()

        assert notice.totals.volum_total_lemn_rotund == 5.0
        assert notice.totals.volume_pe_specii_lemn_rotund == {"Brad": 3.0, "Molid": 2.0}

    # ---------------------------------------------------------------------- #

    def test_cherestele_species_tracked(self):
        notice = make_notice(volum_total_aviz = 4.0)
        notice.wood_items = [
            make_wood_item(sortiment = "Cherestele", volum_mc = 2.5, specie = "Stejar"),
            make_wood_item(sortiment = "Cherestele", volum_mc = 1.5, specie = "Fag", nr_crt = 2)
        ]
        notice.infer_volume_totals()

        assert notice.totals.volum_total_cherestele == 4.0
        assert notice.totals.volume_pe_specii_cherestele == {"Stejar": 2.5, "Fag": 1.5}

    # ---------------------------------------------------------------------- #

    def test_multiple_unknown_sortiments_returned_sorted(self):
        notice = make_notice()
        notice.wood_items = [
            make_wood_item(sortiment = "Zzzz necunoscut", volum_mc = 1.0),
            make_wood_item(sortiment = "Aaaa necunoscut", volum_mc = 1.0, nr_crt = 2)
        ]
        unknown = notice.infer_volume_totals()
        assert unknown == ["Aaaa necunoscut", "Zzzz necunoscut"]

    # ---------------------------------------------------------------------- #

    def test_mixed_known_and_unknown_sortiments(self):
        """Known sortiments should still be counted, unknown ones returned."""
        notice = make_notice(volum_total_aviz = 5.5)
        notice.wood_items = [
            make_wood_item(sortiment = "Lemn rotund", volum_mc = 2.5, specie = "Brad"),
            make_wood_item(sortiment = "Lemn de foc", volum_mc = 3.0, specie = "Fag", nr_crt = 2),
            make_wood_item(sortiment = "Necunoscut", volum_mc = 1.0, nr_crt = 3)
        ]
        unknown = notice.infer_volume_totals()

        assert notice.totals.volum_total_lemn_rotund == 2.5
        assert notice.totals.volum_total_lemn_foc == 3.0
        assert unknown == ["Necunoscut"]

# ---------------------------------------------------------------------- #

class TestNoticeTypeEdgeCases:

    def test_own_emitter_external_dest_lr_provenienta_is_iesire_lr(self):
        """Own emitter sending to external, provenienta is LR deposit -> IESIRE_DIN_DEPOZIT_LR, not PRINCIPAL."""
        depozite = [
            make_depozite_excel_entry(
                nume_depozit = APP_CONFIG.DEPOZIT_OWN, tip_depozit = "Depozit"
            ),
            make_depozite_excel_entry(
                nume_depozit = "Alt Depozit LR", tip_depozit = "Depozit Temporar LR"
            ),
        ]
        notice = make_notice(
            provenienta = "Alt Depozit LR",
            emitent_nume = APP_CONFIG.NUME_OWN, emitent_cui = APP_CONFIG.CUI_OWN, emitent_adresa = APP_CONFIG.ADRESA_OWN,
            destinatar_nume = "Client SRL", destinatar_cui = "99999999",
            destinatar_adresa = "Adresa client", punct_descarcare_depozit = "Depozit client"
        )
        notice.infer_notice_type(depozite)
        assert notice.type == NoticeType.IESIRE_DIN_DEPOZIT_LR

    # ---------------------------------------------------------------------- #

    def test_intrare_partida_proprie_requires_lr_deposit_type(self):
        """Same as INTRARE_DIN_PARTIDA_PROPRIE but provenienta points to main deposit -> UNKNOWN."""
        depozite = [
            make_depozite_excel_entry(
                nume_depozit = "Main Dep", tip_depozit = "Depozit"
            ),
        ]
        notice = make_notice(
            provenienta = "Main Dep",
            emitent_nume = APP_CONFIG.NUME_OWN, emitent_cui = APP_CONFIG.CUI_OWN, emitent_adresa = APP_CONFIG.ADRESA_OWN,
            destinatar_nume = APP_CONFIG.NUME_OWN, destinatar_cui = APP_CONFIG.CUI_OWN,
            destinatar_adresa = APP_CONFIG.ADRESA_OWN, punct_descarcare_depozit = APP_CONFIG.DEPOZIT_OWN
        )
        notice.infer_notice_type(depozite)
        # Own->own but provenienta is "Depozit" type, not "Depozit Temporar LR" -> no rule matches
        assert notice.type == NoticeType.UNKNOWN

