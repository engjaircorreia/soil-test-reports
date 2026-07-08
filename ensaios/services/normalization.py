from __future__ import annotations

import re
from copy import deepcopy
from datetime import date, datetime
from typing import Any


EMPTY_MARKERS = {
    "",
    "-",
    "--",
    "null",
    "none",
    "n/a",
    "na",
    "ilegivel",
    "ilegível",
    "nao identificado",
    "não identificado",
    "nao informado",
    "não informado",
}

TEXT_MARKERS = {"NL", "NP"}

DATE_KEYS = {"data_ensaio"}
IDENTIFIER_KEY_PARTS = {
    "capsula",
    "molde_numero",
    "registro",
    "peneira",
    "estaca",
    "lado",
    "camada",
}
NUMERIC_KEY_PARTS = {
    "peso",
    "volume",
    "umidade",
    "densidade",
    "percent",
    "percentual",
    "altura",
    "constante",
    "golpes",
    "camadas",
    "leitura",
    "pressao",
    "abertura",
}
DENSITY_KEY_PARTS = {"densidade"}


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in EMPTY_MARKERS
    return False


def normalize_text_marker(value: str) -> str | None:
    text = value.strip()
    upper = text.upper()
    if upper in TEXT_MARKERS:
        return upper
    if text.lower() in EMPTY_MARKERS:
        return None
    return None


def normalize_number(value: Any, context: str | None = None) -> float | str | None:
    if is_empty(value):
        return None
    if isinstance(value, (int, float)):
        numeric = float(value)
    elif isinstance(value, str):
        marker = normalize_text_marker(value)
        if marker is not None:
            return marker
        text = value.strip()
        text = text.replace("\u00a0", " ")
        text = text.replace(",", ".")
        if re.search(r"\b\d+\s*/\s*\d+\b", text) and not re.search(r"\d+\.\d+", text):
            return value
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            return None
        numeric = float(match.group(0))
    else:
        return None

    if context == "density" and abs(numeric) > 100:
        numeric = numeric / 1000
    return numeric


def normalize_date(value: Any) -> str | None:
    if is_empty(value):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def should_keep_as_text(key: str) -> bool:
    return any(part in key for part in IDENTIFIER_KEY_PARTS)


def should_normalize_as_number(key: str) -> bool:
    return any(part in key for part in NUMERIC_KEY_PARTS)


def numeric_context_for_key(key: str) -> str | None:
    if any(part in key for part in DENSITY_KEY_PARTS):
        return "density"
    return None


def normalize_scalar(key: str, value: Any) -> Any:
    if is_empty(value):
        return None
    if key in DATE_KEYS or key.endswith("_data") or "data" in key:
        normalized_date = normalize_date(value)
        return normalized_date if normalized_date is not None else value
    if isinstance(value, str):
        marker = normalize_text_marker(value)
        if marker is not None:
            return marker
    if should_keep_as_text(key):
        return value
    if should_normalize_as_number(key):
        normalized = normalize_number(value, context=numeric_context_for_key(key))
        return normalized if normalized is not None else value
    return value


def normalize_object(value: Any, key: str = "") -> Any:
    if isinstance(value, dict):
        return {item_key: normalize_object(item_value, item_key) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [normalize_object(item, key) for item in value]
    return normalize_scalar(key, value)


def find_normalization_issues(data: Any, path: str = "") -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            child_path = f"{path}.{key}" if path else key
            issues.extend(find_normalization_issues(value, child_path))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            issues.extend(find_normalization_issues(value, f"{path}[{index}]"))
    return issues


def normalize_extraction(raw: dict[str, Any] | None) -> tuple[dict[str, Any], list[dict[str, str]]]:
    normalized = normalize_object(deepcopy(raw or {}))
    return normalized, find_normalization_issues(normalized)
