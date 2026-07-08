from ensaios.services.workbook_fill import template_path


def test_template_selection_by_type_and_language():
    assert template_path("compactacao_cbr", "pt").name == "compactacao_cbr_modelo_limpo.xlsx"
    assert template_path("compactacao_cbr", "en").name == "compaction_cbr_clean_template_en.xlsx"
    assert template_path("granulometria", "pt").name == "granulometria_modelo_limpo.xlsx"
    assert template_path("granulometria", "en").name == "granulometry_clean_template_en.xlsx"
