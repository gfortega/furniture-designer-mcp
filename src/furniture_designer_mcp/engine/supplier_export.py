"""Spreadsheet-compatible provisional cut lists."""

from __future__ import annotations

import csv
from pathlib import Path

from .bom_generator import generate_bom

HEADERS = ["Estado", "Piezas", "Cantidad", "Largo mm", "Ancho mm", "Espesor mm", "Material", "Veta", "Tapacantos"]

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
            ", ".join(panel.get("edge_banding", [])) or "POR DEFINIR",
        )]


def export_cutlist_csv(spec: dict, destination: str) -> Path:
    """Write a provisional semicolon-delimited UTF-8 CSV, openable in Excel."""
    path = Path(destination)
    if path.suffix.lower() != ".csv":
        raise ValueError("destination must end in .csv")
    with path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.writer(output, delimiter=";")
        writer.writerow(HEADERS)
        writer.writerows(_rows(spec))
    return path


def export_cutlist_xlsx(spec: dict, destination: str) -> Path:
    """Write a provisional Excel workbook with the same fields as the CSV."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    path = Path(destination)
    if path.suffix.lower() != ".xlsx":
        raise ValueError("destination must end in .xlsx")
    book = Workbook()
    sheet = book.active
    sheet.title = "Despiece"
    sheet.append(HEADERS)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for row in _rows(spec):
        sheet.append(row)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    book.save(path)
    return path
