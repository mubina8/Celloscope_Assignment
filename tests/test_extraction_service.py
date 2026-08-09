from adapters.extraction.mock_adapter import MockExtractionAdapter
from services.extraction_service import ExtractionService


def test_extracts_meta_and_results_from_fixture():
    service = ExtractionService(MockExtractionAdapter("adapters/extraction/fixtures"))
    result = service.extract(b"fake-bytes", "sample_lab_report.jpg")

    assert result.is_lab_report is True
    assert result.meta["patient_name"] == "Jane Doe"
    assert result.meta["sex"] == "Female"
    assert result.meta["report_date"] == "2024-01-12"

    test_names = [r.test_name for r in result.results]
    assert "Hemoglobin" in test_names

    hemoglobin = next(r for r in result.results if r.test_name == "Hemoglobin")
    assert hemoglobin.value == {"kind": "number", "value": 12.5}
    assert hemoglobin.unit == "g/dL"
    assert hemoglobin.flag == "NORMAL"
    assert hemoglobin.raw_line == "Hemoglobin 12.5 g/dL 12.0-15.5 NORMAL"  # verbatim


def test_non_lab_report_degrades_gracefully():
    service = ExtractionService(MockExtractionAdapter("adapters/extraction/fixtures"))
    # No fixture matches this filename -> mock returns low-confidence garbage line
    result = service.extract(b"fake-bytes", "random_photo_of_a_cat.jpg")

    assert result.is_lab_report is False
    assert result.results == []
