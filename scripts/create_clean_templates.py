from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"

SOURCE_COMPACT = ROOT / "BEIRA_MAR_ORGANIZADO/00_modelos/modelo_joao_pessoa_compactacao_cbr.xlsx"
SOURCE_GRAN = ROOT / "BEIRA_MAR_ORGANIZADO/00_modelos/modelo_joao_pessoa_granulometria.xlsx"

OUT_COMPACT = TEMPLATES / "compactacao_cbr_modelo_limpo.xlsx"
OUT_GRAN = TEMPLATES / "granulometria_modelo_limpo.xlsx"

BLANK_SHARED_COMPACT = 180
BLANK_SHARED_GRAN = 91
DASH_SHARED_GRAN = 57


COMPACT_STRING_CELLS = {
    "xl/worksheets/sheet1.xml": [
        "B4",
        "F4",
        "K4",
        "M4",
        "B5",
        "B8",
        "F8",
        "J8",
        "G10",
        "F23",
        "F24",
        "F25",
        "F26",
        "F27",
    ],
    "xl/worksheets/sheet2.xml": ["O11", "P11"],
}

COMPACT_NUMERIC_CELLS = {
    "xl/worksheets/sheet1.xml": [
        "M6",
        "G11",
        "G12",
        "G13",
        "G14",
        "C23",
        "D23",
        "I23",
        "J23",
        "K23",
        "C24",
        "D24",
        "I24",
        "J24",
        "K24",
        "C25",
        "D25",
        "G25",
        "H25",
        "I25",
        "J25",
        "K25",
        "L25",
        "M25",
        "N25",
        "C26",
        "D26",
        "G26",
        "H26",
        "I26",
        "J26",
        "K26",
        "L26",
        "M26",
        "N26",
        "C27",
        "D27",
        "G27",
        "H27",
        "I27",
        "J27",
        "K27",
        "L27",
        "M27",
        "N27",
        "M46",
        "M53",
        "M56",
    ],
    "xl/worksheets/sheet2.xml": [
        "O12",
        "O13",
        "O14",
        "P12",
        "P13",
        "P14",
        "F21",
        "M20",
        "F27",
        "G27",
        "F28",
        "G28",
        "F29",
        "G29",
        "J29",
        "N29",
        "F30",
        "G30",
        "J30",
        "F31",
        "G31",
        "J31",
        "N31",
        "F32",
        "G32",
        "J32",
        "N33",
        "P33",
        "P36",
        "P38",
        "P40",
        "P42",
        "P45",
        "P47",
    ],
}

GRAN_STRING_CELLS_BLANK = {
    "xl/worksheets/sheet1.xml": ["A27", "H27", "B29", "G29", "J29", "L29", "A31", "C31", "G31", "M20", "M21"],
    "xl/worksheets/sheet2.xml": ["A22", "C22", "K22", "H24", "K24", "L24", "A26", "B26", "J26", "M9", "M12", "M14"],
}

GRAN_NUMERIC_CELLS = {
    "xl/worksheets/sheet1.xml": [
        "D3",
        "D4",
        "D5",
        "D6",
        "D7",
        "D8",
        "D9",
        "D11",
        "I3",
        "I4",
        "I5",
        "K5",
        "I6",
        "I7",
        "I8",
        "I9",
        "J9",
        "K9",
        "L9",
        "D19",
        "E19",
        "F19",
        "D20",
        "E20",
        "F20",
        "D21",
        "E21",
        "F21",
        "D22",
        "E22",
        "F22",
        "D23",
        "E23",
        "F23",
        "M15",
        "M18",
        "M22",
        "E31",
        "L31",
    ],
    "xl/worksheets/sheet2.xml": ["L6", "F26", "L26"],
}


def read_part(xlsx: Path, part: str, temp_root: Path) -> Path:
    with zipfile.ZipFile(xlsx) as zf:
        path = temp_root / part
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(zf.read(part))
        return path


def update_parts(xlsx: Path, temp_root: Path, parts: list[str]) -> None:
    subprocess.run(["zip", "-q", str(xlsx), *parts], cwd=temp_root, check=True)


def set_shared_index(xml: str, cell: str, shared_index: int) -> str:
    return set_cell_value(xml, cell, shared_index)


def clear_cell_value(xml: str, cell: str) -> str:
    pattern = re.compile(
        r'(<c\b[^>]*\br="' + re.escape(cell) + r'"[^>]*>.*?<v>)(.*?)(</v>.*?</c>)',
        re.S,
    )
    xml, count = pattern.subn(lambda match: match.group(1) + "" + match.group(3), xml, count=1)
    if count != 1:
        raise RuntimeError(f"Cell {cell} was not found")
    return xml


def cell_has_formula(xml: str, cell: str) -> bool:
    pattern = re.compile(r'<c\b[^>]*\br="' + re.escape(cell) + r'"[^>]*>.*?</c>', re.S)
    match = pattern.search(xml)
    return bool(match and "<f" in match.group(0))


