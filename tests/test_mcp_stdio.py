"""Opt-in end-to-end test: a separate MCP process using stdin/stdout."""

import json
import os
import tempfile
import unittest
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openpyxl import load_workbook


@unittest.skipUnless(os.environ.get("FURNITURE_TEST_STDIO") == "1", "requires subprocess MCP transport")
class MCPStdioTests(unittest.IsolatedAsyncioTestCase):
    async def test_l_desk_change_and_export(self):
        command = os.environ["FURNITURE_MCP_COMMAND"]
        profile = {"name": "Prueba provisional", "sheet_width_mm": 2800,
                   "sheet_height_mm": 2070, "thickness_mm": 18,
                   "blade_kerf_mm": 3, "grain_direction": "none"}
        sizes = [("Tapa principal", 2000, 600, "top_panel"),
                 ("Tapa lateral", 1400, 600, "top_panel"),
                 ("Apoyo 1", 732, 600, "side"), ("Apoyo 2", 732, 600, "side"),
                 ("Apoyo interior", 732, 500, "side")]
        spec = {"material": "melamine_18", "material_thickness_mm": 18,
                "parts": [{"id": name, "width_mm": w, "height_mm": h,
                           "thickness_mm": 18, "role": role} for name, w, h, role in sizes]}
        with tempfile.TemporaryDirectory() as directory, anyio.fail_after(20):
            async with stdio_client(StdioServerParameters(command=command, args=[])) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    response = await session.call_tool("save_supplier_profile", {
                        "profile_id": "prueba", "profile": profile, "directory": directory})
                    self.assertIn("Perfil guardado", response.content[0].text)

                    async def layout():
                        parts = [{"id": p["id"], "width": p["width_mm"],
                                  "height": p["height_mm"], "thickness": p["thickness_mm"]}
                                 for p in spec["parts"]]
                        response = await session.call_tool("optimize_with_profile", {
                            "parts": parts, "profile_id": "prueba", "directory": directory})
                        return json.loads(response.content[0].text)

                    original = await layout()
                    self.assertEqual(original["sheets_needed"], 1)
                    spec["parts"][0]["width_mm"] = 1900
                    modified = await layout()
                    self.assertEqual(modified["sheets_needed"], 1)
                    self.assertEqual(modified["total_pieces"], 5)
                    placed = modified["sheets"][0]["pieces"]
                    self.assertEqual(next(p for p in placed if p["id"] == "Tapa principal")["width"], 1900)
                    for a in placed:
                        self.assertLessEqual(a["x"] + a["width"], 2800)
                        self.assertLessEqual(a["y"] + a["height"], 2070)
                    for i, a in enumerate(placed):
                        for b in placed[i + 1:]:
                            self.assertTrue(a["x"] + a["width"] + 3 <= b["x"] or
                                            b["x"] + b["width"] + 3 <= a["x"] or
                                            a["y"] + a["height"] + 3 <= b["y"] or
                                            b["y"] + b["height"] + 3 <= a["y"])
                    output = str(Path(directory, "despiece.xlsx"))
                    response = await session.call_tool("export_supplier_xlsx", {"spec": spec, "destination": output})
                    self.assertIn("guardado", response.content[0].text)
                    rows = list(load_workbook(output).active.values)
                    self.assertEqual(next(row for row in rows[1:] if row[1] == "Tapa principal")[3], 1900)
                    self.assertEqual(sum(row[2] for row in rows[1:]), 5)
