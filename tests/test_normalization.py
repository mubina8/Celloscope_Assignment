from services.normalization import normalize_date, normalize_unit, normalize_value


class TestNormalizeValue:
    def test_plain_number(self):
        assert normalize_value("12.5") == {"kind": "number", "value": 12.5}

    def test_thousands_separator(self):
        assert normalize_value("12,500") == {"kind": "number", "value": 12500.0}

    def test_less_than(self):
        assert normalize_value("<0.5") == {"kind": "lt", "value": 0.5}

    def test_greater_than(self):
        assert normalize_value(">200") == {"kind": "gt", "value": 200.0}

    def test_range(self):
        assert normalize_value("0.8 - 1.2") == {"kind": "range", "low": 0.8, "high": 1.2}

    def test_range_en_dash(self):
        assert normalize_value("0.8 \u2013 1.2") == {"kind": "range", "low": 0.8, "high": 1.2}

    def test_scientific_notation(self):
        result = normalize_value("1.2 x 10^3")
        assert result["kind"] == "number"
        assert result["value"] == 1200.0

    def test_unparsable_preserved_verbatim(self):
        result = normalize_value("trace amounts detected")
        assert result == {"kind": "unparsed", "raw": "trace amounts detected"}

    def test_empty_string_unparsed(self):
        assert normalize_value("") == {"kind": "unparsed", "raw": ""}

    def test_none_unparsed(self):
        assert normalize_value(None) == {"kind": "unparsed", "raw": None}


class TestNormalizeUnit:
    def test_gm_dl_variants_collapse(self):
        assert normalize_unit("gm/dl") == "g/dL"
        assert normalize_unit("g/dL") == "g/dL"
        assert normalize_unit("g/dl") == "g/dL"

    def test_mg_dl(self):
        assert normalize_unit("mg/dl") == "mg/dL"

    def test_unknown_unit_passed_through(self):
        assert normalize_unit("weird/unit") == "weird/unit"

    def test_none_passthrough(self):
        assert normalize_unit(None) is None


class TestNormalizeDate:
    def test_iso_format(self):
        assert normalize_date("2024-01-12") == "2024-01-12"

    def test_dmy_slash(self):
        assert normalize_date("12/01/2024") == "2024-01-12"

    def test_written_month(self):
        assert normalize_date("12 Jan 2024") == "2024-01-12"

    def test_unparsable_preserved(self):
        assert normalize_date("sometime last week") == "sometime last week"

    def test_none_passthrough(self):
        assert normalize_date(None) is None
