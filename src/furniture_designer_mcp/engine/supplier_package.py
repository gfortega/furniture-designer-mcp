"""Generate a draft supplier workbook and a matching cutting diagram."""

import html
import math
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

from .supplier_export import export_cutlist_xlsx
from .supplier_profiles import load_profile, optimize_profile
from .supplier_templates import load_template


def build_supplier_package(spec: dict, destination: str, profile_id: str = "generico",
                           template_id: str = "generica", profile_directory: str = "./supplier_profiles",
                           template_directory: str = "./supplier_templates",
                           banding_by_part: dict | None = None) -> dict:
    """Export one material/thickness. Spec dimensions are finished dimensions.

    banding_by_part maps piece IDs to edge thicknesses (mm). An empty map for a
    piece confirms no edge banding; an absent ID means its edges are unknown.
    """
    profile = load_profile(profile_directory, profile_id)
    template = load_template(template_directory, template_id)
    cut_spec = deepcopy(spec)
    source = cut_spec.get("parts")
    if not isinstance(source, list) or not source:
        raise ValueError("Se necesita al menos una pieza")
    if banding_by_part is not None and not isinstance(banding_by_part, dict):
        raise ValueError("Los tapacantos deben ser un mapa por identificador de pieza")
    banding = banding_by_part if banding_by_part is not None else {}
    materials, ids, parts, unspecified = set(), set(), [], []
    finished = {}
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
        finished[pid] = {"largo_mm": p["width_mm"], "ancho_mm": p["height_mm"]}
        if pid in banding:
            edges = banding[pid]
            allowed = {"largo_inicio", "largo_fin", "ancho_inicio", "ancho_fin"}
            if not isinstance(edges, dict) or set(edges) - allowed:
                raise ValueError(f"Bordes inválidos en {pid}: use largo_inicio, largo_fin, ancho_inicio, ancho_fin")
            resolved = {}
            for edge, thickness in edges.items():
                if thickness is None:
                    thickness = profile.get("default_edge_banding_mm")
                if (isinstance(thickness, bool) or not isinstance(thickness, (int, float)) or
                        not math.isfinite(thickness) or thickness <= 0):
                    raise ValueError(f"Espesor de tapacanto inválido o no definido en {pid}: {edge}")
                resolved[edge] = thickness
            for field, start, end in (("width_mm", "largo_inicio", "largo_fin"),
                                      ("height_mm", "ancho_inicio", "ancho_fin")):
                amount = Decimal(str(p[field])) - Decimal(str(resolved.get(start, 0))) - Decimal(str(resolved.get(end, 0)))
                if amount <= 0:
                    raise ValueError(f"El tapacanto supera la medida terminada de {pid}")
                p[field] = float(amount)
            p["edge_banding"] = [f"{edge}: {value} mm" for edge, value in sorted(resolved.items())]
            p["edge_banding_confirmed"] = True
        else:
            unspecified.append(pid)
            # A role-based label such as 'front' does not specify which dimension
            # or thickness to deduct; do not make that choice implicitly.
            p["edge_banding"] = []
            p["edge_banding_confirmed"] = False
        if p["role"] in ("back", "drawer_bottom"):
            default_material = "mdf_3"
        else:
            default_material = spec.get("material", "melamine_16")
        materials.add(p.get("material", default_material))
        parts.append({"id": pid, "width": p["width_mm"], "height": p["height_mm"],
                      "thickness": p["thickness_mm"], **({"grain": p["grain"]} if p.get("grain") else {})})
    if len(materials) != 1:
        raise ValueError("Calcule cada material por separado; el paquete admite un solo material")
    if set(banding) - ids:
        raise ValueError("Tapacantos indicados para piezas que no existen")
    result = optimize_profile(parts, profile)
    if "error" in result:
        raise ValueError(result["error"])
    if any("grano relajado" in w.lower() for w in result["warnings"]):
        raise ValueError("La veta de una pieza no cabe en la placa sin rotación; revise el perfil")
    if unspecified:
        result["warnings"].append("Tapacantos sin definir para: " + ", ".join(unspecified) + "; no se descontó canto en esas piezas.")
    result["warnings"].append("Las dimensiones del despiece son de corte; confirmar tapacantos y espesores antes de fabricar.")
    result["finished_dimensions_mm"] = finished
    workbook = Path(destination)
    if workbook.suffix.lower() != ".xlsx":
        raise ValueError("El archivo de destino debe terminar en .xlsx")
    diagram = workbook.with_suffix(".svg")
    export_cutlist_xlsx(cut_spec, str(workbook), template=template, cut_data=result)
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
