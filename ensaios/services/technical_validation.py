from __future__ import annotations

from typing import Any

from .calculations import calculate_moisture


def make_issue(
    field: str,
    message: str,
    severity: str = "error",
    test_type: str | None = None,
    code: str | None = None,
) -> dict[str, str]:
    issue = {
        "field": field,
        "message": message,
        "severity": severity,
    }
    if test_type:
        issue["test_type"] = test_type
    if code:
        issue["code"] = code
    return issue


def is_blank(value: Any) -> bool:
    return value is None or value == "" or value == []


def block(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def first_value(data: dict[str, Any], *paths: str) -> Any:
    for path in paths:
        current: Any = data
        for part in path.split("."):
            if not isinstance(current, dict):
                current = None
                break
            current = current.get(part)
        if not is_blank(current):
            return current
    return None


def require(issues: list[dict[str, str]], data: dict[str, Any], field: str, label: str, test_type: str) -> None:
    if is_blank(first_value(data, field)):
        issues.append(
            make_issue(field, f"Campo obrigatorio ausente: {label}.", "error", test_type, "required")
        )


def validate_moisture_block(
    issues: list[dict[str, str]],
    data: dict[str, Any],
    path: str,
    label: str,
    test_type: str,
) -> None:
    value = first_value(data, path)
    if not isinstance(value, dict):
        issues.append(make_issue(path, f"{label} ausente.", "error", test_type, "required"))
        return

    for key, key_label in {
        "capsula": "capsula",
        "peso_bruto_umido_g": "peso bruto umido",
        "peso_bruto_seco_g": "peso bruto seco",
        "tara_capsula_g": "tara da capsula",
    }.items():
        old_key = key.removesuffix("_g")
        if is_blank(value.get(key)) and is_blank(value.get(old_key)):
            issues.append(
                make_issue(
                    f"{path}.{key}",
                    f"{label}: {key_label} ausente.",
                    "error",
                    test_type,
                    "required",
                )
            )

    calculated = calculate_moisture(
        value.get("peso_bruto_umido_g", value.get("peso_bruto_umido")),
        value.get("peso_bruto_seco_g", value.get("peso_bruto_seco")),
        value.get("tara_capsula_g", value.get("tara_capsula")),
    )
    for item in calculated.get("issues", []):
        if item.get("severity") == "error":
            issues.append(
                make_issue(
                    path,
                    f"{label}: {item.get('message')}",
                    "error",
                    test_type,
                    item.get("code"),
                )
            )


def validate_proctor(data: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    test_type = "proctor"
    required = {
        "dados_comuns.interessado": "Interessado / contratante",
        "dados_comuns.obra": "Obra",
        "dados_comuns.procedencia_rua": "Procedencia / rua",
        "dados_comuns.local_furo_estaca": "Local / furo / estaca",
        "dados_comuns.data_ensaio": "Data do ensaio",
        "proctor.energia": "Energia Proctor",
        "proctor.molde_numero": "Molde",
        "proctor.peso_molde_g": "Peso do molde",
        "proctor.volume_molde_cm3": "Volume do molde",
        "proctor.numero_camadas": "Numero de camadas",
        "proctor.golpes_por_camada": "Golpes por camada",
    }
    for field, label in required.items():
        require(issues, data, field, label, test_type)

    points = first_value(data, "proctor.pontos")
    if not isinstance(points, list) or not points:
        issues.append(make_issue("proctor.pontos", "Pontos de compactacao ausentes.", "error", test_type, "required"))
    else:
        for index, point in enumerate(points, start=1):
            if not isinstance(point, dict):
                continue
            capsules = point.get("capsulas")
            if not isinstance(capsules, list) or not capsules:
                issues.append(
                    make_issue(
                        f"proctor.pontos[{index}].capsulas",
                        f"Ponto Proctor {index}: capsulas de umidade ausentes.",
                        "error",
                        test_type,
                        "required",
                    )
                )
    return issues


def validate_cbr(data: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    test_type = "cbr"
    required = {
        "cbr.registro_numero_cbr": "Registro do CBR",
        "cbr.molde_numero": "Molde",
        "cbr.peso_molde_g": "Peso do molde",
        "cbr.volume_molde_cm3": "Volume do molde",
        "cbr.numero_camadas": "Numero de camadas",
        "cbr.golpes_por_camada": "Golpes por camada",
        "cbr.peso_soquete_g": "Peso do soquete",
        "cbr.espessura_disco_espacador": "Espessura do disco espacador",
        "cbr.altura_cilindro_mm": "Altura do cilindro",
        "cbr.constante_prensa": "Constante da prensa",
    }
    for field, label in required.items():
        require(issues, data, field, label, test_type)

    validate_moisture_block(issues, data, "cbr.higroscopica", "Umidade higroscopica do CBR", test_type)
    validate_moisture_block(issues, data, "cbr.moldagem", "Umidade de moldagem do CBR", test_type)

    penetration = first_value(data, "cbr.penetracao", "cbr.leituras")
    if not isinstance(penetration, list) or not penetration:
        issues.append(make_issue("cbr.penetracao", "Leituras de penetracao ausentes.", "error", test_type, "required"))

    expansion = first_value(data, "cbr.expansao")
    if not isinstance(expansion, dict) or all(is_blank(value) for value in expansion.values()):
        issues.append(make_issue("cbr.expansao", "Leituras de expansao ausentes.", "error", test_type, "required"))
    return issues


def validate_granulometria(data: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    test_type = "granulometria"
    required = {
        "granulometria.empresa_executora": "Empresa executora",
        "granulometria.obra": "Obra",
        "granulometria.procedencia_rua": "Procedencia / rua",
        "granulometria.local_furo_estaca": "Local / furo / estaca",
        "granulometria.data_ensaio": "Data do ensaio",
    }
    for field, label in required.items():
        require(issues, data, field, label, test_type)

    sample = first_value(data, "granulometria.amostra_total")
    if not isinstance(sample, dict) or all(is_blank(value) for value in sample.values()):
        issues.append(make_issue("granulometria.amostra_total", "Amostra total ausente.", "error", test_type, "required"))

    sieves = first_value(data, "granulometria.peneiras")
    if not isinstance(sieves, list) or not sieves:
        issues.append(make_issue("granulometria.peneiras", "Peneiras ausentes.", "error", test_type, "required"))
    return issues


def validate_bundle(data: dict[str, Any], test_type: str = "ambos") -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if test_type in {"compactacao_cbr", "ambos", "proctor"}:
        issues.extend(validate_proctor(data))
        issues.extend(validate_cbr(data))
    if test_type in {"granulometria", "ambos"}:
        issues.extend(validate_granulometria(data))
    return issues

