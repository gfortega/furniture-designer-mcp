"""Spreadsheet-compatible provisional cut lists."""

from __future__ import annotations

import csv
from pathlib import Path

from .bom_generator import generate_bom
from .supplier_templates import DEFAULT_COLUMNS, validate_template

HEADERS = DEFAULT_COLUMNS

def _cell(value):
    """Prevent spreadsheet applications from interpreting text as formulas."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def _rows(spec: dict):
    bom = generate_bom(spec)
    for panel in bom["panels"] + bom["back_panels"]:
        yield [_cell(value) for value in (
            "BORRADOR - REVISAR", ", ".join(panel["ids"]), panel["qty"],
            panel["width_mm"], panel["height_mm"], panel["thickness_mm"],
            panel["material"], panel.get("grain") or "POR DEFINIR",
            ", ".join(panel.get("edge_banding", [])) or
            ("SIN CANTEAR" if panel.get("edge_banding_confirmed") else "POR DEFINIR"),
        )]


def _selected_rows(spec: dict, template: dict | None):
    columns = HEADERS if template is None else validate_template(template)["columns"]
    indices = [HEADERS.index(column) for column in columns]
    return columns, ([row[i] for i in indices] for row in _rows(spec))


def export_cutlist_csv(spec: dict, destination: str, template: dict | None = None) -> Path:
    """Write a provisional semicolon-delimited UTF-8 CSV, openable in Excel."""
    path = Path(destination)
    if path.suffix.lower() != ".csv":
        raise ValueError("destination must end in .csv")
    with path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.writer(output, delimiter=";")
        columns, rows = _selected_rows(spec, template)
        writer.writerow(columns)
        writer.writerows(rows)
    return path


def export_cutlist_xlsx(spec: dict, destination: str, template: dict | None = None,
                        cut_data: dict | None = None) -> Path:
    """Write a provisional Excel workbook with the same fields as the CSV."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    path = Path(destination)
    if path.suffix.lower() != ".xlsx":
        raise ValueError("destination must end in .xlsx")
    book = Workbook()
    sheet = book.active
    sheet.title = "Despiece"
    columns, rows = _selected_rows(spec, template)
    sheet.append(columns)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in rows:
        sheet.append(row)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    if cut_data is not None:
        summary = book.create_sheet("Placas y avisos")
        profile = cut_data["profile"]
        for label, value in [
            ("Estado", "BORRADOR - CONFIRMAR CON PROVEEDOR"),
            ("Perfil", profile["name"]),
            ("Placas", cut_data["sheets_needed"]),
            ("Largo placa mm", profile["sheet_width_mm"]),
            ("Ancho placa mm", profile["sheet_height_mm"]),
            ("Espesor mm", profile["thickness_mm"]),
            ("Sierra mm", profile["blade_kerf_mm"]),
            ("Margen por borde mm", profile.get("trim_margin_mm", "NO DEFINIDO")),
            ("Veta", profile["grain_direction"]),
            ("Superficie no ocupada %", cut_data["waste_percentage"]),
            ("Tapacanto", "Confirmar criterio de medidas con proveedor"),
        ]:
            summary.append([_cell(label), _cell(value)])
        for warning in cut_data.get("warnings", []):
            summary.append(["Aviso", _cell(warning)])
        if "finished_dimensions_mm" in cut_data:
            dimensions = book.create_sheet("Diseño y corte")
            dimensions.append(["Pieza", "Largo terminado mm", "Ancho terminado mm",
                               "Largo de corte mm", "Ancho de corte mm", "Cantos"])
            for p in spec["parts"]:
                finished = cut_data["finished_dimensions_mm"][p["id"]]
                edges = ", ".join(p.get("edge_banding", [])) or (
                    "SIN CANTEAR" if p.get("edge_banding_confirmed") else "POR DEFINIR")
                dimensions.append([_cell(v) for v in (p["id"], finished["largo_mm"],
                                   finished["ancho_mm"], p["width_mm"], p["height_mm"], edges)])
    book.save(path)
    return path
