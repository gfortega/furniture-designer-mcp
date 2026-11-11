import json
import tempfile
import unittest
from pathlib import Path

from furniture_designer_mcp.engine.bom_generator import generate_bom
from furniture_designer_mcp.engine.designer import generate_l_desk_spec
from furniture_designer_mcp.engine.freecad_scripts import _box_dims
from furniture_designer_mcp.engine.report_generator import generate_design_report
from furniture_designer_mcp.engine.spec_validator import validate_spec


class LDeskTests(unittest.TestCase):
    def test_geometry_and_resize_update_cut_list_and_report(self):
        original = generate_l_desk_spec(200, 200, 75, 60)
        modified = generate_l_desk_spec(190, 200, 75, 60)
        self.assertEqual(validate_spec(modified), [])
        self.assertEqual(len(modified["parts"]), 5)
        by_id = {part["id"]: part for part in modified["parts"]}
        self.assertEqual(by_id["tapa_principal"]["width_mm"], 1900)
        self.assertEqual(by_id["apoyo_extremo_principal"]["position_mm"]["x"], 1882)
        self.assertEqual(_box_dims(by_id["tapa_lateral"]), (600, 1400, 18))
        self.assertEqual(_box_dims(by_id["apoyo_extremo_lateral"]), (600, 18, 732))
        self.assertEqual(generate_bom(modified)["summary"]["total_pieces"], 5)

        # The five boxes touch, but must not occupy each other's volume.
        boxes = []
        for part in modified["parts"]:
            pos = part["position_mm"]
            xyz = (pos["x"], pos["y"], pos["z"])
            dims = _box_dims(part)
            boxes.append((xyz, tuple(p + d for p, d in zip(xyz, dims))))
        for i, (a0, a1) in enumerate(boxes):
            for b0, b1 in boxes[i + 1:]:
                self.assertTrue(any(a1[axis] <= b0[axis] or b1[axis] <= a0[axis]
                                    for axis in range(3)))
        self.assertEqual(tuple(max(b[1][axis] for b in boxes) for axis in range(3)),
                         (1900, 2000, 750))

        with tempfile.TemporaryDirectory() as directory:
            target = str(Path(directory) / "report.html")
            generate_design_report(original, iteration_name="200 cm", output_path=target)
            generate_design_report(modified, iteration_name="190 cm", output_path=target)
            report = Path(target).read_text(encoding="utf-8")
            self.assertIn('"name": "200 cm"', report)
            self.assertIn('"name": "190 cm"', report)
            self.assertIn('"width_mm": 1900', report)

    def test_invalid_sizes_and_material_are_rejected(self):
        for args in [(0, 200, 75, 60), (60, 200, 75, 60), (200, 60, 75, 60),
                     (200, 200, float("nan"), 60)]:
            with self.assertRaises(ValueError):
                generate_l_desk_spec(*args)
        with self.assertRaises(ValueError):
            generate_l_desk_spec(200, 200, 75, 60, "solid_pine_20")
