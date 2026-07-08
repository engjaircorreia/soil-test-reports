import importlib

import pytest


def require_module(name):
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        pytest.xfail(f"{name} ainda nao foi implementado: {exc}")


def assert_no_issues(result):
    assert result.get("issues", []) == []


def test_calculate_moisture_from_capsule_weights():
    calculations = require_module("ensaios.services.calculations")

    result = calculations.calculate_moisture(
        peso_bruto_umido_g=101.5,
        peso_bruto_seco_g=101.2,
        tara_capsula_g=17.99,
    )

    assert_no_issues(result)
    assert result["peso_agua_g"] == pytest.approx(0.3)
    assert result["peso_solo_seco_g"] == pytest.approx(83.21)
    assert result["umidade_percent"] == pytest.approx(0.3605, abs=0.001)


def test_calculate_moisture_returns_error_for_physically_impossible_weights():
    calculations = require_module("ensaios.services.calculations")

    result = calculations.calculate_moisture(
        peso_bruto_umido_g=101.0,
        peso_bruto_seco_g=101.2,
        tara_capsula_g=17.99,
    )

    assert result["peso_agua_g"] is None
    assert result["umidade_percent"] is None
    assert result["issues"]
    assert result["issues"][0]["severity"] == "error"


def test_calculate_proctor_point_uses_measured_weights_not_ai_final_result():
    calculations = require_module("ensaios.services.calculations")

    result = calculations.calculate_proctor_point(
        peso_umido_molde_g=9874,
        peso_molde_g=5414,
        volume_molde_cm3=2068,
        umidade_percent=10.0,
    )

    assert_no_issues(result)
    assert result["peso_solo_umido_g"] == pytest.approx(4460)
    assert result["densidade_umida_g_cm3"] == pytest.approx(2.1567, abs=0.0005)
    assert result["densidade_seca_g_cm3"] == pytest.approx(1.9606, abs=0.0005)


def test_calculate_proctor_curve_uses_highest_dry_density_as_initial_rule():
    calculations = require_module("ensaios.services.calculations")

    result = calculations.calculate_proctor_curve(
        [
            {"umidade_percent": 3.5, "densidade_seca_g_cm3": 1.85},
            {"umidade_percent": 5.0, "densidade_seca_g_cm3": 1.933},
            {"umidade_percent": 10.0, "densidade_seca_g_cm3": 1.96},
            {"umidade_percent": 13.1, "densidade_seca_g_cm3": 1.865},
        ]
    )

    assert_no_issues(result)
    assert result["umidade_otima_percent"] == pytest.approx(10.0)
    assert result["densidade_maxima_g_cm3"] == pytest.approx(1.96)


def test_calculate_water_to_add_uses_hygroscopic_moisture_and_soil_weights():
    calculations = require_module("ensaios.services.calculations")

    result = calculations.calculate_water_to_add(
        umidade_otima_percent=10.0,
        umidade_higroscopica_percent=0.36,
        peso_solo_seco_passando_peneira_4_g=5978,
        peso_pedregulho_retido_peneira_4_g=0,
    )

    assert_no_issues(result)
    assert result["diferenca_umidade_percent"] == pytest.approx(9.64)
    assert result["agua_a_juntar_g"] == pytest.approx(576.3, abs=0.2)


def test_calculate_cbr_final_uses_percent_rows_not_standard_pressure_column():
    calculations = require_module("ensaios.services.calculations")

    result = calculations.calculate_cbr_final(
        [
            {"penetracao_mm": 2.54, "cbr_percent": 39.0, "pressao_padrao_kg_cm2": 70},
            {"penetracao_mm": 5.08, "cbr_percent": 31.0, "pressao_padrao_kg_cm2": 105},
            {"penetracao_mm": 7.62, "cbr_percent": 30.0, "pressao_padrao_kg_cm2": 133},
        ]
    )

    assert_no_issues(result)
    assert result["cbr_percent"] == pytest.approx(39.0)
    assert result["cbr_percent"] != 70


def test_calculate_molding_check_derives_cp_weight_and_densities():
    calculations = require_module("ensaios.services.calculations")

    result = calculations.calculate_molding_check(
        peso_bruto_umido_cp_molde_kg=9.605,
        peso_molde_g=4775,
        volume_molde_cm3=2088,
        umidade_moldagem_percent=10.7,
    )

    assert_no_issues(result)
    assert result["peso_cp_umido_kg"] == pytest.approx(4.83)
    assert result["densidade_umida_g_cm3"] == pytest.approx(2.313, abs=0.001)
    assert result["densidade_seca_g_cm3"] == pytest.approx(2.089, abs=0.001)


def test_calculate_granulometry_keeps_passant_percentages_in_monotonic_order():
    calculations = require_module("ensaios.services.calculations")

    result = calculations.calculate_granulometry(
        amostra_total={"peso_seco_total_g": 1500},
        peneiras=[
            {"peneira": "10", "percentual_passante": 40.1},
            {"peneira": "40", "percentual_passante": 26.0},
            {"peneira": "200", "percentual_passante": 14.0},
        ],
    )

    assert_no_issues(result)
    assert result["passante_10_percent"] == pytest.approx(40.1)
    assert result["passante_40_percent"] == pytest.approx(26.0)
    assert result["passante_200_percent"] == pytest.approx(14.0)

