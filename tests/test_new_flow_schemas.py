import importlib

import pytest


def require_module(name):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        pytest.xfail(f"{name} ainda nao foi implementado: {exc}")


def sample_raw_extraction():
    return {
        "metadata": {
            "idioma_modelo": "pt",
            "tipo_esperado": "ambos",
            "arquivos": [
                {"nome": "proctor.jpeg", "tipo_detectado": "proctor", "confianca": 0.95},
                {"nome": "cbr.jpeg", "tipo_detectado": "cbr", "confianca": 0.93},
                {"nome": "gran.jpeg", "tipo_detectado": "granulometria", "confianca": 0.9},
            ],
        },
        "dados_comuns": {
            "interessado": None,
            "obra": "Obra Teste",
            "procedencia_rua": "Travessa do Rio",
            "cidade": None,
            "local_furo_estaca": "E02",
            "profundidade_furo": None,
            "data_ensaio": None,
            "registro_numero": None,
            "responsavel_tecnico": None,
            "observacoes": None,
        },
        "proctor": {
            "energia": "INTERMEDIARIO",
            "molde_numero": "05",
            "peso_molde_g": "5414",
            "volume_molde_cm3": "2068",
            "numero_camadas": "5",
            "golpes_por_camada": "26",
            "peso_soquete_g": None,
            "pontos": [
                {
                    "ponto": 1,
                    "peso_solo_umido_molde_g": "9374",
                    "peso_solo_umido_g": None,
                    "capsulas": [
                        {
                            "capsula": "11",
                            "peso_bruto_umido_g": "61,50",
                            "peso_bruto_seco_g": "61,00",
                            "tara_capsula_g": "11,00",
                        }
                    ],
                }
            ],
            "resultado_lido": {
                "umidade_otima_percent": "10,0",
                "densidade_maxima_g_cm3": "1960",
            },
        },
        "cbr": {
            "registro_numero_cbr": None,
            "molde_numero": "02",
            "peso_molde_g": "4775",
            "volume_molde_cm3": "2088",
            "numero_camadas": "5",
            "golpes_por_camada": "26",
            "peso_soquete_g": "4536",
            "espessura_disco_espacador": '2 1/2"',
            "altura_cilindro_mm": "114",
            "constante_prensa": "0,0839",
            "higroscopica": {
                "capsula": "40",
                "peso_bruto_umido_g": "101,5",
                "peso_bruto_seco_g": "101,2",
                "tara_capsula_g": "17,99",
            },
            "moldagem": {
                "capsula": "32",
                "peso_bruto_umido_g": "100,3",
                "peso_bruto_seco_g": "92,3",
                "tara_capsula_g": "17,35",
            },
            "calculo_moldagem": {
                "peso_solo_umido_passando_peneira_4_g": "6000",
                "peso_solo_seco_passando_peneira_4_g": None,
                "peso_pedregulho_retido_peneira_4_g": None,
            },
            "penetracao": [
                {"tempo_min": "2", "leitura_extensometro": "282", "pressao_corrigida_kg_cm2": "273,5"}
            ],
            "expansao": {
                "leitura_inicial_mm": "0",
                "leitura_final_mm": "0,7",
                "expansao_percent_lida": "0,7",
            },
            "verificacao_moldagem": {
                "peso_bruto_umido_cp_molde_kg": "9,605",
                "peso_cp_umido_kg": None,
            },
            "resultado_lido": {"cbr_percent": "39", "expansao_percent": "0,7"},
        },
        "granulometria": {
            "empresa_executora": "RCA",
            "obra": "Obra Teste",
            "procedencia_rua": "Travessa do Rio",
            "camada": None,
            "lado": None,
            "local_furo_estaca": "E02",
            "profundidade_furo": None,
            "data_ensaio": None,
            "laboratorio": None,
            "operador": None,
            "laboratorista": None,
            "registro_numero": None,
            "umidade": {
                "capsula": None,
                "peso_bruto_umido_g": None,
                "peso_bruto_seco_g": None,
                "tara_capsula_g": None,
            },
            "amostra_total": {
                "peso_umido_total_g": None,
                "peso_seco_total_g": None,
                "material_retido_2mm_g": None,
                "material_passante_2mm_g": None,
            },
            "peneiras": [
                {"peneira": "10", "abertura_mm": None, "peso_retido_g": None, "percentual_passante": "40,1"},
                {"peneira": "40", "abertura_mm": None, "peso_retido_g": None, "percentual_passante": "26"},
                {"peneira": "200", "abertura_mm": None, "peso_retido_g": None, "percentual_passante": "14"},
            ],
            "limites": {"limite_liquidez": "NL", "limite_plasticidade": "NP", "indice_plasticidade": "NP"},
            "classificacao_lida": {"trb": None, "sucs": None},
        },
    }


def test_new_flow_schema_module_exposes_expected_contract():
    schemas = require_module("ensaios.services.schemas")
    for name in [
        "Metadata",
        "UploadedFileClassification",
        "DadosComuns",
        "ProctorRaw",
        "CbrRaw",
        "GranulometriaRaw",
        "ProctorCalculated",
        "CbrCalculated",
        "GranulometriaCalculated",
        "ValidationIssue",
        "ExtractionBundle",
        "ReviewedBundle",
    ]:
        assert hasattr(schemas, name)
    assert hasattr(schemas, "extraction_bundle_from_dict")
    assert hasattr(schemas, "extraction_bundle_to_dict")


def test_extraction_bundle_accepts_none_without_defaults_or_invented_values():
    schemas = require_module("ensaios.services.schemas")
    raw = sample_raw_extraction()
    raw["cbr"]["higroscopica"]["peso_bruto_umido_g"] = None

    bundle = schemas.extraction_bundle_from_dict(raw)
    exported = schemas.extraction_bundle_to_dict(bundle)

    assert exported["cbr"]["higroscopica"]["peso_bruto_umido_g"] is None
    assert exported["dados_comuns"]["interessado"] is None
    assert exported["granulometria"]["limites"]["limite_liquidez"] == "NL"
    assert "agua_a_juntar_g" not in exported["cbr"]["calculo_moldagem"]

