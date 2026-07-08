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

PT_COMPACT = TEMPLATES / "compactacao_cbr_modelo_limpo.xlsx"
PT_GRAN = TEMPLATES / "granulometria_modelo_limpo.xlsx"

EN_COMPACT = TEMPLATES / "compaction_cbr_clean_template_en.xlsx"
EN_GRAN = TEMPLATES / "granulometry_clean_template_en.xlsx"


COMPACT_TRANSLATIONS = {
    0: "WET SOIL DENSITY",
    4: "CAPSULE No.",
    5: "MOLD VOLUME - (cm3)",
    6: "CAPSULE TARE - (g)",
    7: "MOISTURE - (%)",
    8: "MOISTURE / AVERAGE",
    10: "MOISTURE",
    11: "DATE:",
    12: "LOCATION: BOREHOLE / STATION",
    13: "Least Squares Method:",
    14: "Table",
    38: "4th Degree Polynomial:",
    44: "Derivative: P'(x)",
    46: "Function Root:",
    47: "Bisection Method",
    48: "Initial Value",
    54: "Root:",
    57: "Optimum Moisture",
    59: "Maximum Density",
    65: "COMPACTION ENERGY / EQUIPMENT DATA",
    71: "HYGROSCOPIC MOISTURE",
    72: "NOTES:",
    74: "SPECIMEN MOLDING",
    75: "EQUIPMENT DATA",
    76: "MOISTURES",
    77: "MOLDING",
    78: "Mold Weight",
    79: "Wet Gross Weight",
    80: "Mold Volume",
    81: "Dry Gross Weight",
    82: "Number of Layers",
    83: "Capsule Weight",
    84: "Blows/Layer",
    85: "Water Weight",
    86: "Rammer Weight",
    87: "Dry Soil Weight",
    88: "Spacer Disk Thickness",
    89: "Moisture (%)",
    90: "Cylinder Height",
    91: "Average Moisture (%)",
    92: "COMPACTION DATA",
    93: "WATER TO ADD CALCULATION",
    94: "Optimum Moisture - %",
    95: "Hygroscopic Moisture - %",
    96: "Moisture Difference - %",
    97: "PENETRATION TEST",
    98: "SWELL",
    99: "Time min.",
    100: "Penetration",
    101: "Extensometer Reading",
    102: "Pressure - kg/cm2",
    103: "Dates",
    104: "Swell %",
    105: "Calc.",
    106: "Corrected",
    107: "Standard",
    108: "Day",
    109: "Hour",
    110: "30 sec.",
    111: "SWELL (%) =",
    112: "SPECIMEN MOLDING CALCULATIONS",
    113: "Wet soil weight - Ph (g) =",
    114: "Weight retained on sieve No. 04 - Pr 4 (g) =",
    115: "MOLDING CHECK",
    116: "MOISTURE AFTER IMMERSION",
    117: "Specimen gross weight after immersion (Pbim):",
    118: "Specimen weight after immersion (Pim=Pbim-T):",
    119: "Specimen moisture after immersion (him) - %",
    120: "DEGREE OF SATURATION",
    121: "Saturation Moisture (Hsat %) =",
    122: "Degree of Saturation (%) =",
    123: "Capsule - No.",
    124: "Wet specimen gross weight (g):",
    125: "Wet specimen weight (g):",
    126: "Wet specimen density (kg/m3):",
    127: "Dry specimen density (kg/m3):",
    128: "START:",
    129: "Press Constant",
    130: "TEST TIME",
    131: "BLOWS PER LAYER (unit)",
    132: "NUMBER OF LAYERS (unit)",
    133: "OPTIMUM MOISTURE (%)",
    171: "PROCTOR:",
    173: "RECORD No.",
    174: "Calc. Volume (cm3)",
    175: "Maximum Density - kg/m3",
    176: "Dry Soil Weight Passing Sieve No. 04",
    178: "Gravel Weight Retained on Sieve No. 04",
    179: "MAXIMUM DENSITY (g/cm3)",
    185: "CLIENT:",
    186: "SOURCE:",
    187: "CITY:",
    188: "PROJECT:",
    189: "COMPACTION TEST",
    190: "CALIFORNIA BEARING RATIO DETERMINATION C.B.R.",
    191: "RESPONSIBLE:",
    192: "Wet Soil Weight Passing Sieve No. 04",
    193: "Water to Add:",
    195: "Defl. Reading (mm)",
    196: "Difference (mm)",
    197: "Weight passing sieve No. 04 - Os 4 (g) =",
    198: "Dry weight passing sieve No. 04 - (g) =",
    199: "DEPTH (cm)",
    200: "Mold - No.",
    201: "WET GROSS WEIGHT - (g)",
    202: "DRY GROSS WEIGHT - (g)",
    203: "WATER WEIGHT - (g)",
    204: "DRY SOIL WEIGHT - (g)",
    205: "COMPACTION ENERGY (kg.cm / cm3)",
    206: "MOLD No.",
    207: "WET GROSS WEIGHT",
    208: "WET SOIL WEIGHT",
    209: "RAMMER DROP HEIGHT - (cm):",
    210: "MOLD WEIGHT - (g)",
    211: "RAMMER WEIGHT - (g)",
    212: "DRY GROSS WEIGHT",
    213: "WET GROSS WEIGHT",
    214: "CAPSULE WEIGHT",
    215: "POINT No.",
    216: "WATER WEIGHT",
    217: "CAPSULES No.",
    218: "DRY SOIL WEIGHT",
    219: "DRY SOIL DENSITY",
    220: "MOISTURE DETERMINATION",
    221: "SPACER DISK THICKNESS - (in)",
    222: "AVERAGE MOISTURE - (%)",
    223: "RECORD No.:",
    224: "DEPTH (cm):",
    225: "NOTES:",
    235: "LOCATION: BOREHOLE / STATION (E - X - D) - X",
    236: "INTERMEDIATE",
    238: "PROJECT: PITIMBU",
    239: "ROAD NAME",
    246: "HYGROSCOPIC",
}


