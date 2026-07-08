from datetime import datetime
from dataclasses import fields, dataclass
from core.utils import extract_base_name, normalize_field, float_to_display_str
from core.enums import GoodType, DepositType, NoticeType
from core.config import APP_CONFIG, DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE

# ---------------------------------------------------------------------- #

class TestExtractBaseName:

    def test_standard_sumal_filename(self):
        assert extract_base_name("AP25001460001000497311251450_08_12_2025_16_57_38.csv") == \
               "AP25001460001000497311251450"

    # ---------------------------------------------------------------------- #

    def test_different_timestamp(self):
        assert extract_base_name("AP25001460001000497311251450_01_01_2026_00_00_00.csv") == \
               "AP25001460001000497311251450"

    # ---------------------------------------------------------------------- #

    def test_no_timestamp_returns_full_name(self):
        assert extract_base_name("simplefile.csv") == "simplefile"

    # ---------------------------------------------------------------------- #

    def test_name_with_underscores_before_date(self):
        """Underscores in the base name are preserved."""
        result = extract_base_name("some_code_here_08_12_2025_16_57_38.csv")
        assert result == "some_code_here"

    # ---------------------------------------------------------------------- #

    def test_empty_filename(self):
        # No date pattern found, so full name (minus extension) is returned
        assert extract_base_name(".csv") == ".csv"

# ---------------------------------------------------------------------- #

class TestNormalizeField:

    @dataclass
    class _Dummy:
        str_field: str = ""
        int_field: int = 0
        float_field: float = 0.0
        dt_field: datetime = None

    # ---------------------------------------------------------------------- #

    def _get_field(self, name):
        for f in fields(self._Dummy):
            if f.name == name:
                return f
        raise ValueError(f"No field named {name}")

    # ---------------------------------------------------------------------- #

    def test_str_returns_empty(self):
        assert normalize_field(self._get_field("str_field")) == ""

    # ---------------------------------------------------------------------- #

    def test_int_returns_zero(self):
        assert normalize_field(self._get_field("int_field")) == 0

    # ---------------------------------------------------------------------- #

    def test_float_returns_zero(self):
        assert normalize_field(self._get_field("float_field")) == 0.0

    # ---------------------------------------------------------------------- #

    def test_datetime_returns_none(self):
        """Datetime fields cannot be normalized — returns None."""
        assert normalize_field(self._get_field("dt_field")) is None

# ---------------------------------------------------------------------- #

class TestEnumStr:

    def test_notice_type_str(self):
        assert str(NoticeType.INTRARE_DIN_PARTIDA_PROPRIE) == "Intrare din partidă proprie"
        assert str(NoticeType.INTRARE_DIN_SURSA_EXTERNA) == "Intrare din sursa externă"
        assert str(NoticeType.IESIRE_DIN_DEPOZIT_PRINCIPAL) == "Ieșire din depozit principal"
        assert str(NoticeType.IESIRE_DIN_DEPOZIT_LR) == "Ieșire din depozit LR"
        assert str(NoticeType.UNKNOWN) == "Necunoscut"

    # ---------------------------------------------------------------------- #

    def test_deposit_type_str(self):
        assert str(DepositType.DEPOZIT_PRINCIPAL) == "Depozit principal"
        assert str(DepositType.DEPOZIT_TEMPORAR_LR) == "Depozit temporar LR"
        assert str(DepositType.DEPOZIT_EXTERN) == "Depozit extern"
        assert str(DepositType.UNKNOWN) == "Necunoscut"

    # ---------------------------------------------------------------------- #

    def test_good_type_str(self):
        assert str(GoodType.LEMN_ROTUND) == "Lemn rotund"
        assert str(GoodType.LEMN_FOC) == "Lemn de foc"
        assert str(GoodType.CHERESTELE) == "Cherestele"
        assert str(GoodType.UNKNOWN) == "Necunoscut"

# ---------------------------------------------------------------------- #

class TestConstants:

    def test_company_constants_are_nonempty(self):
        assert APP_CONFIG.NUME_OWN
        assert APP_CONFIG.CUI_OWN
        assert APP_CONFIG.ADRESA_OWN
        assert APP_CONFIG.DEPOZIT_OWN

    # ---------------------------------------------------------------------- #

    def test_deposit_enabled_fields_covers_all_known_types(self):
        """Every non-UNKNOWN DepositType should have an enabled-fields mapping."""
        for dt in (DepositType.DEPOZIT_TEMPORAR_LR, DepositType.DEPOZIT_PRINCIPAL, DepositType.DEPOZIT_EXTERN):
            assert dt in DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE
            assert len(DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE[dt]) > 0

    # ---------------------------------------------------------------------- #

    def test_unknown_deposit_type_not_in_enabled_fields(self):
        assert DepositType.UNKNOWN not in DEPOSIT_DATA_ENABLED_FIELDS_BY_TYPE

# ---------------------------------------------------------------------- #

class TestFormatVolume:

    def test_six_decimal_value_strips_trailing_zeros(self):
        assert float_to_display_str(10.726900) == "10.7269"

    # ---------------------------------------------------------------------- #

    def test_value_with_fewer_decimals(self):
        assert float_to_display_str(2.5) == "2.5"

    # ---------------------------------------------------------------------- #

    def test_integer_value(self):
        assert float_to_display_str(5.0) == "5"

    # ---------------------------------------------------------------------- #

    def test_zero(self):
        assert float_to_display_str(0.0) == "0"

    # ---------------------------------------------------------------------- #

    def test_full_six_decimal_precision_kept(self):
        assert float_to_display_str(0.123456) == "0.123456"

    # ---------------------------------------------------------------------- #

    def test_value_with_three_decimals(self):
        assert float_to_display_str(1.234) == "1.234"

    # ---------------------------------------------------------------------- #

    def test_float_noise_is_hidden_at_6th_decimal(self):
        """Even if a value reads as 0.30000000000000004, format prints 0.3."""
        noisy = 0.1 + 0.2  # 0.30000000000000004
        assert float_to_display_str(noisy) == "0.3"

    # ---------------------------------------------------------------------- #

    def test_realistic_csv_value(self):
        """float('10.726900') round-trips and prints clean."""
        assert float_to_display_str(float("10.726900")) == "10.7269"

    # ---------------------------------------------------------------------- #

    def test_small_value(self):
        assert float_to_display_str(0.000001) == "0.000001"

    # ---------------------------------------------------------------------- #

    def test_value_below_six_decimals_rounds(self):
        """Anything below 6 decimals is noise — rounded away by the format spec."""
        assert float_to_display_str(0.0000001) == "0"
