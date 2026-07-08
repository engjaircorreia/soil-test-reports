from __future__ import annotations

from copy import deepcopy
from typing import Any

from .calculations import (
    calculate_cbr_final,
    calculate_cbr_moisture_blocks,
    calculate_granulometry,
    calculate_molding_check,
    calculate_proctor_curve,
    calculate_proctor_point,
)
from .extraction_openai import infer_test_type
from .normalization import normalize_extraction
from .technical_validation import validate_bundle


def get_path(data: dict[str, Any], path: str, default=None):
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(part)
    return default if current in (None, "") else current


def first_value(*values: Any, default=None) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return default


def moisture_block_for_legacy(block: dict[str, Any] | None) -> dict[str, Any]:
    block = block or {}
    return {
        "capsula": block.get("capsula"),
        "peso_bruto_umido": first_value(block.get("peso_bruto_umido_g"), block.get("peso_bruto_umido")),
        "peso_bruto_seco": first_value(block.get("peso_bruto_seco_g"), block.get("peso_bruto_seco")),
        "tara_capsula": first_value(block.get("tara_capsula_g"), block.get("tara_capsula")),
    }


def dict_at(data: dict[str, Any], path: str) -> dict[str, Any]:
    current = get_path(data, path, {})
    return current if isinstance(current, dict) else {}


def set_path(data: dict[str, Any], path: str, value: Any) -> None:
    current = data
    parts = path.split(".")
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            child = {}
            current[part] = child
        current = child
    current[parts[-1]] = value


def is_valid_moisture_block(block: dict[str, Any] | None) -> bool:
    if not isinstance(block, dict):
        return False
    result = calculate_cbr_moisture_blocks(block, {}).get("higroscopica", {})
    return result.get("umidade_percent") is not None


def equivalent_moisture_block(first: dict[str, Any], second: dict[str, Any]) -> bool:
    first_legacy = moisture_block_for_legacy(first)
    second_legacy = moisture_block_for_legacy(second)
    return all(
        str(first_legacy.get(key) or "") == str(second_legacy.get(key) or "")
        for key in ("capsula", "peso_bruto_umido", "peso_bruto_seco", "tara_capsula")
    )


def first_valid_moisture_block(data: dict[str, Any], *paths: str) -> dict[str, Any]:
    for path in paths:
        block = dict_at(data, path)
        if is_valid_moisture_block(block):
            return deepcopy(block)
    return {}


def apply_hygroscopic_fallback(data: dict[str, Any]) -> dict[str, Any]:
    cbr_block = dict_at(data, "cbr.higroscopica")
    proctor_block = first_valid_moisture_block(data, "proctor.higroscopica", "compactacao.higroscopica")
    cbr_valid = is_valid_moisture_block(cbr_block)
    proctor_valid = bool(proctor_block)

    if cbr_valid and proctor_valid and not equivalent_moisture_block(cbr_block, proctor_block):
        data.setdefault("warnings", []).append(
            "Umidade higroscópica do CBR e da compactação divergentes; mantido cada valor extraído para revisão."
        )
        return data

    fallback = deepcopy(cbr_block) if cbr_valid else deepcopy(proctor_block)
    if not fallback:
        return data

    for path in ("cbr.higroscopica", "proctor.higroscopica", "compactacao.higroscopica"):
        if not is_valid_moisture_block(dict_at(data, path)):
            set_path(data, path, deepcopy(fallback))
    return data


def detected_files_for_legacy(data: dict[str, Any]) -> list[dict[str, Any]]:
    files = get_path(data, "metadata.arquivos", [])
    legacy_files = []
    for item in files if isinstance(files, list) else []:
        if not isinstance(item, dict):
            continue
        detected = item.get("tipo_detectado")
        if detected == "proctor":
            detected = "compactacao"
        legacy_files.append({
            "nome": item.get("nome"),
            "classificacao": detected,
            "confianca": item.get("confianca"),
            "observacoes": item.get("observacoes"),
        })
    return legacy_files


