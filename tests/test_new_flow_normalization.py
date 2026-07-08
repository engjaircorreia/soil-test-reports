import importlib

import pytest


def require_module(name):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        pytest.xfail(f"{name} ainda nao foi implementado: {exc}")


def test_normalize_number_handles_brazilian_decimals_units_and_empty_values():
    normalization = require_module("ensaios.services.normalization")

    assert normalization.normalize_number("10,7 %") == 10.7
    assert normalization.normalize_number("1,960") == 1.96
    assert normalization.normalize_number("0,0839") == 0.0839
    assert normalization.normalize_number("") is None
    assert normalization.normalize_number("-") is None
    assert normalization.normalize_number("ilegivel") is None
    assert normalization.normalize_number("NL") == "NL"
    assert normalization.normalize_number("NP") == "NP"


def test_normalize_density_context_converts_kg_m3_to_g_cm3():
    normalization = require_module("ensaios.services.normalization")

    assert normalization.normalize_number("1960 kg/m3", context="density") == 1.96
    assert normalization.normalize_number("1960", context="density") == 1.96
    assert normalization.normalize_number("1,960", context="density") == 1.96


def test_normalize_date_accepts_common_formats():
    normalization = require_module("ensaios.services.normalization")

    assert normalization.normalize_date("08/07/2026") == "2026-07-08"
    assert normalization.normalize_date("2026-07-08") == "2026-07-08"
    assert normalization.normalize_date("") is None


def test_normalize_extraction_preserves_raw_nulls_and_returns_alerts():
    normalization = require_module("ensaios.services.normalization")
    raw = {
        "dados_comuns": {
            "obra": "Obra",
            "data_ensaio": "08/07/2026",
            "profundidade_furo": "",
        },
        "proctor": {
            "resultado_lido": {
                "umidade_otima_percent": "10,0%",
                "densidade_maxima_g_cm3": "1960 kg/m3",
            }
        },
        "cbr": {
            "higroscopica": {
                "capsula": "40",
                "peso_bruto_umido_g": "101,5",
                "peso_bruto_seco_g": "101,2",
                "tara_capsula_g": "17,99",
            }
        },
    }

    normalized, issues = normalization.normalize_extraction(raw)

    assert issues == []
    assert normalized["dados_comuns"]["data_ensaio"] == "2026-07-08"
    assert normalized["dados_comuns"]["profundidade_furo"] is None
    assert normalized["proctor"]["resultado_lido"]["umidade_otima_percent"] == 10.0
    assert normalized["proctor"]["resultado_lido"]["densidade_maxima_g_cm3"] == 1.96
    assert normalized["cbr"]["higroscopica"]["peso_bruto_umido_g"] == 101.5

