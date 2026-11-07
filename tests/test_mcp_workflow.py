"""Exercise the MCP protocol without depending on the process transport."""

import json
import tempfile
import unittest
from pathlib import Path

import anyio
from mcp import ClientSession
from openpyxl import load_workbook

from furniture_designer_mcp.server import mcp


class MCPWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_supplier_workflow(self):
        client_send, server_receive = anyio.create_memory_object_stream(0)
        server_send, client_receive = anyio.create_memory_object_stream(0)
        with tempfile.TemporaryDirectory() as directory:
            async with anyio.create_task_group() as group:
                group.start_soon(mcp._mcp_server.run, server_receive, server_send,
                                 mcp._mcp_server.create_initialization_options())
                async with ClientSession(client_receive, client_send) as session:
                    await session.initialize()
                    names = {tool.name for tool in (await session.list_tools()).tools}
                    self.assertTrue({"save_supplier_profile", "optimize_with_profile",
                                     "export_supplier_xlsx"}.issubset(names))
                    profile = {"name": "Prueba", "sheet_width_mm": 2800,
                               "sheet_height_mm": 2070, "thickness_mm": 18,
                               "blade_kerf_mm": 3, "grain_direction": "none"}
                    saved = await session.call_tool("save_supplier_profile", {
                        "profile_id": "ejemplo", "profile": profile, "directory": directory})
                    self.assertFalse(saved.isError)
                    self.assertTrue(Path(directory, "ejemplo.json").exists())
                    parts = [{"id": "tapa", "width": 1900, "height": 600},
                             {"id": "lateral", "width": 1400, "height": 600},
                             {"id": "extremo", "width": 732, "height": 600, "qty": 2},
                             {"id": "apoyo", "width": 732, "height": 500}]
                    result = await session.call_tool("optimize_with_profile", {
                        "parts": parts, "profile_id": "ejemplo", "directory": directory})
                    layout = json.loads(result.content[0].text)
                    self.assertEqual(layout["sheets_needed"], 1)
                    self.assertEqual(layout["total_pieces"], 5)
                    design = await session.call_tool("design_furniture", {
                        "furniture_type": "desk", "width": 120, "height": 75,
                        "depth": 60, "material": "melamine_18", "compact": False})
                    spec = json.loads(design.content[0].text)
                    target = str(Path(directory, "despiece.xlsx"))
                    exported = await session.call_tool("export_supplier_xlsx", {
                        "spec": spec, "destination": target})
                    self.assertFalse(exported.isError)
                    self.assertTrue(Path(target).exists())
                    self.assertGreater(load_workbook(target).active.max_row, 1)
                group.cancel_scope.cancel()
