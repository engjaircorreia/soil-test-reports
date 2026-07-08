from django.test import override_settings

from ensaios.services.extraction_openai import (
    EXTRACTION_PROMPT,
    extract_data,
    infer_test_type,
    sanitize_extracted_data,
)


@override_settings(OPENAI_API_KEY="")
def test_extraction_without_api_key_returns_manual_fallback():
    data, raw = extract_data([], {"obra": "Rua Teste", "estaca": "ESTACA 01", "language": "pt"})
    assert raw is None
    assert data["obra"] == "Rua Teste"
    assert data["estaca"] == "ESTACA 01"
    assert data["arquivos"] == []
    assert data["warnings"]


def test_infer_test_type_from_file_classification():
    assert infer_test_type({"arquivos": [{"classificacao": "compactacao"}]}) == "compactacao_cbr"
    assert infer_test_type({"arquivos": [{"classificacao": "cbr"}]}) == "compactacao_cbr"
    assert infer_test_type({"arquivos": [{"classificacao": "granulometria"}]}) == "granulometria"
    assert (
        infer_test_type({"arquivos": [{"classificacao": "cbr"}, {"classificacao": "granulometria"}]})
        == "ambos"
    )
    assert infer_test_type({"arquivos": []}, "auto") == "ambos"
    assert infer_test_type({"arquivos": []}, "granulometria") == "granulometria"
    assert (
        infer_test_type({"arquivos": [{"classificacao": "cbr"}]}, "granulometria")
        == "compactacao_cbr"
    )


def test_extraction_prompt_guides_ambiguous_lab_fields():
    assert "normalize para 1.951" in EXTRACTION_PROMPT
    assert "Não use a coluna \"Padrão\"" in EXTRACTION_PROMPT
    assert "linha \"N° 10\"" in EXTRACTION_PROMPT
    assert "coluna \"% QUE PASSA\"" in EXTRACTION_PROMPT
    assert "Não leia peso retido" in EXTRACTION_PROMPT


def test_sanitize_extracted_data_drops_impossible_moisture_block():
    data = {
        "cbr": {
            "higroscopica": {
                "capsula": "31",
                "peso_bruto_umido": 101.7,
                "peso_bruto_seco": 102.2,
                "tara_capsula": 17.29,
            }
        },
        "warnings": [],
    }
    sanitized = sanitize_extracted_data(data)
    assert sanitized["cbr"]["higroscopica"]["capsula"] is None
    assert sanitized["warnings"] == ["Umidade higroscópica do CBR ignorada: pesos incoerentes ou incompletos."]
