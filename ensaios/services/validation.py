from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from openpyxl import load_workbook


MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
VALID_EXCEL_ERRORS = {
    "#NULL!",
    "#DIV/0!",
    "#VALUE!",
    "#REF!",
    "#NAME?",
    "#NUM!",
    "#N/A",
    "#GETTING_DATA",
}


def shared_string_count(workbook: zipfile.ZipFile) -> int:
    try:
        root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    except KeyError:
        return 0
    return len(root.findall(f"{MAIN_NS}si"))


def validate_cell_types(workbook: zipfile.ZipFile) -> None:
    shared_count = shared_string_count(workbook)
    for name in workbook.namelist():
        if not name.startswith("xl/worksheets/") or not name.endswith(".xml"):
            continue
        root = ET.fromstring(workbook.read(name))
        for cell in root.iter(f"{MAIN_NS}c"):
            cell_type = cell.attrib.get("t")
            values = cell.findall(f"{MAIN_NS}v")
            address = cell.attrib.get("r", "?")
            if len(values) > 1:
                raise RuntimeError(f"Célula com mais de um valor em {name}!{address}")
            value = values[0] if values else None
            text = "" if value is None or value.text is None else value.text

            if cell_type == "s" and text:
                if not text.isdigit() or int(text) >= shared_count:
                    raise RuntimeError(f"Referência inválida de texto compartilhado em {name}!{address}: {text}")
            elif cell_type == "e" and text and text not in VALID_EXCEL_ERRORS:
                raise RuntimeError(f"Valor inválido para célula de erro em {name}!{address}: {text}")
            elif cell_type in {"n", None} and text:
                try:
                    float(text)
                except ValueError as exc:
                    raise RuntimeError(f"Valor numérico inválido em {name}!{address}: {text}") from exc


def validate_workbook(path: str | Path) -> None:
    path = Path(path)
    with zipfile.ZipFile(path) as workbook:
        bad_file = workbook.testzip()
        if bad_file:
            raise RuntimeError(f"Arquivo interno corrompido: {bad_file}")
        for name in workbook.namelist():
            if name.endswith(".xml") or name.endswith(".rels"):
                ET.fromstring(workbook.read(name))
        validate_cell_types(workbook)
    load_workbook(path, data_only=False, read_only=False, keep_links=True)
