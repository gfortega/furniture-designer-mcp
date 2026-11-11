"""Editable supplier export layouts; the built-in generic layout is immutable."""

import json
from pathlib import Path

from .supplier_profiles import _path

DEFAULT_TEMPLATE_ID = "generica"
DEFAULT_COLUMNS = ["Estado", "Piezas", "Cantidad", "Largo mm", "Ancho mm",
                   "Espesor mm", "Material", "Veta", "Tapacantos"]
DEFAULT_TEMPLATE = {"name": "Genérica provisional", "columns": DEFAULT_COLUMNS}


def validate_template(template: dict) -> dict:
    if not isinstance(template, dict) or not isinstance(template.get("name"), str) or not template["name"].strip():
        raise ValueError("La plantilla necesita un nombre")
    cols = template.get("columns")
    if (not isinstance(cols, list) or not cols or
            any(not isinstance(c, str) or c not in DEFAULT_COLUMNS for c in cols) or
            len(set(cols)) != len(cols)):
        raise ValueError("Las columnas deben ser nombres válidos y no repetidos")
    return {"name": template["name"], "columns": list(cols)}


def save_template(directory: str, template_id: str, template: dict) -> Path:
    path = _path(directory, template_id)
    if template_id == DEFAULT_TEMPLATE_ID:
        raise ValueError("La plantilla genérica integrada no se puede reemplazar")
    data = validate_template(template)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_template(directory: str, template_id: str = DEFAULT_TEMPLATE_ID) -> dict:
    if template_id == DEFAULT_TEMPLATE_ID:
        return {"name": DEFAULT_TEMPLATE["name"], "columns": list(DEFAULT_COLUMNS)}
    return validate_template(json.loads(_path(directory, template_id).read_text(encoding="utf-8")))


def list_templates(directory: str) -> list[dict]:
    result = [{"id": DEFAULT_TEMPLATE_ID, "template": load_template(directory), "builtin": True}]
    for path in sorted(Path(directory).glob("*.json")):
        if path.stem == DEFAULT_TEMPLATE_ID:
            continue
        try:
            result.append({"id": path.stem, "template": load_template(directory, path.stem), "builtin": False})
        except (ValueError, OSError):
            result.append({"id": path.stem, "error": "Plantilla inválida o inaccesible"})
    return result
