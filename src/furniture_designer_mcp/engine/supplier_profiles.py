"""Supplier settings for repeatable cutting calculations, in millimetres."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

DEFAULT_PROFILE_ID = "generico"
DEFAULT_PROFILE = {
    "name": "Genérico provisional — confirmar con proveedor",
    "sheet_width_mm": 2600, "sheet_height_mm": 1830,
    "thickness_mm": 18, "blade_kerf_mm": 3.2,
    "trim_margin_mm": 5, "default_edge_banding_mm": 1,
    "grain_direction": "none", "provisional": True,
}


def validate_profile(profile: dict) -> dict:
    """Validate settings without guessing allowances or edgebanding rules."""
    required = ("name", "sheet_width_mm", "sheet_height_mm", "thickness_mm", "blade_kerf_mm", "grain_direction")
    missing = [key for key in required if key not in profile]
    if missing:
        raise ValueError("Missing profile fields: " + ", ".join(missing))
    if not isinstance(profile["name"], str) or not profile["name"].strip():
        raise ValueError("name must be a non-empty string")
    for key in required[1:5]:
        value = profile[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f"{key} must be a finite number")
        if value < 0 or (key != "blade_kerf_mm" and value == 0):
            raise ValueError(f"{key} must be positive (kerf may be zero)")
    if profile["grain_direction"] not in ("auto", "length", "none"):
        raise ValueError("grain_direction must be auto, length or none")
    margin = profile.get("trim_margin_mm", 0)
    if (isinstance(margin, bool) or not isinstance(margin, (int, float)) or
            not math.isfinite(margin) or margin < 0):
        raise ValueError("trim_margin_mm must be a finite non-negative number")
    if 2 * margin >= min(profile["sheet_width_mm"], profile["sheet_height_mm"]):
        raise ValueError("trim_margin_mm leaves no usable sheet area")
    if "default_edge_banding_mm" in profile:
        value = profile["default_edge_banding_mm"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError("default_edge_banding_mm must be a finite positive number")
    return dict(profile)


def optimize_profile(parts: list[dict], profile: dict) -> dict:
    """Optimize a single-material sheet with a uniform edge trim allowance.

    trim_margin_mm is removed from each of the four sheet edges. Piece dimensions
    are supplied as cut dimensions; no edge-banding compensation is inferred.
    """
    from .cut_optimizer import optimize_cuts_best

    profile = validate_profile(profile)
    margin = profile.get("trim_margin_mm", 0)
    width = profile["sheet_width_mm"]
    height = profile["sheet_height_mm"]
    for part in parts:
        thickness = part.get("thickness")
        if thickness is not None and thickness != profile["thickness_mm"]:
            raise ValueError(f"Piece {part.get('id')} does not match profile thickness")
    result = optimize_cuts_best(parts, sheet_width=width - 2 * margin,
                                sheet_height=height - 2 * margin,
                                blade_kerf=profile["blade_kerf_mm"],
                                grain_direction=profile["grain_direction"])
    result["profile"] = profile
    if "error" in result:
        return result
    if profile.get("provisional"):
        result["warnings"].append("Perfil provisional: confirmar placa, espesor, sierra, veta y margen con el proveedor.")
    result["usable_sheet_size_mm"] = result["sheet_size_mm"]
    result["sheet_size_mm"] = {"width": width, "height": height}
    result["trim_margin_mm"] = margin
    result["waste_percentage_usable_area"] = result["waste_percentage"]
    piece_area = sum(p["width"] * p["height"] * p.get("qty", 1) for p in parts)
    total_area = result["sheets_needed"] * width * height
    result["waste_percentage"] = round((1 - piece_area / total_area) * 100, 1) if total_area else 0
    for sheet in result["sheets"]:
        for piece in sheet["pieces"]:
            piece["x"] += margin
            piece["y"] += margin
    if "trim_margin_mm" not in profile:
        result["warnings"].append("Margen de escuadrado no definido; se usó 0 mm para la prueba.")
    if margin:
        result["warnings"].append("El diagrama de texto representa solo el área útil; las coordenadas usan el tablero completo.")
    return result


def _path(directory: str, profile_id: str) -> Path:
    if not isinstance(profile_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", profile_id):
        raise ValueError("profile_id must contain only letters, numbers, hyphens or underscores")
    return Path(directory) / f"{profile_id}.json"


def save_profile(directory: str, profile_id: str, profile: dict) -> Path:
    path = _path(directory, profile_id)
    if profile_id == DEFAULT_PROFILE_ID:
        raise ValueError("El perfil genérico integrado no se puede reemplazar; guarde otro identificador")
    validated = validate_profile(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(validated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_profile(directory: str, profile_id: str) -> dict:
    if profile_id == DEFAULT_PROFILE_ID:
        return dict(DEFAULT_PROFILE)
    return validate_profile(json.loads(_path(directory, profile_id).read_text(encoding="utf-8")))


def list_profiles(directory: str) -> list[dict]:
    result = [{"id": DEFAULT_PROFILE_ID, "profile": dict(DEFAULT_PROFILE), "builtin": True}]
    root = Path(directory)
    for path in sorted(root.glob("*.json")):
        if path.stem == DEFAULT_PROFILE_ID:
            continue
        try:
            result.append({"id": path.stem, "profile": load_profile(directory, path.stem), "builtin": False})
        except (ValueError, OSError):
            result.append({"id": path.stem, "error": "Perfil inválido o inaccesible"})
    return result
