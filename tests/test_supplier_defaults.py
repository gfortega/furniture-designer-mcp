import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

from furniture_designer_mcp.engine.designer import generate_l_desk_spec
from furniture_designer_mcp.engine.supplier_package import build_supplier_package
from furniture_designer_mcp.engine.supplier_profiles import list_profiles, load_profile, save_profile
from furniture_designer_mcp.engine.supplier_templates import list_templates, load_template, save_template


class DefaultSupplierTests(unittest.TestCase):
    def test_default_package_consistent_with_model(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = generate_l_desk_spec(190, 200, 75, 60)
            path = Path(directory, "pedido.xlsx")
            result = build_supplier_package(spec, str(path), profile_directory=directory,
                                            template_directory=directory)
            self.assertEqual(result["result"]["sheets_needed"], 1)
            self.assertTrue(any("provisional" in w for w in result["result"]["warnings"]))
            workbook = load_workbook(path)
            self.assertEqual(workbook.sheetnames, ["Despiece", "Placas y avisos", "Diseño y corte"])
            rows = list(workbook["Despiece"].values)
            self.assertEqual(sum(row[2] for row in rows[1:]), 5)
            self.assertEqual(next(row for row in rows[1:] if row[1] == "tapa_principal")[3], 1900)
            summary = dict(workbook["Placas y avisos"].values)
            self.assertEqual(summary["Placas"], 1)
            svg = Path(result["diagram"]).read_text(encoding="utf-8")
            self.assertIn("tapa_principal", svg)
            self.assertIn("BORRADOR", svg)

    def test_profiles_and_templates_are_selectable_without_modifying_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            default = load_profile(directory, "generico")
            save_profile(directory, "proveedor_a", {**default, "name": "Proveedor A", "sheet_width_mm": 2440})
            self.assertEqual(load_profile(directory, "proveedor_a")["sheet_width_mm"], 2440)
            self.assertEqual(load_profile(directory, "generico")["sheet_width_mm"], 2600)
            self.assertEqual({p["id"] for p in list_profiles(directory)}, {"generico", "proveedor_a"})
        with tempfile.TemporaryDirectory() as directory:
            save_template(directory, "proveedor_a", {"name": "Proveedor A", "columns": ["Piezas", "Cantidad"]})
            self.assertEqual(load_template(directory, "proveedor_a")["columns"], ["Piezas", "Cantidad"])
            self.assertEqual({p["id"] for p in list_templates(directory)}, {"generica", "proveedor_a"})
            with self.assertRaises(ValueError):
                save_template(directory, "generica", {"name": "x", "columns": ["Piezas"]})
            with self.assertRaises(ValueError):
                save_template(directory, "bad", {"name": "x", "columns": ["INVALIDA"]})

    def test_different_materials_are_not_placed_on_same_sheet(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = generate_l_desk_spec(190, 200, 75, 60)
            spec["parts"][1]["material"] = "otro"
            with self.assertRaisesRegex(ValueError, "material por separado"):
                build_supplier_package(spec, str(Path(directory, "bad.xlsx")))
            self.assertFalse(Path(directory, "bad.xlsx").exists())

    def test_selected_profile_and_column_template_drive_package(self):
        with tempfile.TemporaryDirectory() as directory:
            profiles = str(Path(directory, "perfiles"))
            templates = str(Path(directory, "plantillas"))
            save_profile(profiles, "a", {"name": "A", "sheet_width_mm": 2440,
                         "sheet_height_mm": 1220, "thickness_mm": 18,
                         "blade_kerf_mm": 3, "grain_direction": "none", "trim_margin_mm": 2})
            save_template(templates, "a", {"name": "A", "columns": ["Piezas", "Cantidad", "Largo mm"]})
            path = Path(directory, "a.xlsx")
            result = build_supplier_package(generate_l_desk_spec(190, 200, 75, 60), str(path),
                                            "a", "a", profiles, templates)
            self.assertEqual(result["result"]["sheets_needed"], 2)
            book = load_workbook(path)
            self.assertEqual(list(book["Despiece"].values)[0], ("Piezas", "Cantidad", "Largo mm"))
            self.assertEqual(dict(book["Placas y avisos"].values)["Margen por borde mm"], 2)

    def test_finished_sizes_are_adjusted_only_for_explicit_edges(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = generate_l_desk_spec(190, 200, 75, 60)
            path = Path(directory, "pedido.xlsx")
            result = build_supplier_package(spec, str(path), banding_by_part={
                "tapa_principal": {"largo_inicio": 1, "largo_fin": 1, "ancho_fin": 0.8},
                "apoyo_extremo_principal": {},
            })
            self.assertEqual(spec["parts"][0]["width_mm"], 1900)
            workbook = load_workbook(path)
            rows = list(workbook["Diseño y corte"].values)
            top = next(row for row in rows if row[0] == "tapa_principal")
            self.assertEqual(top[1:5], (1900, 600, 1898, 599.2))
            end = next(row for row in rows if row[0] == "apoyo_extremo_principal")
            self.assertEqual(end[5], "SIN CANTEAR")
            unknown = next(row for row in rows if row[0] == "tapa_lateral")
            self.assertEqual(unknown[5], "POR DEFINIR")
            placement = next(p for s in result["result"]["sheets"] for p in s["pieces"] if p["id"] == "tapa_principal")
            self.assertEqual(sorted((placement["width"], placement["height"])), [599.2, 1898])
            self.assertTrue(any("sin definir" in w for w in result["result"]["warnings"]))

    def test_rejects_unknown_piece_and_invalid_edges(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = generate_l_desk_spec(190, 200, 75, 60)
            path = str(Path(directory, "pedido.xlsx"))
            for data in ({"no_existe": {}}, {"tapa_principal": {"frente": 1}},
                         {"tapa_principal": {"ancho_fin": -1}},
                         {"tapa_principal": {"ancho_fin": 1000}}):
                with self.assertRaises(ValueError):
                    build_supplier_package(spec, path, banding_by_part=data)
                self.assertFalse(Path(path).exists())
