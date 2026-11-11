"""Generate a draft supplier workbook and a matching cutting diagram."""

import html
import math
from pathlib import Path

from .supplier_export import export_cutlist_xlsx
from .supplier_profiles import load_profile, optimize_profile
from .supplier_templates import load_template


def build_supplier_package(spec: dict, destination: str, profile_id: str = "generico",
                           template_id: str = "generica", profile_directory: str = "./supplier_profiles",
                           template_directory: str = "./supplier_templates") -> dict:
    """Export one material/thickness. Measurements are cuts, not finished dimensions."""
    profile = load_profile(profile_directory, profile_id)
    template = load_template(template_directory, template_id)
    source = spec.get("parts")
    if not isinstance(source, list) or not source:
        raise ValueError("Se necesita al menos una pieza")
    materials, ids, parts = set(), set(), []
    for p in source:
        pid = p.get("id")
        if not isinstance(pid, str) or not pid or pid in ids:
            raise ValueError("Los identificadores de pieza deben ser únicos y no vacíos")
        ids.add(pid)
        for field in ("width_mm", "height_mm", "thickness_mm"):
            value = p.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"Medida inválida en {pid}: {field}")
        if p.get("grain") not in (None, "length", "width", "none"):
            raise ValueError(f"Dirección de veta inválida en {pid}")
        if p["role"] in ("back", "drawer_bottom"):
            default_material = "mdf_3"
        else:
            default_material = spec.get("material", "melamine_16")
        materials.add(p.get("material", default_material))
        parts.append({"id": pid, "width": p["width_mm"], "height": p["height_mm"],
                      "thickness": p["thickness_mm"], **({"grain": p["grain"]} if p.get("grain") else {})})
    if len(materials) != 1:
        raise ValueError("Calcule cada material por separado; el paquete admite un solo material")
    result = optimize_profile(parts, profile)
    if "error" in result:
        raise ValueError(result["error"])
    if any("grano relajado" in w.lower() for w in result["warnings"]):
        raise ValueError("La veta de una pieza no cabe en la placa sin rotación; revise el perfil")
    result["warnings"].append("Las dimensiones son de corte; confirmar tapacantos antes de fabricar.")
    workbook = Path(destination)
    if workbook.suffix.lower() != ".xlsx":
        raise ValueError("El archivo de destino debe terminar en .xlsx")
    diagram = workbook.with_suffix(".svg")
    export_cutlist_xlsx(spec, str(workbook), template=template, cut_data=result)
    diagram.write_text(_svg(result), encoding="utf-8")
    return {"workbook": str(workbook), "diagram": str(diagram), "result": result,
            "template": template, "status": "BORRADOR - REVISAR"}


def _svg(result: dict) -> str:
    width = result["sheet_size_mm"]["width"]
    height = result["sheet_size_mm"]["height"]
    sheets = result["sheets"]
    gap = 180
    size = max(width, height)
    font = max(20, min(55, size / 55))
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {(height + gap) * len(sheets)}">']
    svg.append('<style>text{font-family:sans-serif;fill:#202020}</style>')
    for index, sheet in enumerate(sheets):
        y_offset = index * (height + gap) + gap
        svg.append(f'<text x="10" y="{y_offset - 35}" font-size="{font}">BORRADOR — Placa {sheet["sheet_number"]} ({width} × {height} mm)</text>')
        svg.append(f'<rect x="0" y="{y_offset}" width="{width}" height="{height}" fill="#eee" stroke="#222" stroke-width="5"/>')
        for p in sheet["pieces"]:
            x, y, w, h = p["x"], p["y"] + y_offset, p["width"], p["height"]
            label = html.escape(str(p["id"]))
            svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#b8d8e5" stroke="#333" stroke-width="3"/>')
            svg.append(f'<text x="{x + w/2}" y="{y + h/2}" text-anchor="middle" font-size="{font}">{label}</text>')
    svg.append('</svg>')
    return "".join(svg)
