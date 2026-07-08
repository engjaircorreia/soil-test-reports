import importlib

import pytest


def require_module(name):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        pytest.xfail(f"{name} ainda nao foi implementado: {exc}")


def issue_messages(issues):
    return " | ".join(str(issue.get("message") or issue) for issue in issues)


def test_validation_blocks_cbr_generation_when_hygroscopic_moisture_is_missing():
    validation = require_module("ensaios.services.technical_validation")
    data = {
        "dados_comuns": {
            "interessado": "Cliente",
            "obra": "Obra",
            "procedencia_rua": "Rua",
            "local_furo_estaca": "E02",
            "data_ensaio": "2026-07-08",
        },
        "proctor": {
            "energia": "INTERMEDIARIO",
            "molde_numero": "05",
            "peso_molde_g": 5414,
            "volume_molde_cm3": 2068,
            "numero_camadas": 5,
            "golpes_por_camada": 26,
            "pontos": [{"ponto": 1, "capsulas": [{"capsula": "1"}]}],
        },
        "cbr": {
            "registro_numero_cbr": "1",
            "molde_numero": "02",
            "peso_molde_g": 4775,
            "volume_molde_cm3": 2088,
            "numero_camadas": 5,
            "golpes_por_camada": 26,
            "peso_soquete_g": 4536,
            "espessura_disco_espacador": '2 1/2"',
            "altura_cilindro_mm": 114,
            "constante_prensa": 0.0839,
            "higroscopica": {
                "capsula": None,
                "peso_bruto_umido_g": None,
                "peso_bruto_seco_g": None,
                "tara_capsula_g": None,
            },
            "moldagem": {
                "capsula": "32",
                "peso_bruto_umido_g": 100.3,
                "peso_bruto_seco_g": 92.3,
                "tara_capsula_g": 17.35,
            },
            "penetracao": [{"penetracao_mm": 2.54, "cbr_percent": 39.0}],
            "expansao": {"expansao_percent_lida": 0.7},
        },
    }

    issues = validation.validate_bundle(data, test_type="compactacao_cbr")

    assert any(issue["severity"] == "error" for issue in issues)
    assert "higroscopic" in issue_messages(issues).lower() or "higroscop" in issue_messages(issues).lower()


def test_validation_does_not_require_empresa_executora_for_proctor_cbr():
    validation = require_module("ensaios.services.technical_validation")
    data = {
        "dados_comuns": {
            "interessado": "Cliente",
            "obra": "Obra",
            "procedencia_rua": "Rua",
            "local_furo_estaca": "E02",
            "data_ensaio": "2026-07-08",
        },
        "proctor": {
            "energia": "INTERMEDIARIO",
            "molde_numero": "05",
            "peso_molde_g": 5414,
            "volume_molde_cm3": 2068,
            "numero_camadas": 5,
            "golpes_por_camada": 26,
            "pontos": [{"ponto": 1, "capsulas": [{"capsula": "1"}]}],
        },
        "cbr": {
            "registro_numero_cbr": "1",
            "molde_numero": "02",
            "peso_molde_g": 4775,
            "volume_molde_cm3": 2088,
            "numero_camadas": 5,
            "golpes_por_camada": 26,
            "peso_soquete_g": 4536,
            "espessura_disco_espacador": '2 1/2"',
            "altura_cilindro_mm": 114,
            "constante_prensa": 0.0839,
            "higroscopica": {
                "capsula": "40",
                "peso_bruto_umido_g": 101.5,
                "peso_bruto_seco_g": 101.2,
                "tara_capsula_g": 17.99,
            },
            "moldagem": {
                "capsula": "32",
                "peso_bruto_umido_g": 100.3,
                "peso_bruto_seco_g": 92.3,
                "tara_capsula_g": 17.35,
            },
            "penetracao": [{"penetracao_mm": 2.54, "cbr_percent": 39.0}],
            "expansao": {"expansao_percent_lida": 0.7},
        },
    }

    issues = validation.validate_bundle(data, test_type="compactacao_cbr")

    assert "empresa executora" not in issue_messages(issues).lower()


def test_validation_requires_empresa_executora_for_granulometry():
    validation = require_module("ensaios.services.technical_validation")
    data = {
        "granulometria": {
            "empresa_executora": None,
            "obra": "Obra",
            "procedencia_rua": "Rua",
            "local_furo_estaca": "E02",
            "data_ensaio": "2026-07-08",
            "amostra_total": {"peso_seco_total_g": 1500},
            "peneiras": [{"peneira": "10", "percentual_passante": 40.1}],
        }
    }

    issues = validation.validate_bundle(data, test_type="granulometria")

    assert any(issue["severity"] == "error" for issue in issues)
    assert "empresa" in issue_messages(issues).lower()

