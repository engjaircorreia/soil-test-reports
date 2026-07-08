import importlib

import pytest


def require_module(name):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        pytest.xfail(f"{name} ainda nao foi implementado: {exc}")


def test_pipeline_keeps_ai_raw_data_separate_from_normalized_and_calculated_data(monkeypatch):
    pipeline = require_module("ensaios.services.pipeline")

    raw_extraction = {
        "metadata": {
            "idioma_modelo": "pt",
            "tipo_esperado": "compactacao_cbr",
            "arquivos": [{"nome": "cbr.jpeg", "tipo_detectado": "cbr", "confianca": 0.95}],
        },
        "dados_comuns": {"obra": "Obra", "procedencia_rua": "Rua", "local_furo_estaca": "E02"},
        "cbr": {
            "higroscopica": {
                "capsula": "40",
                "peso_bruto_umido_g": "101,5",
                "peso_bruto_seco_g": "101,2",
                "tara_capsula_g": "17,99",
            },
            "resultado_lido": {"cbr_percent": "39"},
        },
    }

    result = pipeline.build_review_payload(raw_extraction)

    assert result["extracted_data"]["cbr"]["higroscopica"]["peso_bruto_umido_g"] == "101,5"
    assert result["normalized_data"]["cbr"]["higroscopica"]["peso_bruto_umido_g"] == 101.5
    assert result["calculated_data"]["cbr"]["higroscopica"]["umidade_percent"] == pytest.approx(0.3605, abs=0.001)
    assert "validation_issues" in result


def test_pipeline_marks_unreadable_values_as_pending_human_review():
    pipeline = require_module("ensaios.services.pipeline")

    raw_extraction = {
        "metadata": {
            "idioma_modelo": "pt",
            "tipo_esperado": "compactacao_cbr",
            "arquivos": [{"nome": "cbr.jpeg", "tipo_detectado": "cbr", "confianca": 0.95}],
        },
        "dados_comuns": {"obra": "Obra", "procedencia_rua": "Rua", "local_furo_estaca": "E02"},
        "cbr": {
            "higroscopica": {
                "capsula": None,
                "peso_bruto_umido_g": None,
                "peso_bruto_seco_g": None,
                "tara_capsula_g": None,
            }
        },
    }

    result = pipeline.build_review_payload(raw_extraction)

    assert result["normalized_data"]["cbr"]["higroscopica"]["peso_bruto_umido_g"] is None
    assert any(
        issue["severity"] in {"warning", "error"}
        and "higroscop" in str(issue.get("message", "")).lower()
        for issue in result["validation_issues"]
    )


def test_pipeline_reuses_valid_proctor_hygroscopic_moisture_when_cbr_is_unreadable():
    pipeline = require_module("ensaios.services.pipeline")

    raw_extraction = {
        "metadata": {
            "idioma_modelo": "pt",
            "tipo_esperado": "compactacao_cbr",
            "arquivos": [
                {"nome": "proctor.jpeg", "tipo_detectado": "proctor", "confianca": 0.95},
                {"nome": "cbr.jpeg", "tipo_detectado": "cbr", "confianca": 0.95},
            ],
        },
        "proctor": {
            "higroscopica": {
                "capsula": "31",
                "peso_bruto_umido_g": "101,7",
                "peso_bruto_seco_g": "101,2",
                "tara_capsula_g": "17,29",
            }
        },
        "cbr": {
            "higroscopica": {
                "capsula": "40",
                "peso_bruto_umido_g": "101,5",
                "peso_bruto_seco_g": "104,2",
                "tara_capsula_g": "17,99",
            },
            "moldagem": {
                "capsula": "32",
                "peso_bruto_umido_g": "100,3",
                "peso_bruto_seco_g": "92,3",
                "tara_capsula_g": "17,35",
            },
        },
    }

    result = pipeline.build_review_payload(raw_extraction)

    assert result["extracted_data"]["cbr"]["higroscopica"]["peso_bruto_seco_g"] == "104,2"
    assert result["normalized_data"]["cbr"]["higroscopica"]["capsula"] == "31"
    assert result["normalized_data"]["compactacao"]["higroscopica"]["capsula"] == "31"
    assert result["calculated_data"]["cbr"]["higroscopica"]["umidade_percent"] == pytest.approx(0.595, abs=0.001)
    assert result["review_data"]["cbr"]["higroscopica"]["capsula"] == "31"
    assert result["review_data"]["compactacao"]["higroscopica"]["capsula"] == "31"
