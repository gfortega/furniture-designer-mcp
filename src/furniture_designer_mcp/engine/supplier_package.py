"""Generate a draft supplier workbook and a matching cutting diagram."""

import html
import math
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

from .supplier_export import export_cutlist_xlsx
from .supplier_profiles import load_profile, optimize_profile
from .supplier_templates import load_template
from .cut_sequence import build_cut_sequence


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
    result["warnings"].append("Secuencia geométrica de prueba; verificar con la máquina y el proveedor antes de cortar.")
    result["finished_dimensions_mm"] = finished
    result["cut_sequence"] = build_cut_sequence(result)
    workbook = Path(destination)
    if workbook.suffix.lower() != ".xlsx":
        raise ValueError("El archivo de destino debe terminar en .xlsx")
    diagram = workbook.with_suffix(".svg")
    export_cutlist_xlsx(cut_spec, str(workbook), template=template, cut_data=result)
    diagram.write_text(_svg(result), encoding="utf-8")
    return {"workbook": str(workbook), "diagram": str(diagram), "result": result,
            "template": template, "status": "BORRADOR - REVISAR"}


def _cut_label_positions(sheet: dict, cuts: list[dict], width: float, height: float, font: float):
    """Place numbered chips on cut lines, avoiding other chips and piece labels.

    If a congested region cannot fit a chip, move it to a separate legend.
    Coordinates are relative to the sheet, not to the entire SVG.
    """
    chip_h = font * 1.3
    occupied = []
    for part in sheet["pieces"]:
        text_width = min(width, max(font, len(str(part["id"])) * font * 0.64))
        cx = part["x"] + part["width"] / 2
        cy = part["y"] + part["height"] / 2
        occupied.append((cx-text_width/2, cy-font, cx+text_width/2, cy+font*0.35))

    placed, overflow = {}, []
    ordered = sorted(cuts, key=lambda cut: cut["region_antes_mm"][3 if cut["eje"] == "x" else 2])
    fractions = [0.5, 0.25, 0.75, 0.125, 0.875, 0.375, 0.625,
                 0.0625, 0.9375, 0.1875, 0.3125, 0.4375, 0.5625, 0.6875, 0.8125]
    for cut in ordered:
        x, y, w, h = cut["region_antes_mm"]
        center = cut["trayecto_centro_mm"]
        chip_w = max(font * 1.25, font * (0.72 * len(str(cut["numero"])) + 0.5))
        chosen = None
        for fraction in fractions:
            cx = center if cut["eje"] == "x" else x + w * fraction
            cy = y + h * fraction if cut["eje"] == "x" else center
            cx = max(chip_w/2, min(width-chip_w/2, cx))
            cy = max(chip_h/2, min(height-chip_h/2, cy))
            box = (cx-chip_w/2, cy-chip_h/2, cx+chip_w/2, cy+chip_h/2)
            if all(box[2] + font*0.12 <= b[0] or b[2] + font*0.12 <= box[0] or
                   box[3] + font*0.12 <= b[1] or b[3] + font*0.12 <= box[1]
                   for b in occupied):
                chosen = box
                break
        if chosen is None:
            overflow.append((cut, chip_w))
        else:
            placed[cut["numero"]] = chosen
            occupied.append(chosen)
    return placed, overflow


def _svg(result: dict) -> str:
    width = result["sheet_size_mm"]["width"]
    height = result["sheet_size_mm"]["height"]
    sheets = result["sheets"]
    gap = 180
    size = max(width, height)
    font = max(20, min(55, size / 55))
    placements = []
    for sheet in sheets:
        sequence = next(plan for plan in result["cut_sequence"] if plan["sheet_number"] == sheet["sheet_number"])
        labels, overflow = _cut_label_positions(sheet, sequence["cuts"], width, height, font)
        placements.append((sequence, labels, overflow))
    overflow_widths = [chip_w for _, _, overflow in placements for _, chip_w in overflow]
    side_width = max(7 * font, max(overflow_widths, default=0) + 2 * font) if overflow_widths else 0
    block_heights = [max(height, len(item[2]) * font * 1.8) for item in placements]
    svg_height = sum(block + gap for block in block_heights)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width + side_width} {svg_height}">']
    svg.append('<style>text{font-family:sans-serif;fill:#202020}</style>')
    y_offset = gap
    for index, sheet in enumerate(sheets):
        svg.append(f'<text x="10" y="{y_offset - 35}" font-size="{font}">BORRADOR — Placa {sheet["sheet_number"]} ({width} × {height} mm)</text>')
        svg.append(f'<rect x="0" y="{y_offset}" width="{width}" height="{height}" fill="#eee" stroke="#222" stroke-width="5"/>')
        for p in sheet["pieces"]:
            x, y, w, h = p["x"], p["y"] + y_offset, p["width"], p["height"]
            label = html.escape(str(p["id"]))
            svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#b8d8e5" stroke="#333" stroke-width="3"/>')
            svg.append(f'<text x="{x + w/2}" y="{y + h/2}" text-anchor="middle" font-size="{font}">{label}</text>')
        sequence, labels, overflow = placements[index]
        for cut in sequence["cuts"]:
            x, y, w, h = cut["region_antes_mm"]
            center = cut["trayecto_centro_mm"]
            if cut["eje"] == "x":
                x1, y1, x2, y2 = center, y+y_offset, center, y+h+y_offset
            else:
                x1, y1, x2, y2 = x, center+y_offset, x+w, center+y_offset
            svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#c62828" stroke-width="5"/>')
        # Draw legend connectors before all chips, so they cannot obscure numbers.
        for i, (cut, chip_w) in enumerate(overflow):
            cy = y_offset + font*(0.8 + i*1.8)
            x, y, w, h = cut["region_antes_mm"]
            center = cut["trayecto_centro_mm"]
            anchor_x = center if cut["eje"] == "x" else x+w/2
            anchor_y = y+h/2 if cut["eje"] == "x" else center
            svg.append(f'<line x1="{anchor_x}" y1="{anchor_y+y_offset}" x2="{width+font}" y2="{cy}" stroke="#b42318" stroke-width="2" stroke-dasharray="12 8"/>')
        # Draw labels after all cut lines so the white chips remain legible.
        for cut in sequence["cuts"]:
            number = cut["numero"]
            if number not in labels:
                continue
            left, top, right, bottom = labels[number]
            svg.append(f'<g class="cut-label" data-cut="{number}"><rect x="{left}" y="{top+y_offset}" width="{right-left}" height="{bottom-top}" rx="{font*0.18}" fill="white" stroke="#b42318" stroke-width="2"/><text x="{(left+right)/2}" y="{(top+bottom)/2+y_offset}" dominant-baseline="central" text-anchor="middle" font-size="{font}">{number}</text></g>')
        for i, (cut, chip_w) in enumerate(overflow):
            cy = y_offset + font*(0.8 + i*1.8)
            cx = width + font + chip_w/2
            svg.append(f'<g class="cut-label" data-cut="{cut["numero"]}"><rect x="{cx-chip_w/2}" y="{cy-font*0.65}" width="{chip_w}" height="{font*1.3}" rx="{font*0.18}" fill="white" stroke="#b42318" stroke-width="2"/><text x="{cx}" y="{cy}" dominant-baseline="central" text-anchor="middle" font-size="{font}">{cut["numero"]}</text></g>')
        y_offset += block_heights[index] + gap
    svg.append('</svg>')
    return "".join(svg)
