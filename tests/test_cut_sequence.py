import unittest
import xml.etree.ElementTree as ET

from furniture_designer_mcp.engine.cut_sequence import SequenceUnavailable, build_cut_sequence
from furniture_designer_mcp.engine.designer import generate_l_desk_spec
from furniture_designer_mcp.engine.supplier_profiles import load_profile, optimize_profile
from furniture_designer_mcp.engine.supplier_package import _svg


class CutSequenceTests(unittest.TestCase):
    def test_each_numbered_cut_uses_existing_region_and_avoids_every_piece(self):
        spec = generate_l_desk_spec(190, 200, 75, 60)
        pieces = [{"id": p["id"], "width": p["width_mm"], "height": p["height_mm"]}
                  for p in spec["parts"]]
        layout = optimize_profile(pieces, load_profile("/tmp", "generico"))
        plan = build_cut_sequence(layout)[0]
        self.assertTrue(plan["cuts"])
        self.assertEqual([cut["numero"] for cut in plan["cuts"]], list(range(1, len(plan["cuts"])+1)))
        # Independently check that no saw slot intersects any requested part.
        for cut in plan["cuts"]:
            x, y, w, h = cut["region_antes_mm"]
            start, kerf = cut["inicio_sierra_mm"], cut["ancho_sierra_mm"]
            slot = (start, y, start+kerf, y+h) if cut["eje"] == "x" else (x, start, x+w, start+kerf)
            for part in layout["sheets"][0]["pieces"]:
                px, py, pw, ph = (part[k] for k in ("x", "y", "width", "height"))
                intersects = (slot[0] < px+pw-1e-6 and slot[2] > px+1e-6 and
                              slot[1] < py+ph-1e-6 and slot[3] > py+1e-6)
                self.assertFalse(intersects, (cut, part))

    def test_overlapping_parts_are_rejected(self):
        result = {"sheet_size_mm": {"width": 100, "height": 100}, "blade_kerf_mm": 3,
                  "sheets": [{"sheet_number": 1, "pieces": [
                      {"id": "a", "x": 0, "y": 0, "width": 60, "height": 60},
                      {"id": "b", "x": 40, "y": 40, "width": 60, "height": 60}]}]}
        with self.assertRaises(SequenceUnavailable):
            build_cut_sequence(result)

    def test_numbered_labels_do_not_overlap_on_desk_diagram(self):
        spec = generate_l_desk_spec(190, 200, 75, 60)
        parts = [{"id": p["id"], "width": p["width_mm"], "height": p["height_mm"]}
                 for p in spec["parts"]]
        layout = optimize_profile(parts, load_profile("/tmp", "generico"))
        layout["cut_sequence"] = build_cut_sequence(layout)
        document = ET.fromstring(_svg(layout))
        ns = {"s": "http://www.w3.org/2000/svg"}
        groups = document.findall('.//s:g[@class="cut-label"]', ns)
        self.assertEqual(len(groups), len(layout["cut_sequence"][0]["cuts"]))
        boxes = []
        for group in groups:
            rect = group.find("s:rect", ns)
            x, y, w, h = (float(rect.attrib[k]) for k in ("x", "y", "width", "height"))
            boxes.append((x, y, x+w, y+h))
        for i, a in enumerate(boxes):
            for b in boxes[i+1:]:
                self.assertTrue(a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])

    def test_dense_labels_use_separate_legend_without_collisions(self):
        cuts = [{"numero": i, "eje": "x", "trayecto_centro_mm": 50,
                 "region_antes_mm": [0, 0, 100, 100]} for i in range(1, 41)]
        layout = {"sheet_size_mm": {"width": 100, "height": 100},
                  "sheets": [{"sheet_number": 1, "pieces": []}],
                  "cut_sequence": [{"sheet_number": 1, "cuts": cuts}]}
        root = ET.fromstring(_svg(layout))
        ns = {"s": "http://www.w3.org/2000/svg"}
        labels = root.findall('.//s:g[@class="cut-label"]', ns)
        self.assertEqual(len(labels), 40)
        rects = []
        for label in labels:
            rect = label.find("s:rect", ns)
            x, y, w, h = (float(rect.attrib[k]) for k in ("x", "y", "width", "height"))
            rects.append((x, y, x+w, y+h))
        self.assertTrue(any(rect[0] >= 100 for rect in rects))
        for i, a in enumerate(rects):
            for b in rects[i+1:]:
                self.assertTrue(a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])
