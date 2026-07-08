from __future__ import annotations

from typing import Any

from .normalization import normalize_number


def issue(field: str, message: str, severity: str = "warning", code: str | None = None) -> dict[str, str]:
    data = {"field": field, "message": message, "severity": severity}
    if code:
        data["code"] = code
    return data


def _num(value: Any, context: str | None = None) -> float | None:
    normalized = normalize_number(value, context=context)
    return normalized if isinstance(normalized, float) else None


def _base_result(**values: Any) -> dict[str, Any]:
    values.setdefault("issues", [])
    return values


def calculate_moisture(
    peso_bruto_umido_g: Any,
    peso_bruto_seco_g: Any,
    tara_capsula_g: Any,
) -> dict[str, Any]:
    wet = _num(peso_bruto_umido_g)
    dry = _num(peso_bruto_seco_g)
    tare = _num(tara_capsula_g)
    if wet is None or dry is None or tare is None:
        return _base_result(
            peso_agua_g=None,
            peso_solo_seco_g=None,
            umidade_percent=None,
            issues=[issue("moisture", "Dados de umidade incompletos.")],
        )
    if wet < dry:
        return _base_result(
            peso_agua_g=None,
            peso_solo_seco_g=None,
            umidade_percent=None,
            issues=[issue("peso_bruto_umido_g", "Peso bruto umido menor que o peso bruto seco.", "error")],
        )
    if dry <= tare:
        return _base_result(
            peso_agua_g=None,
            peso_solo_seco_g=None,
            umidade_percent=None,
            issues=[issue("tara_capsula_g", "Peso bruto seco deve ser maior que a tara da capsula.", "error")],
        )
    water = wet - dry
    dry_soil = dry - tare
    return _base_result(
        peso_agua_g=water,
        peso_solo_seco_g=dry_soil,
        umidade_percent=water / dry_soil * 100,
    )


def calculate_proctor_point(
    peso_umido_molde_g: Any,
    peso_molde_g: Any,
    volume_molde_cm3: Any,
    umidade_percent: Any,
) -> dict[str, Any]:
    gross = _num(peso_umido_molde_g)
    mold = _num(peso_molde_g)
    volume = _num(volume_molde_cm3)
    moisture = _num(umidade_percent)
    if gross is None or mold is None or volume is None or moisture is None:
        return _base_result(
            peso_solo_umido_g=None,
            densidade_umida_g_cm3=None,
            densidade_seca_g_cm3=None,
            issues=[issue("proctor_point", "Dados do ponto Proctor incompletos.")],
        )
    if volume <= 0:
        return _base_result(
            peso_solo_umido_g=None,
            densidade_umida_g_cm3=None,
            densidade_seca_g_cm3=None,
            issues=[issue("volume_molde_cm3", "Volume do molde deve ser maior que zero.", "error")],
        )
    if gross < mold:
        return _base_result(
            peso_solo_umido_g=None,
            densidade_umida_g_cm3=None,
            densidade_seca_g_cm3=None,
            issues=[issue("peso_umido_molde_g", "Peso com molde menor que o peso do molde.", "error")],
        )
    if moisture <= -100:
        return _base_result(
            peso_solo_umido_g=None,
            densidade_umida_g_cm3=None,
            densidade_seca_g_cm3=None,
            issues=[issue("umidade_percent", "Umidade invalida.", "error")],
        )

    wet_soil = gross - mold
    wet_density = wet_soil / volume
    dry_density = wet_density / (1 + moisture / 100)
    return _base_result(
        peso_solo_umido_g=wet_soil,
        densidade_umida_g_cm3=wet_density,
        densidade_seca_g_cm3=dry_density,
    )


