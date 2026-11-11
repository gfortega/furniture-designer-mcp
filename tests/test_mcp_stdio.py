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
        with tempfile.TemporaryDirectory() as directory, anyio.fail_after(20):
            async with stdio_client(StdioServerParameters(command=command, args=[])) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    response = await session.call_tool("save_supplier_profile", {
                        "profile_id": "prueba", "profile": profile, "directory": directory})
                    self.assertIn("Perfil guardado", response.content[0].text)

                    async def design(width):
                        response = await session.call_tool("design_l_desk", {
                            "width": width, "depth": 200, "height": 75,
                            "worktop_depth": 60, "material": "melamine_18"})
                        return json.loads(response.content[0].text)

                    spec = await design(200)
                    report = str(Path(directory, "escritorio.html"))
                    response = await session.call_tool("update_design_report", {
                        "spec": spec, "iteration_name": "200 cm", "output_path": report})
                    self.assertIn("actualizado", response.content[0].text)

                    async def layout():
                        parts = [{"id": p["id"], "width": p["width_mm"],
                                  "height": p["height_mm"], "thickness": p["thickness_mm"]}
                                 for p in spec["parts"]]
                        response = await session.call_tool("optimize_with_profile", {
                            "parts": parts, "profile_id": "prueba", "directory": directory})
                        return json.loads(response.content[0].text)

                    original = await layout()
                    self.assertEqual(original["sheets_needed"], 1)
                    spec = await design(190)
                    modified = await layout()
                    self.assertEqual(modified["sheets_needed"], 1)
                    self.assertEqual(modified["total_pieces"], 5)
                    placed = modified["sheets"][0]["pieces"]
                    self.assertEqual(next(p for p in placed if p["id"] == "tapa_principal")["width"], 1900)
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
                    self.assertEqual(next(row for row in rows[1:] if row[1] == "tapa_principal")[3], 1900)
                    self.assertEqual(sum(row[2] for row in rows[1:]), 5)
                    response = await session.call_tool("update_design_report", {
                        "spec": spec, "iteration_name": "190 cm", "output_path": report,
                        "cut_data": modified})
                    self.assertIn("actualizado", response.content[0].text)
                    self.assertIn('"name": "190 cm"', Path(report).read_text(encoding="utf-8"))
                    package = str(Path(directory, "paquete.xlsx"))
                    response = await session.call_tool("export_supplier_package", {
                        "spec": spec, "destination": package,
                        "banding_by_part": {"tapa_principal": {"largo_inicio": 1, "largo_fin": 1}}})
                    result = json.loads(response.content[0].text)
                    self.assertEqual(result["result"]["sheets_needed"], 1)
                    self.assertTrue(Path(result["diagram"]).exists())
                    self.assertEqual(load_workbook(package).sheetnames, ["Despiece", "Placas y avisos", "Diseño y corte", "Secuencia cortes"])
                    rows = list(load_workbook(package)["Diseño y corte"].values)
                    top = next(row for row in rows if row[0] == "tapa_principal")
                    self.assertEqual(top[1:5], (1900, 600, 1898, 600))
                    templates = str(Path(directory, "templates"))
                    saved = await session.call_tool("save_supplier_template", {
                        "template_id": "test", "directory": templates,
                        "template": {"name": "Test", "columns": ["Piezas", "Cantidad"]}})
                    self.assertIn("guardada", saved.content[0].text)
                    listed = await session.call_tool("list_supplier_templates", {"directory": templates})
                    self.assertEqual({item["id"] for item in json.loads(listed.content[0].text)},
                                     {"generica", "test"})
                    custom = str(Path(directory, "personalizado.xlsx"))
                    response = await session.call_tool("export_supplier_package", {
                        "spec": spec, "destination": custom, "template_id": "test",
                        "template_directory": templates})
                    self.assertFalse(response.isError)
                    self.assertEqual(list(load_workbook(custom)["Despiece"].values)[0],
                                     ("Piezas", "Cantidad"))