def set_cell_value(xml: str, cell: str, value: int | float | str) -> str:
    pattern = re.compile(
        r'(<c\b[^>]*\br="' + re.escape(cell) + r'"[^>]*>.*?<v>)(.*?)(</v>.*?</c>)',
        re.S,
    )
    xml, count = pattern.subn(lambda match: match.group(1) + escape(str(value)) + match.group(3), xml, count=1)
    if count != 1:
        raise RuntimeError(f"Cell {cell} was not found")
    return xml


def replace_shared_string(xml: str, index: int, text: str) -> str:
    spans = [match.span() for match in re.finditer(r"<si>.*?</si>", xml, re.S)]
    if index >= len(spans):
        raise RuntimeError(f"Shared string {index} was not found")
    start, end = spans[index]
    return xml[:start] + f"<si><t>{escape(text)}</t></si>" + xml[end:]


def enable_recalculation(workbook_xml: str) -> str:
    if "<calcPr " not in workbook_xml:
        return workbook_xml.replace("</workbook>", '<calcPr calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"/></workbook>')

    def patch(match: re.Match[str]) -> str:
        tag = match.group(0)
        tag = re.sub(r'\sfullCalcOnLoad="[^"]*"', "", tag)
        tag = re.sub(r'\sforceFullCalc="[^"]*"', "", tag)
        tag = re.sub(r'\scalcMode="[^"]*"', "", tag)
        return tag[:-2] + ' calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"/>'

    return re.sub(r"<calcPr\b[^>]*/>", patch, workbook_xml, count=1)


def clear_formula_caches(xml: str) -> str:
    return re.sub(r"(<c\b[^>]*>.*?<f\b[^>]*>.*?</f>.*?<v>)(.*?)(</v>.*?</c>)", r"\1\3", xml, flags=re.S)


def clean_compact_template() -> None:
    shutil.copy2(SOURCE_COMPACT, OUT_COMPACT)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        parts = ["xl/workbook.xml", "xl/sharedStrings.xml", "xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml", "xl/worksheets/sheet3.xml"]
        for part in parts:
            read_part(OUT_COMPACT, part, temp_root)

        workbook = (temp_root / "xl/workbook.xml").read_text(encoding="utf-8")
        (temp_root / "xl/workbook.xml").write_text(enable_recalculation(workbook), encoding="utf-8")

        for part, cells in COMPACT_STRING_CELLS.items():
            xml = (temp_root / part).read_text(encoding="utf-8")
            for cell in cells:
                xml = set_shared_index(xml, cell, BLANK_SHARED_COMPACT)
            (temp_root / part).write_text(xml, encoding="utf-8")

        for part, cells in COMPACT_NUMERIC_CELLS.items():
            xml = (temp_root / part).read_text(encoding="utf-8")
            for cell in cells:
                if cell_has_formula(xml, cell):
                    continue
                xml = clear_cell_value(xml, cell)
            (temp_root / part).write_text(xml, encoding="utf-8")

        for part in ["xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml", "xl/worksheets/sheet3.xml"]:
            xml = (temp_root / part).read_text(encoding="utf-8")
            (temp_root / part).write_text(clear_formula_caches(xml), encoding="utf-8")

        update_parts(OUT_COMPACT, temp_root, parts)


def clean_granulometry_template() -> None:
    shutil.copy2(SOURCE_GRAN, OUT_GRAN)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        parts = ["xl/workbook.xml", "xl/sharedStrings.xml", "xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml"]
        for part in parts:
            read_part(OUT_GRAN, part, temp_root)

        workbook = (temp_root / "xl/workbook.xml").read_text(encoding="utf-8")
        (temp_root / "xl/workbook.xml").write_text(enable_recalculation(workbook), encoding="utf-8")

        shared = (temp_root / "xl/sharedStrings.xml").read_text(encoding="utf-8")
        shared = replace_shared_string(shared, BLANK_SHARED_GRAN, "")
        (temp_root / "xl/sharedStrings.xml").write_text(shared, encoding="utf-8")

        for part, cells in GRAN_STRING_CELLS_BLANK.items():
            xml = (temp_root / part).read_text(encoding="utf-8")
            for cell in cells:
                xml = set_shared_index(xml, cell, BLANK_SHARED_GRAN)
            (temp_root / part).write_text(xml, encoding="utf-8")

        for part, cells in GRAN_NUMERIC_CELLS.items():
            xml = (temp_root / part).read_text(encoding="utf-8")
            for cell in cells:
                xml = clear_cell_value(xml, cell)
            (temp_root / part).write_text(xml, encoding="utf-8")

        update_parts(OUT_GRAN, temp_root, parts)


def main() -> None:
    TEMPLATES.mkdir(exist_ok=True)
    clean_compact_template()
    clean_granulometry_template()
    print(OUT_COMPACT.relative_to(ROOT))
    print(OUT_GRAN.relative_to(ROOT))


if __name__ == "__main__":
    main()