def calculate_proctor_curve(points: list[dict[str, Any]]) -> dict[str, Any]:
    valid_points = []
    for point in points:
        moisture = _num(point.get("umidade_percent"))
        dry_density = _num(point.get("densidade_seca_g_cm3"), context="density")
        if moisture is not None and dry_density is not None:
            valid_points.append((moisture, dry_density))
    if not valid_points:
        return _base_result(
            umidade_otima_percent=None,
            densidade_maxima_g_cm3=None,
            issues=[issue("proctor.points", "Nenhum ponto Proctor valido para calcular a curva.")],
        )
    optimum_moisture, max_density = max(valid_points, key=lambda item: item[1])
    return _base_result(
        umidade_otima_percent=optimum_moisture,
        densidade_maxima_g_cm3=max_density,
    )


def calculate_cbr_moisture_blocks(
    higroscopica: dict[str, Any] | None,
    moldagem: dict[str, Any] | None,
) -> dict[str, Any]:
    higroscopica = higroscopica or {}
    moldagem = moldagem or {}
    hygro = calculate_moisture(
        higroscopica.get("peso_bruto_umido_g", higroscopica.get("peso_bruto_umido")),
        higroscopica.get("peso_bruto_seco_g", higroscopica.get("peso_bruto_seco")),
        higroscopica.get("tara_capsula_g", higroscopica.get("tara_capsula")),
    )
    molding = calculate_moisture(
        moldagem.get("peso_bruto_umido_g", moldagem.get("peso_bruto_umido")),
        moldagem.get("peso_bruto_seco_g", moldagem.get("peso_bruto_seco")),
        moldagem.get("tara_capsula_g", moldagem.get("tara_capsula")),
    )
    return {
        "higroscopica": hygro,
        "moldagem": molding,
        "issues": [*hygro.get("issues", []), *molding.get("issues", [])],
    }


def calculate_water_to_add(
    umidade_otima_percent: Any,
    umidade_higroscopica_percent: Any,
    peso_solo_seco_passando_peneira_4_g: Any,
    peso_pedregulho_retido_peneira_4_g: Any = 0,
) -> dict[str, Any]:
    optimum = _num(umidade_otima_percent)
    hygroscopic = _num(umidade_higroscopica_percent)
    passing = _num(peso_solo_seco_passando_peneira_4_g)
    retained = _num(peso_pedregulho_retido_peneira_4_g) or 0.0
    if optimum is None or hygroscopic is None or passing is None:
        return _base_result(
            diferenca_umidade_percent=None,
            agua_a_juntar_g=None,
            issues=[issue("cbr.water_to_add", "Dados incompletos para calcular agua a juntar.")],
        )
    difference = optimum - hygroscopic
    if difference < 0:
        return _base_result(
            diferenca_umidade_percent=difference,
            agua_a_juntar_g=None,
            issues=[issue("umidade_higroscopica_percent", "Umidade higroscopica maior que a umidade otima.", "error")],
        )
    dry_mass = passing + retained
    return _base_result(
        diferenca_umidade_percent=difference,
        agua_a_juntar_g=dry_mass * difference / 100,
    )


def calculate_cbr_penetration(
    penetration_rows: list[dict[str, Any]],
    constante_prensa: Any,
) -> dict[str, Any]:
    constant = _num(constante_prensa)
    calculated_rows: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    if constant is None:
        issues.append(issue("constante_prensa", "Constante da prensa ausente."))

    for row in penetration_rows or []:
        corrected = _num(row.get("pressao_corrigida_kg_cm2"))
        reading = _num(row.get("leitura_extensometro"))
        if corrected is None and reading is not None and constant is not None:
            corrected = reading * constant
        cbr_percent = _num(row.get("cbr_percent"))
        calculated_rows.append({
            **row,
            "pressao_corrigida_kg_cm2": corrected,
            "cbr_percent": cbr_percent,
        })
    return {"rows": calculated_rows, "issues": issues}


