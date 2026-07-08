import pytest
import os
import tempfile
from datetime import datetime
from unittest.mock import MagicMock
from core.csv_reader import CsvReader
from core.models import TransportNoticeModel
from core.enums import CSVParseStatus
from core.sr_error import SRError

@pytest.fixture
def reader():
    return CsvReader(MagicMock())

# ---------------------------------------------------------------------- #

def _write_csv(tmp_dir, filename, content):
    """Write a CSV file to a temp directory."""
    path = os.path.join(tmp_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

# ---------------------------------------------------------------------- #

# Minimal valid CSV with all required columns
VALID_CSV_HEADER = (
    "Certificare,Cod unic,Data si ora emiterii codului unic,Valabil pana la data/ora,"
    "Provenienta,Emitent - nume,Emitent - CUI,Emitent - Nr. Reg. Com.,"
    "Emitent - Localitate,Emitent - Judet,Emitent - Adresa,"
    "Punct incarcare - Judet,Punct incarcare - Localitate,Punct incarcare - Adresa,"
    "Destinatar - Nume,Destinatar - CUI/CNP,Destinatar - Nr. Reg. Com.,"
    "Destinatar - Localitate,Destinatar - Judet,Destinatar - Adresa,"
    "Punct descarcare - Depozit,Punct descarcare - Tara,Punct descarcare - Judet,"
    "Punct descarcare - Localitate,Punct descarcare - Adresa,"
    "Vama,Identificator sofer,Mijloc transport,Cap tractor,Remorca,"
    "Nr. Km la bord,Volum total aviz,"
    "Nr.Crt.,Grupa de specii,Specie,Sortiment,Subsortiment,Nr. Bucati,"
    "Lungime(m),Latime(m),Inaltime(m),Diametru(cm),Volum(mc),"
    "Nume proprietar,Cnp proprietar,Detalii masa lemnoasa,Identificator container"
)

# ---------------------------------------------------------------------- #

def _build_valid_csv_row():
    """Build a valid CSV row matching VALID_CSV_HEADER column order exactly."""
    # Map each column to its value — must match VALID_CSV_HEADER order
    vals = [
        "-",                               # Certificare
        "AP250014600010004973",            # Cod unic
        "08-12-2025 12:57:38",             # Data si ora emiterii codului unic
        "08-12-2025 20:57:38",             # Valabil pana la data/ora
        "Test Depozit",                    # Provenienta
        "Firma Test",                      # Emitent - nume
        "12345678",                        # Emitent - CUI
        "J26/100/2020",                    # Emitent - Nr. Reg. Com.
        "Localitatea",                     # Emitent - Localitate
        "Judetul",                         # Emitent - Judet
        "Adresa emitent",                  # Emitent - Adresa
        "Judet inc",                       # Punct incarcare - Judet
        "Loc inc",                         # Punct incarcare - Localitate
        "Adresa inc",                      # Punct incarcare - Adresa
        "Destinatar Test",                 # Destinatar - Nume
        "87654321",                        # Destinatar - CUI/CNP
        "J26/200/2020",                    # Destinatar - Nr. Reg. Com.
        "Loc dest",                        # Destinatar - Localitate
        "Judet dest",                      # Destinatar - Judet
        "Adresa dest",                     # Destinatar - Adresa
        "Depozit dest",                    # Punct descarcare - Depozit
        "Romania",                         # Punct descarcare - Tara
        "Judet desc",                      # Punct descarcare - Judet
        "Loc desc",                        # Punct descarcare - Localitate
        "Adresa desc",                     # Punct descarcare - Adresa
        "",                                # Vama
        "1234567890",                      # Identificator sofer
        "Camion",                          # Mijloc transport
        "MS98LIR",                         # Cap tractor
        "MS99LIR",                         # Remorca
        "12345",                           # Nr. Km la bord
        "2.5",                             # Volum total aviz
        "1",                               # Nr.Crt.
        "Rasinoase",                       # Grupa de specii
        "Brad",                            # Specie
        "Lemn rotund",                     # Sortiment
        "-",                               # Subsortiment
        "5",                               # Nr. Bucati
        "4.0",                             # Lungime(m)
        "0.0",                             # Latime(m)
        "0.0",                             # Inaltime(m)
        "28.0",                            # Diametru(cm)
        "2.5",                             # Volum(mc)
        "",                                # Nume proprietar
        "",                                # Cnp proprietar
        "",                                # Detalii masa lemnoasa
        ""                                 # Identificator container
    ]
    return ",".join(vals)

# ---------------------------------------------------------------------- #

VALID_CSV_ROW = _build_valid_csv_row()

# ---------------------------------------------------------------------- #

class TestCsvReaderReadNotice:
    def test_valid_csv_parses_successfully(self, reader):
        """CSV parsed successfully"""
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_csv(tmp, "test.csv", f"{VALID_CSV_HEADER}\n{VALID_CSV_ROW}")
            notice = reader.read_notice(path)

            assert isinstance(notice, TransportNoticeModel)
            assert notice.cod_unic == "AP250014600010004973"
            assert len(notice.wood_items) == 1
            assert notice.wood_items[0].specie == "Brad"
            assert notice.volum_total_aviz == 2.5
            # Verify parsed field types
            assert isinstance(notice.data_ora_emitere, datetime)
            assert isinstance(notice.km_bord, int)
            assert isinstance(notice.wood_items[0].volum_mc, float)
            assert isinstance(notice.wood_items[0].nr_bucati, int)
            assert isinstance(notice.volum_total_aviz, float)

    # ---------------------------------------------------------------------- #

    def test_empty_csv_raises(self, reader):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_csv(tmp, "empty.csv", VALID_CSV_HEADER + "\n")
            # pandas read_csv with only header and no data rows
            with pytest.raises(SRError, match = "gol"):
                reader.read_notice(path)

    # ---------------------------------------------------------------------- #

    def test_missing_column_raises(self, reader):
        bad_header = "Col1,Col2,Col3"
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_csv(tmp, "bad.csv", f"{bad_header}\nval1,val2,val3")
            with pytest.raises(SRError, match = "coloanele necesare"):
                reader.read_notice(path)

    # ---------------------------------------------------------------------- #

    def test_inconsistent_header_field_raises(self, reader):
        """If a header field differs across rows, it should raise."""
        # Two rows with different "Cod unic" values
        row2 = VALID_CSV_ROW.replace("AP250014600010004973", "DIFFERENT_CODE")
        csv_content = f"{VALID_CSV_HEADER}\n{VALID_CSV_ROW}\n{row2}"
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_csv(tmp, "inconsistent.csv", csv_content)
            with pytest.raises(SRError, match = "valori diferite"):
                reader.read_notice(path)

    # ---------------------------------------------------------------------- #

    def test_nonexistent_file_raises(self, reader):
        with pytest.raises(SRError, match = "nu a putut fi deschis"):
            reader.read_notice("/nonexistent/path/file.csv")

# ---------------------------------------------------------------------- #

class TestCsvReaderBatch:
    def test_batch_collects_errors(self, reader):
        with tempfile.TemporaryDirectory() as tmp:
            # One valid, one invalid
            _write_csv(tmp, "good.csv", f"{VALID_CSV_HEADER}\n{VALID_CSV_ROW}")
            _write_csv(tmp, "bad.csv", "Col1,Col2\nval1,val2")

            notices, results = reader.read_all_notices_in_folder(
                tmp, ["good.csv", "bad.csv"]
            )

            assert len(notices) == 1
            assert len(results) == 2
            ok_results = [r for r in results if r.status == CSVParseStatus.OK]
            err_results = [r for r in results if r.status == CSVParseStatus.ERROR]
            assert len(ok_results) == 1
            assert len(err_results) == 1

    # ---------------------------------------------------------------------- #

    def test_empty_batch(self, reader):
        with tempfile.TemporaryDirectory() as tmp:
            notices, results = reader.read_all_notices_in_folder(tmp, [])
            assert notices == []
            assert results == []

# ---------------------------------------------------------------------- #

class TestCsvReaderPrecision:
    """SUMAL volumes carry up to 6 decimals — parsing must preserve them exactly."""

    def test_six_decimal_volumes_parse_exactly(self, reader):
        from decimal import Decimal

        header_cols = VALID_CSV_HEADER.split(",")
        vol_total_idx = header_cols.index("Volum total aviz")
        vol_item_idx = header_cols.index("Volum(mc)")
        nr_crt_idx = header_cols.index("Nr.Crt.")

        # Two items whose float sum is noisy (0.123456 + 0.234567) but whose
        # 6-decimal total is exact — the realistic SUMAL shape.
        item_volumes = ["0.123456", "0.234567"]
        total = "0.358023"

        rows = []
        for nr_crt, item_volume in enumerate(item_volumes, start = 1):
            cols = VALID_CSV_ROW.split(",")
            cols[vol_total_idx] = total
            cols[vol_item_idx] = item_volume
            cols[nr_crt_idx] = str(nr_crt)
            rows.append(",".join(cols))

        with tempfile.TemporaryDirectory() as tmp:
            path = _write_csv(tmp, "precise.csv", "\n".join([VALID_CSV_HEADER] + rows))
            notice = reader.read_notice(path)

        # Parsed floats round-trip to the identical decimal values
        assert Decimal(repr(notice.volum_total_aviz)) == Decimal(total)
        for item, source_value in zip(notice.wood_items, item_volumes):
            assert Decimal(repr(item.volum_mc)) == Decimal(source_value)

        # And the full volume validation passes at source precision
        notice.infer_volume_totals()
        assert notice.validate_volumes(MagicMock()) is True
