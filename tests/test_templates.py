from pathlib import Path

from openpyxl import load_workbook

from ensaios.services.validation import validate_workbook


def test_templates_are_valid():
    for path in Path("templates").glob("*.xlsx"):
        validate_workbook(path)


def test_expected_templates_exist():
    names = {path.name for path in Path("templates").glob("*.xlsx")}
    assert "compactacao_cbr_modelo_limpo.xlsx" in names
    assert "compaction_cbr_clean_template_en.xlsx" in names
    assert "granulometria_modelo_limpo.xlsx" in names
    assert "granulometry_clean_template_en.xlsx" in names


def test_compaction_templates_have_no_default_depth():
    for path in [
        Path("templates/compactacao_cbr_modelo_limpo.xlsx"),
        Path("templates/compaction_cbr_clean_template_en.xlsx"),
    ]:
        workbook = load_workbook(path, data_only=False)
        assert workbook["DENS"]["K6"].value in (None, "")