def calculate_cbr_final(cbr_percent_rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [
        _num(row.get("cbr_percent"))
        for row in cbr_percent_rows or []
        if isinstance(row, dict)
    ]
    values = [value for value in values if value is not None]
    if not values:
        return _base_result(
            cbr_percent=None,
            issues=[issue("cbr.penetracao", "Nenhum percentual de CBR valido encontrado.")],
        )
    return _base_result(cbr_percent=max(values))


def calculate_expansion(
    leitura_inicial_mm: Any,
    leitura_final_mm: Any,
    altura_cilindro_mm: Any,
) -> dict[str, Any]:
    initial = _num(leitura_inicial_mm)
    final = _num(leitura_final_mm)
    height = _num(altura_cilindro_mm)
    if initial is None or final is None or height is None:
        return _base_result(
            expansao_percent=None,
            diferenca_mm=None,
            issues=[issue("cbr.expansao", "Dados de expansao incompletos.")],
        )
    if height <= 0:
        return _base_result(
            expansao_percent=None,
            diferenca_mm=None,
            issues=[issue("altura_cilindro_mm", "Altura do cilindro deve ser maior que zero.", "error")],
        )
    difference = final - initial
    return _base_result(
        expansao_percent=difference / height * 100,
        diferenca_mm=difference,
    )


def calculate_molding_check(
    peso_bruto_umido_cp_molde_kg: Any,
    peso_molde_g: Any,
    volume_molde_cm3: Any,
    umidade_moldagem_percent: Any,
    peso_cp_umido_kg: Any = None,
) -> dict[str, Any]:
    gross_kg = _num(peso_bruto_umido_cp_molde_kg)
    mold_g = _num(peso_molde_g)
    volume = _num(volume_molde_cm3)
    moisture = _num(umidade_moldagem_percent)
    cp_kg = _num(peso_cp_umido_kg)
    if gross_kg is None or mold_g is None or volume is None or moisture is None:
        return _base_result(
            peso_cp_umido_kg=None,
            densidade_umida_g_cm3=None,
            densidade_seca_g_cm3=None,
            issues=[issue("cbr.verificacao_moldagem", "Dados incompletos para verificacao da moldagem.")],
        )
    if volume <= 0:
        return _base_result(
            peso_cp_umido_kg=None,
            densidade_umida_g_cm3=None,
            densidade_seca_g_cm3=None,
            issues=[issue("volume_molde_cm3", "Volume do molde deve ser maior que zero.", "error")],
        )
    if cp_kg is None:
        cp_kg = gross_kg - mold_g / 1000
    if cp_kg < 0:
        return _base_result(
            peso_cp_umido_kg=None,
            densidade_umida_g_cm3=None,
            densidade_seca_g_cm3=None,
            issues=[issue("peso_cp_umido_kg", "Peso do corpo de prova umido invalido.", "error")],
        )
    wet_density = cp_kg * 1000 / volume
    dry_density = wet_density / (1 + moisture / 100)
    return _base_result(
        peso_cp_umido_kg=cp_kg,
        densidade_umida_g_cm3=wet_density,
        densidade_seca_g_cm3=dry_density,
    )


def calculate_granulometry(
    amostra_total: dict[str, Any] | None,
    peneiras: list[dict[str, Any]],
) -> dict[str, Any]:
    del amostra_total
    values: dict[str, float] = {}
    issues: list[dict[str, str]] = []
    for row in peneiras or []:
        sieve = str(row.get("peneira") or "").replace("#", "").strip()
        passant = _num(row.get("percentual_passante"))
        if passant is None:
            continue
        if not 0 <= passant <= 100:
            issues.append(issue(f"peneira_{sieve}", "Percentual passante fora da faixa 0-100.", "error"))
            continue
        values[sieve] = passant

    p10 = values.get("10")
    p40 = values.get("40")
    p200 = values.get("200")
    if p10 is not None and p40 is not None and p40 > p10:
        issues.append(issue("peneira_40", "Passante #40 maior que passante #10.", "error"))
    if p40 is not None and p200 is not None and p200 > p40:
        issues.append(issue("peneira_200", "Passante #200 maior que passante #40.", "error"))
    return _base_result(
        passante_10_percent=p10,
        passante_40_percent=p40,
        passante_200_percent=p200,
        issues=issues,
    )