def infer_test_type_from_bundle(data: dict[str, Any]) -> str:
    legacy_files = detected_files_for_legacy(data)
    default = get_path(data, "metadata.tipo_esperado", "ambos")
    return infer_test_type({"arquivos": legacy_files}, default)


def build_legacy_review_data(normalized: dict[str, Any], raw: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = raw or {}
    dados = normalized.get("dados_comuns") if isinstance(normalized.get("dados_comuns"), dict) else {}
    proctor = normalized.get("proctor") if isinstance(normalized.get("proctor"), dict) else {}
    cbr = normalized.get("cbr") if isinstance(normalized.get("cbr"), dict) else {}
    granulometria = (
        normalized.get("granulometria")
        if isinstance(normalized.get("granulometria"), dict)
        else {}
    )
    proctor_result = proctor.get("resultado_lido") if isinstance(proctor.get("resultado_lido"), dict) else {}
    cbr_result = cbr.get("resultado_lido") if isinstance(cbr.get("resultado_lido"), dict) else {}
    hygroscopic = first_valid_moisture_block(
        normalized,
        "cbr.higroscopica",
        "proctor.higroscopica",
        "compactacao.higroscopica",
    )
    gran_limits = granulometria.get("limites") if isinstance(granulometria.get("limites"), dict) else {}
    gran_class = (
        granulometria.get("classificacao_lida")
        if isinstance(granulometria.get("classificacao_lida"), dict)
        else {}
    )

    language = first_value(get_path(normalized, "metadata.idioma_modelo"), raw.get("language"), default="pt")
    test_type = infer_test_type_from_bundle(normalized)
    legacy = {
        "language": language,
        "test_type": test_type,
        "expected_test_type": get_path(normalized, "metadata.tipo_esperado", test_type),
        "arquivos": detected_files_for_legacy(normalized),
        "proctor_admin": {
            "interessado": dados.get("interessado"),
            "obra": dados.get("obra"),
            "proctor": proctor.get("energia"),
            "registro": dados.get("registro_numero"),
            "estaca": dados.get("local_furo_estaca"),
            "profundidade": dados.get("profundidade_furo"),
            "data_ensaio": dados.get("data_ensaio"),
            "procedencia": dados.get("procedencia_rua"),
            "cidade": dados.get("cidade"),
            "responsavel_tecnico": dados.get("responsavel_tecnico"),
            "observacoes": dados.get("observacoes"),
        },
        "cbr_admin": {
            "registro": cbr.get("registro_numero_cbr") or dados.get("registro_numero"),
            "molde_numero": cbr.get("molde_numero"),
            "peso_molde": cbr.get("peso_molde_g"),
            "volume_molde": cbr.get("volume_molde_cm3"),
            "numero_camadas": cbr.get("numero_camadas"),
            "golpes_camada": cbr.get("golpes_por_camada"),
            "peso_soquete": cbr.get("peso_soquete_g"),
            "espessura_disco": cbr.get("espessura_disco_espacador"),
            "altura_cilindro": cbr.get("altura_cilindro_mm"),
            "constante_prensa": cbr.get("constante_prensa"),
        },
        "granulometria_admin": {
            "empresa_executora": granulometria.get("empresa_executora"),
            "obra": granulometria.get("obra") or dados.get("obra"),
            "procedencia": granulometria.get("procedencia_rua") or dados.get("procedencia_rua"),
            "camada": granulometria.get("camada"),
            "estaca": granulometria.get("local_furo_estaca") or dados.get("local_furo_estaca"),
            "lado": granulometria.get("lado"),
            "profundidade": granulometria.get("profundidade_furo") or dados.get("profundidade_furo"),
            "data_ensaio": granulometria.get("data_ensaio") or dados.get("data_ensaio"),
            "laboratorio": granulometria.get("laboratorio"),
            "operador": granulometria.get("operador"),
            "laboratorista": granulometria.get("laboratorista"),
            "registro": granulometria.get("registro_numero") or dados.get("registro_numero"),
        },
        "compactacao": {
            "umidade_otima": proctor_result.get("umidade_otima_percent"),
            "densidade_maxima": proctor_result.get("densidade_maxima_g_cm3"),
            "higroscopica": moisture_block_for_legacy(hygroscopic),
            "pontos": proctor.get("pontos") or [],
        },
        "cbr": {
            "cbr": cbr_result.get("cbr_percent"),
            "expansao": cbr_result.get("expansao_percent"),
            "higroscopica": moisture_block_for_legacy(hygroscopic),
            "moldagem": moisture_block_for_legacy(cbr.get("moldagem")),
            "calculo_moldagem": cbr.get("calculo_moldagem") or {},
            "verificacao_moldagem": cbr.get("verificacao_moldagem") or {},
            "leituras": cbr.get("penetracao") or [],
        },
        "granulometria": {
            "passante_10": passante_from_sieves(granulometria.get("peneiras"), "10"),
            "passante_40": passante_from_sieves(granulometria.get("peneiras"), "40"),
            "passante_200": passante_from_sieves(granulometria.get("peneiras"), "200"),
            "classificacao_trb": gran_class.get("trb"),
            "classificacao_sucs": gran_class.get("sucs"),
            "limites": {
                "ll": gran_limits.get("limite_liquidez") or gran_limits.get("ll") or "NL",
                "lp": gran_limits.get("limite_plasticidade") or gran_limits.get("lp") or "NP",
                "ip": gran_limits.get("indice_plasticidade") or gran_limits.get("ip") or "NP",
            },
        },
        "warnings": raw.get("warnings", []),
    }
    add_flat_compatibility(legacy)
    return legacy


def add_flat_compatibility(data: dict[str, Any]) -> dict[str, Any]:
    proctor = data.get("proctor_admin") or {}
    cbr = data.get("cbr_admin") or {}
    granulometria = data.get("granulometria_admin") or {}
    data.update({
        "interessado": proctor.get("interessado") or "",
        "obra": proctor.get("obra") or granulometria.get("obra") or "",
        "proctor": proctor.get("proctor") or "",
        "registro": proctor.get("registro") or cbr.get("registro") or granulometria.get("registro") or "",
        "estaca": proctor.get("estaca") or granulometria.get("estaca") or "",
        "profundidade": proctor.get("profundidade") or granulometria.get("profundidade") or "",
        "data_ensaio": proctor.get("data_ensaio") or granulometria.get("data_ensaio") or "",
        "procedencia": proctor.get("procedencia") or granulometria.get("procedencia") or "",
        "cidade": proctor.get("cidade") or "",
        "responsavel_tecnico": proctor.get("responsavel_tecnico") or "",
        "observacoes": proctor.get("observacoes") or "",
        "empresa_executora": granulometria.get("empresa_executora") or "",
        "camada": granulometria.get("camada") or "",
        "lado": granulometria.get("lado") or "",
        "laboratorio": granulometria.get("laboratorio") or "",
        "operador": granulometria.get("operador") or "",
        "laboratorista": granulometria.get("laboratorista") or "",
    })
    return data


def passante_from_sieves(peneiras: Any, target: str) -> Any:
    if not isinstance(peneiras, list):
        return None
    for row in peneiras:
        if not isinstance(row, dict):
            continue
        sieve = str(row.get("peneira") or "").replace("#", "").strip()
        if sieve == target:
            return row.get("percentual_passante")
    return None


def calculate_proctor(normalized: dict[str, Any]) -> dict[str, Any]:
    proctor = normalized.get("proctor") if isinstance(normalized.get("proctor"), dict) else {}
    calculated_points = []
    for point in proctor.get("pontos") or []:
        if not isinstance(point, dict):
            continue
        moisture = None
        capsules = point.get("capsulas")
        if isinstance(capsules, list) and capsules:
            moisture_calc = calculate_cbr_moisture_blocks(capsules[0], {})
            moisture = moisture_calc.get("higroscopica", {}).get("umidade_percent")
        calculated_points.append(
            calculate_proctor_point(
                point.get("peso_solo_umido_molde_g"),
                proctor.get("peso_molde_g"),
                proctor.get("volume_molde_cm3"),
                moisture,
            )
        )
    curve = calculate_proctor_curve([
        {
            "umidade_percent": item.get("umidade_percent") or item.get("umidade_media_percent"),
            "densidade_seca_g_cm3": item.get("densidade_seca_g_cm3"),
        }
        for item in calculated_points
    ])
    return {
        "points": calculated_points,
        "umidade_otima_percent": curve.get("umidade_otima_percent"),
        "densidade_maxima_g_cm3": curve.get("densidade_maxima_g_cm3"),
        "issues": [
            issue
            for item in [*calculated_points, curve]
            for issue in item.get("issues", [])
        ],
    }


def calculate_cbr(normalized: dict[str, Any]) -> dict[str, Any]:
    cbr = normalized.get("cbr") if isinstance(normalized.get("cbr"), dict) else {}
    moisture = calculate_cbr_moisture_blocks(cbr.get("higroscopica"), cbr.get("moldagem"))
    final = calculate_cbr_final(cbr.get("penetracao") or cbr.get("leituras") or [])
    molding = calculate_molding_check(
        get_path(cbr, "verificacao_moldagem.peso_bruto_umido_cp_molde_kg"),
        cbr.get("peso_molde_g"),
        cbr.get("volume_molde_cm3"),
        get_path(moisture, "moldagem.umidade_percent"),
        get_path(cbr, "verificacao_moldagem.peso_cp_umido_kg"),
    )
    return {
        "higroscopica": moisture.get("higroscopica", {}),
        "moldagem": moisture.get("moldagem", {}),
        "penetracao": cbr.get("penetracao") or cbr.get("leituras") or [],
        "cbr_percent": final.get("cbr_percent"),
        "expansao_percent": get_path(cbr, "expansao.expansao_percent_lida"),
        "verificacao_moldagem": molding,
        "issues": [*moisture.get("issues", []), *final.get("issues", []), *molding.get("issues", [])],
    }


def calculate_all(normalized: dict[str, Any]) -> dict[str, Any]:
    granulometria = (
        normalized.get("granulometria")
        if isinstance(normalized.get("granulometria"), dict)
        else {}
    )
    return {
        "proctor": calculate_proctor(normalized),
        "cbr": calculate_cbr(normalized),
        "granulometria": calculate_granulometry(
            granulometria.get("amostra_total") or {},
            granulometria.get("peneiras") or [],
        ),
    }


def build_review_payload(raw_extraction: dict[str, Any] | None) -> dict[str, Any]:
    extracted_data = deepcopy(raw_extraction or {})
    normalized_data, normalization_issues = normalize_extraction(extracted_data)
    apply_hygroscopic_fallback(normalized_data)
    calculated_data = calculate_all(normalized_data)
    test_type = infer_test_type_from_bundle(normalized_data)
    validation_issues = [
        *normalization_issues,
        *validate_bundle(normalized_data, test_type=test_type),
    ]
    if is_legacy_extraction(extracted_data):
        review_data = deepcopy(extracted_data)
    else:
        review_data = build_legacy_review_data(normalized_data, extracted_data)
    apply_hygroscopic_fallback(review_data)
    review_data["_pipeline"] = {
        "extracted_data": extracted_data,
        "normalized_data": normalized_data,
        "calculated_data": calculated_data,
        "validation_issues": validation_issues,
    }
    return {
        "extracted_data": extracted_data,
        "normalized_data": normalized_data,
        "calculated_data": calculated_data,
        "validation_issues": validation_issues,
        "review_data": review_data,
    }


def is_legacy_extraction(data: dict[str, Any]) -> bool:
    return (
        "metadata" not in data
        and "dados_comuns" not in data
        and (
            "compactacao" in data
            or "proctor_admin" in data
            or "granulometria_admin" in data
        )
    )
