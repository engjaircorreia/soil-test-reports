from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from django.conf import settings

from .validation import validate_workbook


TEMPLATE_MAP = {
    ("compactacao_cbr", "pt"): "compactacao_cbr_modelo_limpo.xlsx",
    ("compactacao_cbr", "en"): "compaction_cbr_clean_template_en.xlsx",
    ("granulometria", "pt"): "granulometria_modelo_limpo.xlsx",
    ("granulometria", "en"): "granulometry_clean_template_en.xlsx",
}


def fmt(value: float | int | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if abs(value - round(value)) < 1e-10:
        return str(int(round(value)))
    return f"{value:.12f}".rstrip("0").rstrip(".")


def set_v(xml: str, cell: str, value: float | int | str | None) -> str:
    return set_cell(xml, cell, value, "n")


def set_cell(
    xml: str,
    cell: str,
    value: float | int | str | None,
    cell_type: str | None = None,
    remove_formula: bool = False,
) -> str:
    value_xml = escape(fmt(value))

    def with_cell_type(open_tag: str) -> str:
        if not cell_type:
            return open_tag
        if cell_type == "n":
            return re.sub(r'\st="[^"]*"', "", open_tag, count=1)
        if re.search(r'\st="[^"]*"', open_tag):
            return re.sub(r'\st="[^"]*"', f' t="{cell_type}"', open_tag, count=1)
        return open_tag[:-1] + f' t="{cell_type}">'

    full = re.compile(r'(<c\b(?=[^>]*\br="' + re.escape(cell) + r'")[^>]*(?<!/)>)(.*?)(</c>)', re.S)

    def replace_full(match: re.Match) -> str:
        open_tag = with_cell_type(match.group(1))
        body = match.group(2)
        if remove_formula:
            body = re.sub(r"<f\b[^>]*/>", "", body, flags=re.S)
            body = re.sub(r"<f\b[^>]*>.*?</f>", "", body, flags=re.S)
        if re.search(r"<v\b[^>]*/>", body, re.S):
            body = re.sub(
                r"<v\b[^>]*/>",
                f"<v>{value_xml}</v>",
                body,
                count=1,
                flags=re.S,
            )
        elif re.search(r"<v>.*?</v>", body, re.S):
            body = re.sub(
                r"(<v>)(.*?)(</v>)",
                lambda inner: inner.group(1) + value_xml + inner.group(3),
                body,
                count=1,
                flags=re.S,
            )
        else:
            body = body + f"<v>{value_xml}</v>"
        return open_tag + body + match.group(3)

    xml, count = full.subn(replace_full, xml, count=1)
    if count == 1:
        return xml

    self_closing = re.compile(r'(<c\b(?=[^>]*\br="' + re.escape(cell) + r'")[^>]*)/>', re.S)

    def replace_self_closing(match: re.Match) -> str:
        open_tag = with_cell_type(match.group(1).rstrip("/") + ">")
        return f"{open_tag}<v>{value_xml}</v></c>"

    xml, count = self_closing.subn(replace_self_closing, xml, count=1)
    if count != 1:
        raise RuntimeError(f"Cell {cell} not found")
    return xml


def set_shared_cell(xml: str, cell: str, shared_index: int, remove_formula: bool = False) -> str:
    return set_cell(xml, cell, shared_index, "s", remove_formula=remove_formula)


def replace_si(xml: str, index: int, text: str) -> str:
    spans = [match.span() for match in re.finditer(r"<si>.*?</si>", xml, re.S)]
    if index >= len(spans):
        raise RuntimeError(f"Shared string index {index} not found")
    start, end = spans[index]
    return xml[:start] + f"<si><t>{escape(text)}</t></si>" + xml[end:]


def append_si(xml: str, text: str) -> tuple[str, int]:
    index = len(re.findall(r"<si>", xml))
    item = f"<si><t>{escape(text)}</t></si>"
    xml = xml.replace("</sst>", item + "</sst>")
    for attr in ("count", "uniqueCount"):
        match = re.search(attr + r'="(\d+)"', xml)
        if match:
            xml = xml[: match.start(1)] + str(int(match.group(1)) + 1) + xml[match.end(1) :]
    return xml, index


def copy_part(xlsx: Path, part: str, root: Path) -> None:
    with zipfile.ZipFile(xlsx) as workbook:
        path = root / part
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(workbook.read(part))


def update_zip(xlsx: Path, root: Path, parts: list[str]) -> None:
    subprocess.run(["zip", "-q", str(xlsx.resolve()), *parts], cwd=root, check=True)


def template_path(test_type: str, language: str) -> Path:
    key = (test_type, language)
    if key not in TEMPLATE_MAP:
        raise ValueError(f"Modelo não encontrado para {test_type}/{language}")
    return settings.BASE_DIR / "templates" / TEMPLATE_MAP[key]


def value(data: dict[str, Any], path: str, default=None):
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(part)
    return default if current in ("", None) else current


def text_value(data: dict[str, Any], key: str, default: str = "") -> str:
    raw = data.get(key)
    if raw in (None, ""):
        return default
    return str(raw)


def first_text(data: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        raw = data.get(key)
        if raw not in (None, ""):
            return str(raw)
    return default


def block_text(data: dict[str, Any], block_name: str, key: str, default: str = "") -> str:
    block = data.get(block_name)
    if isinstance(block, dict):
        raw = block.get(key)
        if raw not in (None, ""):
            return str(raw)
    raw = data.get(key)
    if raw not in (None, ""):
        return str(raw)
    return default


def compaction_text(data: dict[str, Any], key: str, default: str = "") -> str:
    for block_name in ("proctor_admin", "cbr_admin"):
        text = block_text(data, block_name, key)
        if text:
            return text
    raw = data.get(key)
    if raw not in (None, ""):
        return str(raw)
    return default


def granulometry_text(data: dict[str, Any], key: str, default: str = "") -> str:
    return block_text(data, "granulometria_admin", key, default)


def excel_date(value_: Any) -> int | str:
    if not value_:
        return ""
    if isinstance(value_, datetime):
        parsed = value_.date()
    elif isinstance(value_, date):
        parsed = value_
    else:
        text = str(value_).strip()
        parsed = None
        for fmt_ in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                parsed = datetime.strptime(text, fmt_).date()
                break
            except ValueError:
                continue
        if parsed is None:
            return text
    return (parsed - date(1899, 12, 30)).days


def append_text_indexes(shared: str, values: dict[str, str]) -> tuple[str, dict[str, int]]:
    indexes: dict[str, int] = {}
    for key, text in values.items():
        shared, indexes[key] = append_si(shared, text)
    return shared, indexes


def set_register_cell(xml: str, cell: str, register: str, shared_index: int) -> str:
    if re.fullmatch(r"\d+([,.]\d+)?", register.strip()):
        return set_cell(xml, cell, register.replace(",", "."), "n")
    return set_shared_cell(xml, cell, shared_index)


def number_text(value_: Any) -> str | None:
    if value_ in (None, ""):
        return None
    text = str(value_).strip().replace(",", ".")
    if any(char in text for char in "¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞"):
        return None
    text = re.sub(r"[^0-9.+-]", "", text)
    return text if re.fullmatch(r"-?\d+(\.\d+)?", text) else None


def number_value(data: dict[str, Any], path: str, default: float) -> float:
    raw = value(data, path, default)
    numeric = number_text(raw)
    return float(numeric) if numeric is not None else float(default)


def cbr_admin_value(data: dict[str, Any], key: str, default: Any) -> Any:
    block = data.get("cbr_admin")
    if isinstance(block, dict) and block.get(key) not in (None, ""):
        return block.get(key)
    return default


def block_at(data: dict[str, Any], path: str) -> dict[str, Any]:
    current = value(data, path, {})
    return current if isinstance(current, dict) else {}


def first_block(data: dict[str, Any], *paths: str) -> dict[str, Any]:
    for path in paths:
        block = block_at(data, path)
        if any(item not in (None, "") for item in block.values()):
            return block
    return {}


def first_valid_moisture_block(data: dict[str, Any], *paths: str) -> dict[str, Any]:
    for path in paths:
        block = valid_moisture_block(block_at(data, path))
        if block:
            return block
    return {}


def block_field(block: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        raw = block.get(key)
        if raw not in (None, ""):
            return raw
    return None


def numeric_block_field(block: dict[str, Any], *keys: str) -> float | None:
    raw = block_field(block, *keys)
    numeric = number_text(raw)
    return float(numeric) if numeric is not None else None


def water_weight(block: dict[str, Any]) -> float | None:
    wet = numeric_block_field(block, "peso_bruto_umido", "peso_bruto_umido_g")
    dry = numeric_block_field(block, "peso_bruto_seco", "peso_bruto_seco_g")
    if wet is None or dry is None:
        return None
    return wet - dry


def grams_value(value_: Any) -> float | None:
    numeric = number_text(value_)
    if numeric is None:
        return None
    value_float = float(numeric)
    if 0 < value_float < 100:
        return value_float * 1000
    return value_float


def kg_value(value_: Any) -> float | None:
    numeric = number_text(value_)
    if numeric is None:
        return None
    value_float = float(numeric)
    if value_float > 100:
        return value_float / 1000
    return value_float


def valid_moisture_block(block: dict[str, Any]) -> dict[str, Any]:
    wet = numeric_block_field(block, "peso_bruto_umido", "peso_bruto_umido_g")
    dry = numeric_block_field(block, "peso_bruto_seco", "peso_bruto_seco_g")
    tare = numeric_block_field(block, "tara_capsula", "peso_capsula", "peso_da_capsula", "tara_da_capsula")
    if wet is None and dry is None and tare is None:
        return {}
    if wet is None or dry is None or tare is None:
        return {}
    if wet < dry or dry < tare:
        return {}
    return block


def set_optional_number(xml: str, cell: str, value_: Any) -> str:
    numeric = number_text(value_)
    return set_v(xml, cell, numeric) if numeric is not None else xml


def set_optional_grams(xml: str, cell: str, value_: Any) -> str:
    grams = grams_value(value_)
    return set_v(xml, cell, grams) if grams is not None else xml


def set_optional_kg(xml: str, cell: str, value_: Any) -> str:
    kg = kg_value(value_)
    return set_v(xml, cell, kg) if kg is not None else xml


def set_mixed_cell(xml: str, cell: str, value_: Any, shared_index: int) -> str:
    numeric = number_text(value_)
    if numeric is not None:
        return set_cell(xml, cell, numeric, "n")
    return set_shared_cell(xml, cell, shared_index)


def compact_defaults(data: dict[str, Any]) -> dict[str, float]:
    opt = number_value(data, "compactacao.umidade_otima", 9.8)
    gdmax = number_value(data, "compactacao.densidade_maxima", 1.95)
    cbr = number_value(data, "cbr.cbr", 32.0)
    exp = number_value(data, "cbr.expansao", 0.5)
    return {"opt": opt, "gdmax": gdmax, "cbr": cbr, "exp": exp}


def list_value(data: dict[str, Any], path: str) -> list[dict[str, Any]]:
    current = value(data, path, [])
    return [item for item in current if isinstance(item, dict)] if isinstance(current, list) else []


def point_field(point: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        raw = point.get(key)
        if raw not in (None, ""):
            return raw
    return None


def point_number(point: dict[str, Any], *keys: str) -> float | None:
    raw = point_field(point, *keys)
    numeric = number_text(raw)
    return float(numeric) if numeric is not None else None


def point_capsule(point: dict[str, Any]) -> dict[str, Any]:
    capsules = point.get("capsulas")
    if isinstance(capsules, list):
        for capsule in capsules:
            if isinstance(capsule, dict):
                return capsule
    return {}


def cbr_readings(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list_value(data, "cbr.leituras") or list_value(data, "cbr.penetracao")


def compaction_points(data: dict[str, Any]) -> list[dict[str, Any]]:
    return list_value(data, "compactacao.pontos")


def require_compaction_points(data: dict[str, Any]) -> list[dict[str, Any]]:
    points = compaction_points(data)
    if not points:
        raise ValueError("pontos brutos de compactação ausentes")
    return points


def reading_target_row(reading: dict[str, Any], fallback: int) -> int:
    raw = point_field(reading, "linha", "row")
    numeric = number_text(raw)
    if numeric is not None:
        row = int(float(numeric))
        if 27 <= row <= 32:
            return row
    return fallback


def generate_compaction_cbr(data: dict[str, Any], language: str, job_id: int, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"job_{job_id}_compactacao_cbr_{language}.xlsx"
    shutil.copy2(template_path("compactacao_cbr", language), out)
    params = compact_defaults(data)
    points = require_compaction_points(data)
    obra = compaction_text(data, "obra", "OBRA")
    estaca = compaction_text(data, "estaca", "ESTACA")
    procedencia = compaction_text(data, "procedencia", obra)
    interessado = compaction_text(data, "interessado")
    registro = compaction_text(data, "registro", f"{job_id:02d}")
    cbr_registro = block_text(data, "cbr_admin", "registro") or registro
    cbr_equipment = {
        "molde_numero": cbr_admin_value(data, "molde_numero", "02"),
        "peso_molde": cbr_admin_value(data, "peso_molde", 5436),
        "volume_molde": cbr_admin_value(data, "volume_molde", 3210),
        "numero_camadas": cbr_admin_value(data, "numero_camadas", 5),
        "golpes_camada": cbr_admin_value(data, "golpes_camada", 26),
        "peso_soquete": cbr_admin_value(data, "peso_soquete", 4536),
        "espessura_disco": cbr_admin_value(data, "espessura_disco", '2½"'),
        "altura_cilindro": cbr_admin_value(data, "altura_cilindro", 114),
        "constante_prensa": cbr_admin_value(data, "constante_prensa", 0.0839),
    }
    proctor = compaction_text(data, "proctor")
    cidade = compaction_text(data, "cidade")
    responsavel = compaction_text(data, "responsavel_tecnico")
    profundidade = compaction_text(data, "profundidade")
    observacoes = compaction_text(data, "observacoes")
    data_ensaio = excel_date(compaction_text(data, "data_ensaio"))
    hygroscopic = first_valid_moisture_block(
        data,
        "cbr.higroscopica",
        "compactacao.higroscopica",
        "proctor.higroscopica",
    )
    molding_moisture = valid_moisture_block(first_block(data, "cbr.moldagem"))
    molding_calc = block_at(data, "cbr.calculo_moldagem")
    molding_check = block_at(data, "cbr.verificacao_moldagem")
    hygro_capsule = str(block_field(hygroscopic, "capsula", "capsula_n", "capsula_numero") or "")
    molding_capsule = str(block_field(molding_moisture, "capsula", "capsula_n", "capsula_numero") or "")

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        parts = ["xl/sharedStrings.xml", "xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml"]
        for part in parts:
            copy_part(out, part, root)

        shared = (root / "xl/sharedStrings.xml").read_text(encoding="utf-8")
        location_label = "LOCATION" if language == "en" else "LOCAL"
        project_label = "PROJECT" if language == "en" else "OBRA"
        shared, admin = append_text_indexes(
            shared,
            {
                "interessado": interessado,
                "obra": f"{project_label}: {obra}",
                "proctor": proctor,
                "registro": registro,
                "cbr_registro": cbr_registro,
                "local": f"{location_label}: {estaca}",
                "profundidade": profundidade,
                "procedencia": procedencia,
                "cidade": cidade,
                "responsavel": responsavel,
                "observacoes": ("NOTES: " if language == "en" else "OBSERVAÇÕES: ") + observacoes,
                "point_1": "1",
                "point_2": "2",
                "point_3": "3",
                "point_4": "4",
                "point_5": "5",
                "capsule_h": hygro_capsule,
                "capsule_m": molding_capsule,
                "blank": "",
                "interessado_label": "INTERESTED PARTY:" if language == "en" else "INTERESSADO:",
                "obra_label": f"{project_label}:",
                "estaca_value": estaca,
                "cbr_molde_numero": str(cbr_equipment["molde_numero"]),
                "cbr_peso_molde": str(cbr_equipment["peso_molde"]),
                "cbr_volume_molde": str(cbr_equipment["volume_molde"]),
                "cbr_numero_camadas": str(cbr_equipment["numero_camadas"]),
                "cbr_golpes_camada": str(cbr_equipment["golpes_camada"]),
                "cbr_peso_soquete": str(cbr_equipment["peso_soquete"]),
                "cbr_espessura_disco": str(cbr_equipment["espessura_disco"]),
                "cbr_altura_cilindro": str(cbr_equipment["altura_cilindro"]),
                "cbr_constante_prensa": str(cbr_equipment["constante_prensa"]),
            },
        )
        (root / "xl/sharedStrings.xml").write_text(shared, encoding="utf-8")

        s1 = (root / "xl/worksheets/sheet1.xml").read_text(encoding="utf-8")
        s2 = (root / "xl/worksheets/sheet2.xml").read_text(encoding="utf-8")
        for cell, shared_index in {
            "B4": admin["interessado"],
            "F4": admin["obra"],
            "K4": admin["proctor"],
            "M4": admin["registro"],
            "B5": admin["local"],
            "K6": admin["profundidade"],
            "B8": admin["procedencia"],
            "F8": admin["cidade"],
            "J8": admin["responsavel"],
            "G10": admin["capsule_h"],
            "F23": admin["point_1"],
            "F24": admin["point_2"],
            "F25": admin["point_3"],
            "F26": admin["point_4"],
            "F27": admin["point_5"],
        }.items():
            s1 = set_shared_cell(s1, cell, shared_index)
        s1 = set_cell(s1, "M6", data_ensaio, "n" if isinstance(data_ensaio, int) else None)
        if observacoes:
            s1 = set_shared_cell(s1, "B58", admin["observacoes"])
        for cell, shared_index in {"O11": admin["capsule_h"], "P11": admin["capsule_m"]}.items():
            s2 = set_shared_cell(s2, cell, shared_index)
        for cell, shared_index in {
            "B3": admin["interessado_label"],
            "F3": admin["obra_label"],
            "B4": admin["interessado"],
            "F4": admin["obra"],
            "L4": admin["proctor"],
            "O4": admin["cbr_registro"],
            "B5": admin["blank"],
            "B6": admin["blank"],
            "I6": admin["estaca_value"],
            "M6": admin["profundidade"],
            "B8": admin["procedencia"],
            "H8": admin["cidade"],
            "L8": admin["responsavel"],
            "H11": admin["cbr_molde_numero"],
        }.items():
            s2 = set_shared_cell(s2, cell, shared_index, remove_formula=True)
        s2 = set_cell(s2, "O6", data_ensaio, "n" if isinstance(data_ensaio, int) else None, remove_formula=True)
        for cell, key in {
            "H12": "peso_molde",
            "H13": "volume_molde",
            "H14": "numero_camadas",
            "H15": "golpes_camada",
            "H16": "peso_soquete",
            "H17": "espessura_disco",
            "H18": "altura_cilindro",
            "P22": "constante_prensa",
        }.items():
            s2 = set_mixed_cell(s2, cell, cbr_equipment[key], admin[f"cbr_{key}"])

        for cell, val in {
            "G11": block_field(hygroscopic, "peso_bruto_umido", "peso_bruto_umido_g"),
            "G12": block_field(hygroscopic, "peso_bruto_seco", "peso_bruto_seco_g"),
            "G13": block_field(hygroscopic, "tara_capsula", "peso_capsula", "peso_da_capsula", "tara_da_capsula"),
            "G14": water_weight(hygroscopic),
            "O12": block_field(hygroscopic, "peso_bruto_umido", "peso_bruto_umido_g"),
            "O13": block_field(hygroscopic, "peso_bruto_seco", "peso_bruto_seco_g"),
            "O14": block_field(hygroscopic, "tara_capsula", "peso_capsula", "peso_da_capsula", "tara_da_capsula"),
        }.items():
            if cell.startswith("G"):
                s1 = set_optional_number(s1, cell, val)
            else:
                s2 = set_optional_number(s2, cell, val)

        for index, row in enumerate(range(23, 28)):
            point = points[index] if index < len(points) else {}
            capsule = point_capsule(point)
            gross = point_number(point, "peso_umido_molde_g", "peso_solo_umido_molde_g")
            wet_soil = point_number(point, "peso_solo_umido_g")
            wet_density = point_number(point, "densidade_umida_g_cm3")
            moisture = point_number(point, "umidade_media_percent", "umidade_percent")
            dry_density = point_number(point, "densidade_seca_g_cm3")
            cap_wet = numeric_block_field(capsule, "peso_bruto_umido_g", "peso_bruto_umido")
            cap_dry_gross = numeric_block_field(capsule, "peso_bruto_seco_g", "peso_bruto_seco")
            cap_tare = numeric_block_field(capsule, "tara_capsula_g", "tara_capsula")
            cap_water = cap_wet - cap_dry_gross if cap_wet is not None and cap_dry_gross is not None else None
            cap_dry = cap_dry_gross - cap_tare if cap_dry_gross is not None and cap_tare is not None else None
            for cell, val in {
                f"C{row}": gross,
                f"D{row}": wet_soil,
                f"E{row}": wet_density,
                f"G{row}": cap_wet,
                f"H{row}": cap_dry_gross,
                f"I{row}": cap_tare,
                f"J{row}": cap_water,
                f"K{row}": cap_dry,
                f"L{row}": moisture,
                f"M{row}": moisture,
                f"N{row}": dry_density,
            }.items():
                s1 = set_cell(s1, cell, val, "n", remove_formula=True)
        for index, row in enumerate(range(32, 37)):
            point = points[index] if index < len(points) else {}
            s1 = set_cell(
                s1,
                f"B{row}",
                point_number(point, "umidade_media_percent", "umidade_percent"),
                "n",
                remove_formula=True,
            )
            s1 = set_cell(
                s1,
                f"C{row}",
                point_number(point, "densidade_seca_g_cm3"),
                "n",
                remove_formula=True,
            )
        s1 = set_v(s1, "M46", params["gdmax"])
        s1 = set_v(s1, "M53", params["opt"])

        for cell, val in {
            "P12": block_field(molding_moisture, "peso_bruto_umido", "peso_bruto_umido_g"),
            "P13": block_field(molding_moisture, "peso_bruto_seco", "peso_bruto_seco_g"),
            "P14": block_field(molding_moisture, "tara_capsula", "peso_capsula", "peso_da_capsula", "tara_da_capsula"),
            "F21": params["opt"],
            "M20": value(data, "cbr.peso_solo_umido_passando_peneira_4"),
        }.items():
            s2 = set_optional_number(s2, cell, val)
        for cell, val in {
            "P36": block_field(molding_calc, "peso_solo_umido", "peso_solo_seco", "peso_solo"),
            "P38": block_field(molding_calc, "peso_retido_peneira_4", "peso_retido_peneira_04"),
            "P40": block_field(molding_calc, "peso_passando_peneira_4", "peso_passando_peneira_04"),
            "P42": block_field(molding_calc, "agua_a_juntar", "agua_adicionar"),
        }.items():
            s2 = set_optional_grams(s2, cell, val)
        gross_cp_wet = block_field(molding_check, "peso_bruto_cp_umido", "peso_bruto_corpo_prova_umido")
        cp_wet = block_field(molding_check, "peso_cp_umido", "peso_corpo_prova_umido")
        gross_cp_wet_kg = kg_value(gross_cp_wet)
        cp_wet_kg = kg_value(cp_wet)
        mold_weight_kg = grams_value(cbr_equipment["peso_molde"])
        if mold_weight_kg is not None:
            mold_weight_kg = mold_weight_kg / 1000
        if cp_wet_kg is None and gross_cp_wet_kg is not None and mold_weight_kg is not None:
            cp_wet_kg = gross_cp_wet_kg - mold_weight_kg
        s2 = set_optional_kg(s2, "P45", gross_cp_wet)
        if cp_wet_kg is not None:
            s2 = set_v(s2, "P47", cp_wet_kg)
        s2 = set_optional_number(s2, "P54", block_field(molding_check, "peso_bruto_cp_apos_imersao"))
        s2 = set_optional_number(s2, "P61", block_field(molding_check, "umidade_saturacao"))

        exp = params["exp"]
        readings = cbr_readings(data)
        cbr_values: list[float] = []
        for row in range(27, 33):
            for col in ("F", "G", "J"):
                s2 = set_v(s2, f"{col}{row}", None)
        for index, reading in enumerate(readings[:6]):
            row = reading_target_row(reading, 27 + index)
            cbr_percent = point_number(reading, "cbr_percent", "cbr")
            if cbr_percent is not None:
                cbr_values.append(cbr_percent)
            for cell, val in {
                f"F{row}": point_number(reading, "leitura_extensometro", "leitura"),
                f"G{row}": point_number(reading, "pressao_corrigida_kg_cm2", "pressao_corrigida"),
                f"J{row}": cbr_percent,
            }.items():
                s2 = set_v(s2, cell, val)
        cbr_final = max(cbr_values) if cbr_values else params["cbr"]
        for cell, val in {
            "F34": cbr_final / 100 if cbr_final is not None else None,
            "N27": 0,
            "N29": exp * 0.45,
            "N31": exp * 0.75,
            "N33": exp,
            "P24": exp / 100,
            "P33": exp,
            "J34": exp / 100,
        }.items():
            s2 = set_v(s2, cell, val)

        (root / "xl/worksheets/sheet1.xml").write_text(s1, encoding="utf-8")
        (root / "xl/worksheets/sheet2.xml").write_text(s2, encoding="utf-8")
        update_zip(out, root, parts)

    validate_workbook(out)
    return out


def gran_defaults(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "p10": number_value(data, "granulometria.passante_10", 25.0),
        "p40": number_value(data, "granulometria.passante_40", 19.0),
        "p200": number_value(data, "granulometria.passante_200", 11.0),
        "trb": value(data, "granulometria.classificacao_trb", "A-1-a"),
        "sucs": value(data, "granulometria.classificacao_sucs", "GM"),
    }


def generate_granulometry(data: dict[str, Any], language: str, job_id: int, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"job_{job_id}_granulometria_{language}.xlsx"
    shutil.copy2(template_path("granulometria", language), out)
    params = gran_defaults(data)
    obra = granulometry_text(data, "obra", "OBRA")
    estaca = granulometry_text(data, "estaca", "ESTACA")
    procedencia = granulometry_text(data, "procedencia", obra)
    empresa = granulometry_text(data, "empresa_executora") or text_value(data, "interessado", "")
    camada = granulometry_text(data, "camada")
    lado = granulometry_text(data, "lado")
    profundidade = granulometry_text(data, "profundidade")
    laboratorio = granulometry_text(data, "laboratorio")
    operador = granulometry_text(data, "operador")
    laboratorista = granulometry_text(data, "laboratorista")
    registro = granulometry_text(data, "registro", f"{job_id:02d}")
    data_ensaio = excel_date(granulometry_text(data, "data_ensaio"))

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        parts = ["xl/sharedStrings.xml", "xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml"]
        for part in parts:
            copy_part(out, part, root)
        shared = (root / "xl/sharedStrings.xml").read_text(encoding="utf-8")
        shared, indexes = append_text_indexes(
            shared,
            {
                "obra": obra,
                "procedencia": procedencia,
                "empresa": empresa,
                "camada": camada,
                "estaca": estaca,
                "lado": lado,
                "profundidade": profundidade,
                "laboratorio": laboratorio,
                "operador": operador,
                "laboratorista": laboratorista,
                "registro": registro,
                "trb": str(params["trb"]),
                "sucs": str(params["sucs"]),
            },
        )
        (root / "xl/sharedStrings.xml").write_text(shared, encoding="utf-8")

        s1 = (root / "xl/worksheets/sheet1.xml").read_text(encoding="utf-8")
        s2 = (root / "xl/worksheets/sheet2.xml").read_text(encoding="utf-8")
        for cell, idx in {
            "A27": indexes["obra"],
            "D27": indexes["procedencia"],
            "H27": indexes["empresa"],
            "B29": indexes["camada"],
            "G29": indexes["estaca"],
            "J29": indexes["lado"],
            "L29": indexes["profundidade"],
            "A31": indexes["laboratorio"],
            "C31": indexes["operador"],
            "G31": indexes["laboratorista"],
            "M20": indexes["trb"],
            "M21": indexes["sucs"],
        }.items():
            s1 = set_shared_cell(s1, cell, idx)
        s1 = set_cell(s1, "E31", data_ensaio, "n" if isinstance(data_ensaio, int) else None)
        s1 = set_register_cell(s1, "L31", registro, indexes["registro"])
        for cell, idx in {
            "A22": indexes["obra"],
            "C22": indexes["procedencia"],
            "K22": indexes["empresa"],
            "A24": indexes["camada"],
            "H24": indexes["estaca"],
            "K24": indexes["lado"],
            "L24": indexes["profundidade"],
            "A26": indexes["laboratorio"],
            "B26": indexes["operador"],
            "J26": indexes["laboratorista"],
        }.items():
            s2 = set_shared_cell(s2, cell, idx)
        s2 = set_cell(s2, "F26", data_ensaio, "n" if isinstance(data_ensaio, int) else None)
        s2 = set_register_cell(s2, "L26", registro, indexes["registro"])

        p10 = params["p10"]
        p40 = params["p40"]
        p200 = params["p200"]
        p38 = min(p10 + 35.0, 75.0)
        p4 = min(p10 + 21.0, p38 - 1.0)
        total = 1500.0
        e19 = total * p38 / 100
        e20 = total * p4 / 100
        e21 = total * p10 / 100
        partial = 100.0
        e22 = partial * p40 / p10 if p10 else 0
        e23 = partial * p200 / p10 if p10 else 0
        h = 1.0
        for cell, val in {
            "D3": 1,
            "D4": 61.5,
            "D5": 61.0,
            "D6": 11.0,
            "D7": 0.5,
            "D8": 50,
            "D9": h,
            "D11": h,
            "I3": 2,
            "I4": 1550,
            "I5": 1500,
            "K5": partial,
            "I6": 1500 - e21,
            "I7": e21 * (1 + h / 100),
            "I8": e21,
            "I9": e21 * h / 100,
            "J9": total,
            "K9": h,
            "L9": 100 - h,
            "D19": 300,
            "E19": e19,
            "F19": p38,
            "D20": e19 - e20,
            "E20": e20,
            "F20": p4,
            "D21": e20 - e21,
            "E21": e21,
            "F21": p10,
            "D22": partial - e22,
            "E22": e22,
            "F22": p40,
            "D23": e22 - e23,
            "E23": e23,
            "F23": p200,
            "M15": 100 / total,
            "M18": p10 / 100,
            "M22": 0,
        }.items():
            s1 = set_v(s1, cell, val)

        (root / "xl/worksheets/sheet1.xml").write_text(s1, encoding="utf-8")
        (root / "xl/worksheets/sheet2.xml").write_text(s2, encoding="utf-8")
        update_zip(out, root, parts)

    validate_workbook(out)
    return out


def generate_workbooks(job_id: int, data: dict[str, Any]) -> list[dict[str, str]]:
    language = data.get("language") or "pt"
    test_type = data.get("test_type") or "ambos"
    output_dir = settings.MEDIA_ROOT / "generated" / f"job_{job_id}"
    generated: list[Path] = []
    if test_type in {"compactacao_cbr", "ambos"}:
        generated.append(generate_compaction_cbr(data, language, job_id, output_dir))
    if test_type in {"granulometria", "ambos"}:
        generated.append(generate_granulometry(data, language, job_id, output_dir))
    return [{"name": path.name, "path": str(path)} for path in generated]
