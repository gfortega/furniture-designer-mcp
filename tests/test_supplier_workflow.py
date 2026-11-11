import csv
import tempfile
import unittest
from pathlib import Path

from furniture_designer_mcp.engine.bom_generator import generate_bom
from furniture_designer_mcp.engine.cut_optimizer import optimize_cuts, optimize_cuts_best
from furniture_designer_mcp.engine.supplier_profiles import load_profile, save_profile, optimize_profile
from furniture_designer_mcp.engine.supplier_export import export_cutlist_csv, export_cutlist_xlsx


class SupplierWorkflowTests(unittest.TestCase):
    def test_grouping_preserves_material_grain_and_edge_banding(self):
        def panel(id, **changes):
            return {"id": id, "role": "side", "width_mm": 600, "height_mm": 732,
                    "thickness_mm": 18, "material": "white", "grain": "length",
                    "edge_banding": ["front"], **changes}
        parts = [panel("a"), panel("b"), panel("c", edge_banding=["back_edge"]),
                 panel("d", material="oak"), panel("e", grain="none")]
        bom = generate_bom({"parts": parts})
        self.assertEqual(sorted(p["qty"] for p in bom["panels"]), [1, 1, 1, 2])
        self.assertEqual(bom["summary"]["total_pieces"], 5)

    def test_profile_round_trip_and_desk_layout(self):
        profile = {"name": "Example", "sheet_width_mm": 2800, "sheet_height_mm": 2070,
                   "thickness_mm": 18, "blade_kerf_mm": 3, "grain_direction": "none"}
        parts = [{"id": "top", "width": 1900, "height": 600},
                 {"id": "return", "width": 1400, "height": 600},
                 {"id": "end", "width": 732, "height": 600, "qty": 2},
                 {"id": "corner", "width": 732, "height": 500}]
        with tempfile.TemporaryDirectory() as directory:
            save_profile(directory, "provider", profile)
            loaded = load_profile(directory, "provider")
            self.assertEqual(loaded, profile)
            with self.assertRaises(ValueError):
                save_profile(directory, "../outside", profile)
            result = optimize_cuts(parts, sheet_width=loaded["sheet_width_mm"],
                                   sheet_height=loaded["sheet_height_mm"],
                                   blade_kerf=loaded["blade_kerf_mm"],
                                   grain_direction=loaded["grain_direction"])
        self.assertEqual(result["sheets_needed"], 1)
        self.assertEqual(result["total_pieces"], 5)
        placed = result["sheets"][0]["pieces"]
        for a in placed:
            self.assertLessEqual(a["x"] + a["width"], 2800)
            self.assertLessEqual(a["y"] + a["height"], 2070)
        for i, a in enumerate(placed):
            for b in placed[i + 1:]:
                self.assertTrue(a["x"] + a["width"] + 3 <= b["x"] or
                                b["x"] + b["width"] + 3 <= a["x"] or
                                a["y"] + a["height"] + 3 <= b["y"] or
                                b["y"] + b["height"] + 3 <= a["y"])

    def test_profile_rejects_invalid_dimensions(self):
        profile = {"name": "bad", "sheet_width_mm": -1, "sheet_height_mm": 2070,
                   "thickness_mm": 18, "blade_kerf_mm": 3, "grain_direction": "none"}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                save_profile(directory, "bad", profile)
            self.assertFalse(Path(directory, "bad.json").exists())

    def test_trim_margin_is_reserved_on_all_edges(self):
        profile = {"name": "Test", "sheet_width_mm": 1000, "sheet_height_mm": 600,
                   "thickness_mm": 18, "blade_kerf_mm": 3, "grain_direction": "none",
                   "trim_margin_mm": 10}
        result = optimize_profile([{"id": "a", "width": 980, "height": 580}], profile)
        self.assertEqual(result["sheets_needed"], 1)
        self.assertEqual(result["usable_sheet_size_mm"], {"width": 980, "height": 580})
        self.assertEqual(result["sheet_size_mm"], {"width": 1000, "height": 600})
        piece = result["sheets"][0]["pieces"][0]
        self.assertEqual((piece["x"], piece["y"]), (10, 10))
        self.assertEqual(result["waste_percentage"], 5.3)
        self.assertIn("error", optimize_profile([{"id": "b", "width": 990, "height": 590}], profile))
        with self.assertRaises(ValueError):
            optimize_profile([], {**profile, "trim_margin_mm": 300})

    def test_missing_margin_is_explicitly_reported(self):
        profile = {"name": "Test", "sheet_width_mm": 1000, "sheet_height_mm": 600,
                   "thickness_mm": 18, "blade_kerf_mm": 3, "grain_direction": "none"}
        result = optimize_profile([{"id": "a", "width": 100, "height": 100}], profile)
        self.assertTrue(any("no definido" in warning for warning in result["warnings"]))

    def test_invalid_pieces_and_incompatible_thickness_are_rejected(self):
        profile = {"name": "15 mm", "sheet_width_mm": 2600, "sheet_height_mm": 1830,
                   "thickness_mm": 15, "blade_kerf_mm": 3.2, "grain_direction": "none"}
        for piece in ({"id": "bad", "width": -1, "height": 100},
                      {"id": "bad", "width": 100, "height": 100, "qty": 0},
                      {"id": "bad", "width": 100, "height": 100, "thickness": 18},
                      {"id": "bad", "width": 100, "height": 100, "grain": "unknown"}):
            with self.assertRaises(ValueError):
                optimize_profile([piece], profile)
        self.assertIn("error", optimize_profile([{"id": "large", "width": 3000, "height": 2000}], profile))

    def test_grain_restriction_is_not_silently_relaxed(self):
        profile = {"name": "Veta", "sheet_width_mm": 1000, "sheet_height_mm": 500,
                   "thickness_mm": 18, "blade_kerf_mm": 3, "grain_direction": "length"}
        # Rotation would fit, but would turn a fixed lengthwise grain.
        result = optimize_profile([{"id": "veta", "width": 400, "height": 800}], profile)
        self.assertIn("error", result)
        self.assertIn("veta", result["error"])

    def test_export_keeps_distinct_edges_and_prevents_formulas(self):
        parts = [{"id": "=HYPERLINK()", "role": "side", "width_mm": 600,
                  "height_mm": 732, "thickness_mm": 18, "edge_banding": ["front"]},
                 {"id": "side2", "role": "side", "width_mm": 600,
                  "height_mm": 732, "thickness_mm": 18, "edge_banding": ["left"]}]
        with tempfile.TemporaryDirectory() as directory:
            path = export_cutlist_csv({"parts": parts}, str(Path(directory) / "parts.csv"))
            with path.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f, delimiter=";"))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Piezas"], "'=HYPERLINK()")
        self.assertEqual({row["Tapacantos"] for row in rows}, {"front", "left"})

    def test_excel_round_trip_preserves_values(self):
        from openpyxl import load_workbook
        spec = {"parts": [{"id": "Panel", "role": "side", "width_mm": 1900,
                           "height_mm": 600, "thickness_mm": 18,
                           "edge_banding": ["front"], "grain": "length"}]}
        with tempfile.TemporaryDirectory() as directory:
            path = export_cutlist_xlsx(spec, str(Path(directory) / "parts.xlsx"))
            sheet = load_workbook(path).active
            rows = list(sheet.values)
        self.assertEqual(rows[1][1:6], ("Panel", 1, 1900, 600, 18))
        self.assertEqual(rows[1][7:], ("length", "front"))

    def test_alternative_order_can_save_a_sheet(self):
        sizes = [(2, 6), (3, 8), (6, 3), (2, 8), (7, 7), (2, 4)]
        parts = [{"id": str(i), "width": w, "height": h} for i, (w, h) in enumerate(sizes)]
        settings = {"sheet_width": 12, "sheet_height": 12, "blade_kerf": 0, "grain_direction": "none"}
        self.assertEqual(optimize_cuts(parts, **settings)["sheets_needed"], 2)
        improved = optimize_cuts_best(parts, **settings)
        self.assertEqual(improved["sheets_needed"], 1)
        self.assertFalse(improved["optimization"]["guarantees_global_optimum"])


if __name__ == "__main__":
    unittest.main()