GRAN_TRANSLATIONS = {
    0: "MOISTURE",
    2: "SAMPLE",
    4: "Partial",
    5: "Capsule - No.",
    6: "Wet Gross Weight",
    7: "Dry Gross Weight",
    8: "Wet Weight",
    9: "Capsule Weight",
    10: "Weight Retained on Sieve No. 10",
    11: "Water Weight",
    12: "Wet Weight Passing Sieve No. 10",
    13: "Dry Soil Weight",
    14: "Dry Weight Passing Sieve No. 10",
    15: "Moisture",
    16: "Dry Sample Weight",
    17: "Average Moisture",
    18: "Sieving",
    19: "Total Sample",
    20: "Sieves",
    21: "Weight",
    22: "AASHTO RANGE",
    23: "CONSTANTS",
    24: "Retained",
    25: "Passing",
    26: "Minimum",
    27: "Maximum",
    28: "in",
    30: "Accumulated",
    31: "Total Sample",
    38: 'Class.:"T.R.B"',
    40: 'Class.:"S.U.C.S"',
    42: "Partial Sample",
    43: "Group Index:",
    44: "Notes:",
    45: "Silt + Clay",
    46: "Sand",
    47: "Gravel",
    48: "PROJECT:",
    49: "SOURCE:",
    50: "EXECUTING COMPANY:",
    51: "LAYER:",
    52: "LOCATION / BOREHOLE / STATION:",
    53: "SIDE D-X-E",
    54: "DEPTH (m)",
    55: "APPROVED:",
    56: "EMBANKMENT BODY STUDY",
    58: "LABORATORY:",
    59: "OPERATOR:",
    60: "DATE:",
    61: "LAB TECHNICIAN:",
    62: "RECORD:",
    63: "TEAM",
    64: "CONSISTENCY TEST ON SOIL SAMPLE",
    65: "LIQUID LIMIT - DNER-ME 122/94",
    66: "Capsule",
    68: "Blows",
    70: "N/L",
    71: "Calculator:",
    72: "LL=",
    73: "NL",
    74: "PLASTIC LIMIT - DNER-ME 82/94",
    75: "PL =",
    76: "NP",
    77: "N/P",
    78: "P.I.=",
    79: "Notes:",
    80: "TEST VALIDITY:",
    82: "GRAIN SIZE CHARACTERIZATION TESTS ON SOIL SAMPLE",
    83: '100\n90\n80\n70\n60\n50\n40\n30\n20\n10\n0\n0.01                                          0.1                        No. 200                              No. 40                  No.10             No. 4          3/8"                  1"    1½"    2"    in. 100                  \n  ',
    87: "Liquid Limit",
    90: "PROJECT; ROAD NAME",
    92: "ENG. JAIR ADHONAI CORREIA DOS SANTOS                                                                                                                                           ",
    93: "JAIR ADHONAI CORREIA DOS SANTOS                                                                                                                                                                                         ",
}


def replace_shared_string(xml: str, index: int, text: str) -> str:
    spans = [match.span() for match in re.finditer(r"<si>.*?</si>", xml, re.S)]
    if index >= len(spans):
        raise RuntimeError(f"Shared string {index} was not found")
    start, end = spans[index]
    return xml[:start] + f"<si><t>{escape(text)}</t></si>" + xml[end:]


def translate_workbook(source: Path, target: Path, translations: dict[int, str]) -> None:
    shutil.copy2(source, target)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        part = "xl/sharedStrings.xml"
        with zipfile.ZipFile(target) as workbook:
            path = temp_root / part
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(workbook.read(part))

        xml = path.read_text(encoding="utf-8")
        for index, text in sorted(translations.items()):
            xml = replace_shared_string(xml, index, text)
        path.write_text(xml, encoding="utf-8")

        subprocess.run(["zip", "-q", str(target), part], cwd=temp_root, check=True)


def main() -> None:
    translate_workbook(PT_COMPACT, EN_COMPACT, COMPACT_TRANSLATIONS)
    translate_workbook(PT_GRAN, EN_GRAN, GRAN_TRANSLATIONS)
    print(EN_COMPACT.relative_to(ROOT))
    print(EN_GRAN.relative_to(ROOT))


if __name__ == "__main__":
    main()
