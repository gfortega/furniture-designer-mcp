"""Supplier settings for repeatable cutting calculations, in millimetres."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path


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
    return dict(profile)


def _path(directory: str, profile_id: str) -> Path:
    if not isinstance(profile_id, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", profile_id):
        raise ValueError("profile_id must contain only letters, numbers, hyphens or underscores")
    return Path(directory) / f"{profile_id}.json"


def save_profile(directory: str, profile_id: str, profile: dict) -> Path:
    path = _path(directory, profile_id)
    validated = validate_profile(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(validated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_profile(directory: str, profile_id: str) -> dict:
    return validate_profile(json.loads(_path(directory, profile_id).read_text(encoding="utf-8")))
